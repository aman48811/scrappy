"""
GMAT Club -- PS x Source: OG  Full Scraper  (with Login)
=========================================================
Scrapes ALL questions tagged with any "Source: OG *" tag
inside the Problem Solving (PS) category.

Login Strategy
--------------
1. Browser opens to GMAT Club login page
2. YOU log in manually (handles Cloudflare + 2FA naturally)
3. Script detects when login is complete and starts scraping automatically
4. Session is saved to disk -- next run skips login entirely

What it does
------------
1. Reads gmatclub_tags.xlsx (built in Step 1) to get the 14 PS Source:OG tag IDs
2. For each tag ID, paginates through ALL search result pages (start=0,50,100...)
3. From every question card captures:
      Title, Link, Category, Tags (labels), Tag IDs
4. Deduplicates globally -- a question under multiple OG tags is saved only once
5. Saves a master Excel:
      - Sheet "All Questions"  -- full deduplicated list
      - Sheet per OG tag label -- e.g. "OG 2025-2026", "OG 2022" ...
      - Sheet "Summary"        -- count per tag + grand total

Output
------
  PS_OG_questions.xlsx

Usage
-----
  python scrape_ps_og.py                              # normal run (login if needed)
  python scrape_ps_og.py --fresh-login                # force re-login even if session exists
  python scrape_ps_og.py --test-html Search-by-tags.html  # offline test
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode

try:
    from bs4 import BeautifulSoup
    import pandas as pd
    from openpyxl.styles import Font, PatternFill, Alignment
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit(
        "Missing dependencies. Run:\n"
        "  pip install beautifulsoup4 pandas openpyxl playwright\n"
        "  playwright install chromium"
    )

# ── Config ────────────────────────────────────────────────────────────────────

TAGS_EXCEL = "gmatclub_tags.xlsx"
OUTPUT_EXCEL = "DS_OG_questions.xlsx"
SESSION_FILE = "gmatclub_session.json"  # saved cookies -- reused across runs
LOGIN_URL = "https://gmatclub.com/forum/ucp.php?mode=login"
FORUM_HOME = "https://gmatclub.com/forum/"
BASE_SEARCH_URL = "https://gmatclub.com/forum/search.php"
PAGE_SIZE = 50
NO_RESULTS_MSG = "No suitable matches were found."
CF_WAIT_MS = 4000
CF_RETRIES = 20
PAGE_TIMEOUT = 60000
CRAWL_DELAY = 2  # seconds between page requests


# ── Load Target Tags ──────────────────────────────────────────────────────────


def load_ds_og_tags(tags_excel: str) -> list:
    df = pd.read_excel(tags_excel, sheet_name="All Tags")
    mask = (df["Category"] == "Data Sufficiency (DS)") & (
        df["Tag Label"].str.startswith("Source: OG")
    )
    rows = df[mask][["Tag ID", "Tag Label"]].reset_index(drop=True)
    tags = [
        {"tag_id": int(r["Tag ID"]), "tag_label": str(r["Tag Label"])}
        for _, r in rows.iterrows()
    ]
    print(f"\n🏷   Found {len(tags)} DS Source:OG tags to scrape:")
    for t in tags:
        print(f"       {t['tag_id']:>6}  {t['tag_label']}")
    return tags


# ── URL Builder ───────────────────────────────────────────────────────────────


def build_url(tag_id: int, start: int = 0) -> str:
    params = [
        ("selected_search_tags[]", tag_id),
        ("search_tags", "exact"),
        ("submit", "Search"),
    ]
    if start:
        params.append(("start", start))
    return BASE_SEARCH_URL + "?" + urlencode(params)


# ── HTML Parser ───────────────────────────────────────────────────────────────


def parse_page(html: str):
    """
    Returns (questions_list, is_done).
    is_done=True means no more pages for this tag.
    """
    if NO_RESULTS_MSG in html:
        return [], True

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.topicsName")
    if not cards:
        return [], False

    questions = []
    for card in cards:
        link_tag = card.select_one("a.topic-link")
        if not link_tag:
            continue

        href = link_tag.get("href", "").strip()
        title = link_tag.get("title", "").strip()
        if not title:
            span = link_tag.select_one("span.topicTitle")
            title = span.get_text(strip=True) if span else ""
        if href.startswith("/"):
            href = "https://gmatclub.com" + href

        cat_tag = card.select_one("p > a")
        category = cat_tag.get_text(strip=True) if cat_tag else ""

        tags_div = card.select_one("div.topic-tags")
        tag_labels = []
        tag_ids = []
        if tags_div:
            for a in tags_div.select("a[href*='tag_id=']"):
                lbl = a.get_text(strip=True)
                m = re.search(r"tag_id=(\d+)", a.get("href", ""))
                if m:
                    tag_labels.append(lbl)
                    tag_ids.append(m.group(1))

        questions.append(
            {
                "Title": title,
                "Link": href,
                "Category": category,
                "Tags": " | ".join(tag_labels),
                "Tag IDs": " | ".join(tag_ids),
            }
        )

    return questions, False


# ── Cloudflare Wait ───────────────────────────────────────────────────────────


async def wait_for_cloudflare(page) -> bool:
    for attempt in range(CF_RETRIES):
        content = await page.content()
        if (
            "Just a moment" not in content
            and "security verification" not in content.lower()
        ):
            return True
        print(f"    ⏳ Cloudflare... ({attempt + 1}/{CF_RETRIES})")
        await page.wait_for_timeout(CF_WAIT_MS)
    return False


# ── Login Handler ─────────────────────────────────────────────────────────────


def is_logged_in(html: str, current_url: str = "") -> bool:
    """Detect if the current page shows a logged-in user."""
    # If we're still on the login page, we definitely aren't logged in yet
    # (the login page itself can contain the word "logout" in its HTML)
    if "ucp.php?mode=login" in current_url:
        return False
    indicators = [
        "ucp.php?mode=logout",
        'class="icon-svg-logout"',
        "My Profile",
    ]
    html_lower = html.lower()
    return any(ind.lower() in html_lower for ind in indicators)


async def login(page, session_file: str, fresh_login: bool = False) -> bool:
    """
    Attempt to restore session from disk first.
    If that fails (or fresh_login=True), open login page for manual login.
    Returns True if logged in successfully.
    """
    session_path = Path(session_file)

    # ── Try restoring saved session ──────────────────────────────────────────
    if not fresh_login and session_path.exists():
        print("\n🔑  Found saved session -- attempting to restore...")
        try:
            cookies = json.loads(session_path.read_text())
            await page.context.add_cookies(cookies)
            await page.goto(FORUM_HOME, timeout=PAGE_TIMEOUT)
            await wait_for_cloudflare(page)
            html = await page.content()
            if is_logged_in(html, page.url):
                print("    ✅  Session restored -- already logged in!")
                return True
            else:
                print("    ⚠️  Saved session expired -- need to log in again.")
        except Exception as e:
            print(f"    ⚠️  Could not restore session: {e}")

    # ── Manual login ─────────────────────────────────────────────────────────
    print("\n🔐  Opening GMAT Club login page...")
    print("    👉  Please log in manually in the browser window.")
    print("    👉  The script will continue automatically once you are logged in.")
    print("    (You have up to 3 minutes)\n")

    await page.goto(LOGIN_URL, timeout=PAGE_TIMEOUT)
    await wait_for_cloudflare(page)

    # Wait up to 3 minutes for user to log in
    for i in range(36):  # 36 x 5s = 180s = 3 minutes
        await page.wait_for_timeout(5000)
        html = await page.content()
        if is_logged_in(html, page.url):
            print("\n    ✅  Login detected! Starting scrape...\n")
            # Save session cookies for next run
            cookies = await page.context.cookies()
            session_path.write_text(json.dumps(cookies, indent=2))
            print(f"    💾  Session saved to {session_file} (reused on next run)")
            return True
        remaining = (36 - i - 1) * 5
        print(f"    ⏳  Waiting for login... ({remaining}s remaining)", end="\r")

    print("\n    ❌  Login timeout. Please run the script again.")
    return False


# ── Per-Tag Paginator ─────────────────────────────────────────────────────────


async def scrape_one_tag(page, tag: dict, seen_links: set, save_html: str = "") -> list:
    tag_id = tag["tag_id"]
    tag_label = tag["tag_label"]
    collected = []
    start = 0
    page_num = 1

    print(f"\n  ── {tag_label}  (id={tag_id}) ──────────────────────────")

    while True:
        url = build_url(tag_id, start)
        print(f"    Page {page_num}  start={start}")

        try:
            await page.goto(url, timeout=PAGE_TIMEOUT)
            # Wait for JS to finish populating links and tags
            await page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT)
        except Exception as e:
            print(f"    ✗ Navigation failed: {e}")
            break

        if not await wait_for_cloudflare(page):
            print("    ⚠️  Cloudflare did not clear -- skipping this tag.")
            break

        # Safety check: did we get logged out mid-scrape?
        html = await page.content()
        if not is_logged_in(html, page.url):
            print("    ⚠️  Session expired mid-scrape! Please re-run the script.")
            break

        # Save first page HTML for debugging if requested
        if save_html and page_num == 1 and start == 0:
            Path(save_html).write_text(html, encoding="utf-8")
            print(f"    💾  Saved page HTML to {save_html}")

        rows, done = parse_page(html)

        if done:
            print(f"    ✅  No more results for this tag.")
            break

        if not rows:
            print(f"    ⚠️  Zero cards found -- stopping this tag.")
            break

        new_rows = [r for r in rows if r["Link"] not in seen_links]
        seen_links.update(r["Link"] for r in new_rows)
        collected.extend(new_rows)

        dupes = len(rows) - len(new_rows)
        print(
            f"    ✓  {len(new_rows):>3} new  |  {dupes:>3} dupes  |  tag total: {len(collected)}"
        )

        if len(rows) < PAGE_SIZE:
            print(f"    ✅  Last page.")
            break

        start += PAGE_SIZE
        page_num += 1
        await asyncio.sleep(CRAWL_DELAY)

    return collected


# ── Master Orchestrator ───────────────────────────────────────────────────────


async def run_scraper(
    tags: list, output: str, session_file: str, fresh_login: bool, save_html: str = ""
):
    all_rows = []
    seen_links = set()
    tag_buckets = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context()
        page = await context.new_page()

        # Stealth
        await page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

        # Login
        logged_in = await login(page, session_file, fresh_login)
        if not logged_in:
            await browser.close()
            return

        # Scrape all tags
        for tag in tags:
            rows = await scrape_one_tag(page, tag, seen_links, save_html=save_html)
            tag_buckets[tag["tag_label"]] = rows
            all_rows.extend(rows)
            print(f"    📦  {tag['tag_label']}: {len(rows)} unique questions")

        await browser.close()

    print(f"\n{'='*60}")
    print(f"  Total unique questions scraped: {len(all_rows)}")
    print(f"{'='*60}")
    save_excel(all_rows, tag_buckets, output)


# ── Offline Test Mode ─────────────────────────────────────────────────────────


def run_offline(tags: list, html_file: str, output: str):
    print(f"\n📄  Offline mode -- parsing: {html_file}")
    html = Path(html_file).read_text(encoding="utf-8", errors="replace")
    rows, _ = parse_page(html)
    print(f"    Parsed {len(rows)} questions")

    tag_id_to_label = {str(t["tag_id"]): t["tag_label"] for t in tags}
    tag_buckets = {t["tag_label"]: [] for t in tags}

    for row in rows:
        for tid in row["Tag IDs"].split(" | "):
            if tid in tag_id_to_label:
                tag_buckets[tag_id_to_label[tid]].append(row)

    save_excel(rows, tag_buckets, output)


# ── Excel Saver ───────────────────────────────────────────────────────────────

# openpyxl rejects control characters outside the allowed XML 1.0 range
_ILLEGAL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean(value):
    if isinstance(value, str):
        return _ILLEGAL_CHARS.sub("", value)
    return value


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.applymap(_clean)


HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
ALT_FILL = PatternFill("solid", fgColor="EBF3FB")


def _style_sheet(ws, df: pd.DataFrame):
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )

    link_col = None
    for idx, col_cell in enumerate(ws[1], start=1):
        if col_cell.value == "Link":
            link_col = idx
            break

    for row_idx in range(2, ws.max_row + 1):
        if row_idx % 2 == 0:
            for cell in ws[row_idx]:
                cell.fill = ALT_FILL
        if link_col:
            cell = ws.cell(row=row_idx, column=link_col)
            if cell.value and str(cell.value).startswith("http"):
                cell.hyperlink = cell.value
                cell.font = Font(color="0563C1", underline="single")

    col_widths = {
        "No": 6,
        "Title": 55,
        "Link": 30,
        "Category": 22,
        "Tags": 70,
        "Tag IDs": 30,
    }
    for col_cells in ws.columns:
        header = col_cells[0].value
        width = col_widths.get(header, 18)
        ws.column_dimensions[col_cells[0].column_letter].width = width

    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"


def save_excel(all_rows: list, tag_buckets: dict, path: str):
    if not all_rows:
        print("⚠️  No data to save.")
        return

    all_df = _clean_df(pd.DataFrame(all_rows))
    all_df.insert(0, "No", range(1, len(all_df) + 1))

    summary_rows = [
        {"Tag Label": lbl, "Question Count": len(rows)}
        for lbl, rows in tag_buckets.items()
        if rows
    ]
    summary_rows.append(
        {"Tag Label": "TOTAL (deduplicated)", "Question Count": len(all_rows)}
    )
    summary_df = pd.DataFrame(summary_rows)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        all_df.to_excel(writer, sheet_name="All Questions", index=False)
        _style_sheet(writer.sheets["All Questions"], all_df)

        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        ws_sum = writer.sheets["Summary"]
        for cell in ws_sum[1]:
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
        ws_sum.column_dimensions["A"].width = 30
        ws_sum.column_dimensions["B"].width = 18

        for tag_label, rows in tag_buckets.items():
            if not rows:
                continue
            sheet_name = tag_label.replace("Source: ", "")[:31]
            t_df = _clean_df(pd.DataFrame(rows))
            t_df.insert(0, "No", range(1, len(t_df) + 1))
            t_df.to_excel(writer, sheet_name=sheet_name, index=False)
            _style_sheet(writer.sheets[sheet_name], t_df)

    print(f"\n✅  Saved {len(all_rows)} questions --> {path}")
    non_empty = len([b for b in tag_buckets.values() if b])
    print(f"    Sheets: 'All Questions' + 'Summary' + {non_empty} tag sheets")


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Scrape GMAT Club PS x Source:OG questions (with login)"
    )
    parser.add_argument(
        "--tags-excel",
        default=TAGS_EXCEL,
        help=f"Path to gmatclub_tags.xlsx (default: {TAGS_EXCEL})",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_EXCEL,
        help=f"Output Excel filename (default: {OUTPUT_EXCEL})",
    )
    parser.add_argument(
        "--session",
        default=SESSION_FILE,
        help=f"Session cookie file (default: {SESSION_FILE})",
    )
    parser.add_argument(
        "--fresh-login",
        action="store_true",
        help="Force re-login even if a saved session exists",
    )
    parser.add_argument(
        "--test-html",
        metavar="FILE",
        help="Offline test: parse a saved HTML instead of launching browser",
    )
    parser.add_argument(
        "--save-html",
        metavar="FILE",
        default="",
        help="Save the first scraped page's HTML to FILE for debugging",
    )
    args = parser.parse_args()

    # Resolve tags excel path
    tags_excel = args.tags_excel
    if not Path(tags_excel).exists():
        alt = Path(__file__).parent / tags_excel
        if alt.exists():
            tags_excel = str(alt)
        else:
            sys.exit(f"Cannot find {tags_excel}. Run extract_tags.py first.")

    tags = load_ds_og_tags(tags_excel)

    if args.test_html:
        run_offline(tags, args.test_html, args.output)
        return

    try:
        import nest_asyncio

        nest_asyncio.apply()
    except ImportError:
        pass

    asyncio.run(
        run_scraper(tags, args.output, args.session, args.fresh_login, args.save_html)
    )


if __name__ == "__main__":
    main()
