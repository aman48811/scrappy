"""
GMAT Club — PS × Source: OG  Full Scraper
==========================================
Scrapes ALL questions tagged with any "Source: OG *" tag
inside the Problem Solving (PS) category.

What it does
------------
1. Reads gmatclub_tags.xlsx (built in Step 1) to get the 14 PS Source:OG tag IDs
2. For each tag ID, paginates through ALL search result pages (start=0,50,100…)
3. From every question card captures:
      Title, Link, Category, Tags (labels), Tag IDs
4. Deduplicates globally — a question appearing under multiple OG tags is saved once
5. Saves a master Excel with:
      • Sheet "All Questions"  — full deduplicated list
      • Sheet per OG tag label — e.g. "OG 2025-2026", "OG 2022" …
      • Sheet "Summary"        — count per tag

Output
------
  PS_OG_questions.xlsx

Usage
-----
  python scrape_ps_og.py                        # live browser scrape
  python scrape_ps_og.py --test-html Search-by-tags.html   # offline test
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode

try:
    from bs4 import BeautifulSoup
    import pandas as pd
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("Run: pip install beautifulsoup4 pandas openpyxl playwright\n"
             "     playwright install chromium")

# ── Config ────────────────────────────────────────────────────────────────────

TAGS_EXCEL       = "gmatclub_tags.xlsx"
OUTPUT_EXCEL     = "PS_OG_questions.xlsx"
BASE_SEARCH_URL  = "https://gmatclub.com/forum/search.php"
PAGE_SIZE        = 50
NO_RESULTS_MSG   = "No suitable matches were found."
CLOUDFLARE_WAIT  = 4_000   # ms
CF_RETRIES       = 20
PAGE_TIMEOUT     = 60_000  # ms
CRAWL_DELAY      = 2       # seconds between page requests


# ── Load Target Tags ──────────────────────────────────────────────────────────

def load_ps_og_tags(tags_excel: str) -> list[dict]:
    """Return list of {tag_id, tag_label} for PS category Source:OG tags."""
    df = pd.read_excel(tags_excel, sheet_name="All Tags")
    mask = (
        (df["Category"] == "Problem Solving (PS)") &
        (df["Tag Label"].str.startswith("Source: OG"))
    )
    rows = df[mask][["Tag ID", "Tag Label"]].reset_index(drop=True)
    result = [
        {"tag_id": int(r["Tag ID"]), "tag_label": str(r["Tag Label"])}
        for _, r in rows.iterrows()
    ]
    print(f"🏷   Found {len(result)} PS Source:OG tags:")
    for t in result:
        print(f"       {t['tag_id']:>6}  {t['tag_label']}")
    return result


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

def parse_page(html: str) -> tuple[list[dict], bool]:
    """
    Parse one search results page.
    Returns (questions_list, is_done).
    is_done=True  → "No matches" seen, stop pagination.
    """
    if NO_RESULTS_MSG in html:
        return [], True

    soup  = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.topicsName")

    if not cards:
        return [], False     # Possibly Cloudflare — caller handles retry

    questions = []
    for card in cards:
        link_tag = card.select_one("a.topic-link")
        if not link_tag:
            continue

        href  = link_tag.get("href", "").strip()
        title = link_tag.get("title", "").strip()
        if not title:
            span  = link_tag.select_one("span.topicTitle")
            title = span.get_text(strip=True) if span else ""
        if href.startswith("/"):
            href = "https://gmatclub.com" + href

        cat_tag  = card.select_one("p > a")
        category = cat_tag.get_text(strip=True) if cat_tag else ""

        tags_div    = card.select_one("div.topic-tags")
        tag_labels  = []
        tag_id_list = []
        if tags_div:
            for a in tags_div.select("a[href*='tag_id=']"):
                lbl = a.get_text(strip=True)
                m   = re.search(r"tag_id=(\d+)", a.get("href", ""))
                if m:
                    tag_labels.append(lbl)
                    tag_id_list.append(m.group(1))

        questions.append({
            "Title":    title,
            "Link":     href,
            "Category": category,
            "Tags":     " | ".join(tag_labels),
            "Tag IDs":  " | ".join(tag_id_list),
        })

    return questions, False


# ── Cloudflare Wait ───────────────────────────────────────────────────────────

async def wait_for_cloudflare(page) -> bool:
    for attempt in range(CF_RETRIES):
        content = await page.content()
        if ("Just a moment" not in content and
                "security verification" not in content.lower()):
            return True
        print(f"    ⏳ Cloudflare… ({attempt + 1}/{CF_RETRIES})")
        await page.wait_for_timeout(CLOUDFLARE_WAIT)
    return False


# ── Per-Tag Paginator ─────────────────────────────────────────────────────────

async def scrape_one_tag(page, tag: dict, seen_links: set) -> list[dict]:
    """
    Paginate through ALL search results pages for one tag.
    Returns only questions whose links have NOT been seen before (dedup).
    Updates seen_links in-place.
    """
    tag_id    = tag["tag_id"]
    tag_label = tag["tag_label"]
    collected = []
    start     = 0
    page_num  = 1

    print(f"\n  ── {tag_label}  (id={tag_id}) ──────────────────────────")

    while True:
        url = build_url(tag_id, start)
        print(f"    Page {page_num}  start={start}  →  {url}")

        try:
            await page.goto(url, timeout=PAGE_TIMEOUT)
        except Exception as e:
            print(f"    ✗ Navigation failed: {e}")
            break

        if not await wait_for_cloudflare(page):
            print("    ⚠️  Cloudflare did not clear — skipping remaining pages for this tag.")
            break

        html         = await page.content()
        rows, done   = parse_page(html)

        if done:
            print(f"    ✅  No more results.")
            break

        if not rows:
            print(f"    ⚠️  Zero cards found — stopping this tag.")
            break

        new_rows = [r for r in rows if r["Link"] not in seen_links]
        seen_links.update(r["Link"] for r in new_rows)
        collected.extend(new_rows)

        print(f"    ✓  {len(new_rows)} new  |  {len(rows) - len(new_rows)} dupes  |  tag total so far: {len(collected)}")

        if len(rows) < PAGE_SIZE:
            # Last page had fewer than 50 results — no need to request next
            print(f"    ✅  Last page (< {PAGE_SIZE} results).")
            break

        start    += PAGE_SIZE
        page_num += 1
        await asyncio.sleep(CRAWL_DELAY)

    return collected


# ── Master Orchestrator ───────────────────────────────────────────────────────

async def run_scraper(tags: list[dict], output: str):
    all_rows:    list[dict]           = []
    seen_links:  set[str]             = set()
    tag_buckets: dict[str, list[dict]] = {}   # tag_label → rows

    async with __import__("playwright.async_api", fromlist=["async_playwright"]).async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        page = await browser.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

        for tag in tags:
            rows = await scrape_one_tag(page, tag, seen_links)
            tag_buckets[tag["tag_label"]] = rows
            all_rows.extend(rows)
            print(f"    📦  {tag['tag_label']}: {len(rows)} unique questions collected")

        await browser.close()

    save_excel(all_rows, tag_buckets, output)


# ── Offline Test Mode ─────────────────────────────────────────────────────────

def run_offline(tags: list[dict], html_file: str, output: str):
    """Parse a single saved HTML file — useful for testing without a browser."""
    print(f"\n📄  Offline mode — parsing: {html_file}")
    html = Path(html_file).read_text(encoding="utf-8", errors="replace")
    rows, _ = parse_page(html)
    print(f"    Parsed {len(rows)} questions from sample HTML")

    # Bucket by whichever OG tags appear on each question
    tag_id_to_label = {str(t["tag_id"]): t["tag_label"] for t in tags}
    tag_buckets: dict[str, list[dict]] = {t["tag_label"]: [] for t in tags}

    for row in rows:
        ids_on_question = row["Tag IDs"].split(" | ")
        matched = False
        for tid in ids_on_question:
            if tid in tag_id_to_label:
                tag_buckets[tag_id_to_label[tid]].append(row)
                matched = True
        if not matched:
            # Shouldn't happen in a correctly filtered search, but keep it safe
            tag_buckets.setdefault("Unmatched", []).append(row)

    save_excel(rows, tag_buckets, output)


# ── Excel Saver ───────────────────────────────────────────────────────────────

HEADER_FILL  = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT  = Font(bold=True, color="FFFFFF", size=11)
ALT_FILL     = PatternFill("solid", fgColor="EBF3FB")

def _style_sheet(ws, df: pd.DataFrame):
    """Apply header styling, alternating row colours, hyperlinks, column widths."""
    # Header row
    for cell in ws[1]:
        cell.fill      = HEADER_FILL
        cell.font      = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Data rows — alternating fill + hyperlinks on Link column
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

    # Column widths
    col_widths = {"No": 6, "Title": 55, "Link": 30, "Category": 22,
                  "Tags": 70, "Tag IDs": 30}
    for col_cells in ws.columns:
        header = col_cells[0].value
        width  = col_widths.get(header, 18)
        ws.column_dimensions[col_cells[0].column_letter].width = width

    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"


def save_excel(all_rows: list[dict], tag_buckets: dict, path: str):
    if not all_rows:
        print("⚠️  No data to save.")
        return

    all_df = pd.DataFrame(all_rows)
    all_df.insert(0, "No", range(1, len(all_df) + 1))

    # Summary
    summary_rows = [
        {"Tag Label": lbl, "Question Count": len(rows)}
        for lbl, rows in tag_buckets.items()
        if rows
    ]
    summary_rows.append({"Tag Label": "TOTAL (deduplicated)", "Question Count": len(all_rows)})
    summary_df = pd.DataFrame(summary_rows)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:

        # ── Sheet 1: All Questions ───────────────────────────────────────────
        all_df.to_excel(writer, sheet_name="All Questions", index=False)
        _style_sheet(writer.sheets["All Questions"], all_df)

        # ── Sheet 2: Summary ─────────────────────────────────────────────────
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        ws_sum = writer.sheets["Summary"]
        for cell in ws_sum[1]:
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
        ws_sum.column_dimensions["A"].width = 30
        ws_sum.column_dimensions["B"].width = 18

        # ── One sheet per OG tag ─────────────────────────────────────────────
        for tag_label, rows in tag_buckets.items():
            if not rows:
                continue
            # Sheet name: "OG 2025-2026", strip the "Source: " prefix, max 31 chars
            sheet_name = tag_label.replace("Source: ", "")[:31]
            t_df = pd.DataFrame(rows)
            t_df.insert(0, "No", range(1, len(t_df) + 1))
            t_df.to_excel(writer, sheet_name=sheet_name, index=False)
            _style_sheet(writer.sheets[sheet_name], t_df)

    print(f"\n✅  Saved {len(all_rows)} questions → {path}")
    print(f"    Sheets: 'All Questions'  +  'Summary'  +  {len([b for b in tag_buckets.values() if b])} tag sheets")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scrape PS × Source:OG questions from GMAT Club")
    parser.add_argument("--tags-excel", default=TAGS_EXCEL,
                        help=f"Path to gmatclub_tags.xlsx (default: {TAGS_EXCEL})")
    parser.add_argument("--output", default=OUTPUT_EXCEL,
                        help=f"Output Excel (default: {OUTPUT_EXCEL})")
    parser.add_argument("--test-html", metavar="FILE",
                        help="Offline test: parse a saved HTML instead of launching browser")
    args = parser.parse_args()

    # Resolve tags excel path
    tags_excel = args.tags_excel
    if not Path(tags_excel).exists():
        # Try same directory as this script
        alt = Path(__file__).parent / tags_excel
        if alt.exists():
            tags_excel = str(alt)
        else:
            sys.exit(f"❌  Cannot find {tags_excel}. Run extract_tags.py first.")

    tags = load_ps_og_tags(tags_excel)

    if args.test_html:
        run_offline(tags, args.test_html, args.output)
    else:
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass
        asyncio.run(run_scraper(tags, args.output))


if __name__ == "__main__":
    main()
