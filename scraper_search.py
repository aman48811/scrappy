"""
Step 2 — GMAT Club Search-Page Scraper
========================================
Given one or more search tag IDs (from gmatclub_tags.xlsx), this script:

  1. Auto-paginates every search-results page (start=0, 50, 100 …)
  2. From each question card extracts:
       - Question title / snippet
       - Direct link to the question page
       - All tags attached (tag label + tag ID)
       - Forum category (e.g. Problem Solving)
  3. Stops cleanly when "No suitable matches were found." appears
  4. Deduplicates across pages (same question can appear in multiple runs)
  5. Saves everything to  question_links_<tag_id>.xlsx

Usage examples
--------------
# Single tag — OG 2025-2026 under Problem Solving
python scraper_search.py --tags 2067

# Multiple tags at once (each gets its own output file)
python scraper_search.py --tags 2067 2063 2061

# Combine two tags with AND logic (both must match)
python scraper_search.py --tags 2067 140 --mode all

# Use a locally saved HTML file for testing (no browser needed)
python scraper_search.py --tags 2067 --test-html Search-by-tags.html

Requirements
------------
pip install playwright pandas openpyxl beautifulsoup4
playwright install chromium
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

try:
    from bs4 import BeautifulSoup
    import pandas as pd
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit(
        "Missing dependencies.\n"
        "Run: pip install playwright pandas openpyxl beautifulsoup4\n"
        "     playwright install chromium"
    )


# ── Constants ─────────────────────────────────────────────────────────────────

BASE_SEARCH_URL = "https://gmatclub.com/forum/search.php"
PAGE_SIZE       = 50          # GMAT Club returns 50 results per page
CLOUDFLARE_WAIT = 4_000       # ms between Cloudflare retry checks
CF_RETRIES      = 20          # max attempts before giving up on CF
PAGE_TIMEOUT    = 60_000      # ms for page.goto()
NO_RESULTS_MSG  = "No suitable matches were found."


# ── URL Builder ───────────────────────────────────────────────────────────────

def build_search_url(tag_ids: list[int], start: int = 0, mode: str = "any") -> str:
    """
    Build a GMAT Club search URL for the given tag IDs.

    mode='any'  → search_tags=exact  (show questions matching ANY of the tags)
    mode='all'  → search_tags=all    (show questions matching ALL tags)

    The URL pattern observed in the wild:
      https://gmatclub.com/forum/search.php?
        selected_search_tags[]=2067&
        search_tags=exact&
        submit=Search&
        start=50
    """
    params = []
    for tid in tag_ids:
        params.append(("selected_search_tags[]", tid))
    params.append(("search_tags", "exact" if mode == "any" else "all"))
    params.append(("submit", "Search"))
    if start:
        params.append(("start", start))
    return BASE_SEARCH_URL + "?" + urlencode(params)


# ── HTML Parser ───────────────────────────────────────────────────────────────

def parse_search_results(html: str) -> tuple[list[dict], bool]:
    """
    Parse one search-results page.

    Returns
    -------
    (questions, done)
        questions : list of dicts — one per question card
        done      : True if "No suitable matches" detected → stop pagination
    """
    if NO_RESULTS_MSG in html:
        return [], True

    soup  = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.topicsName")

    if not cards:
        # Might be a Cloudflare/login wall with no cards at all
        return [], False

    questions = []
    for card in cards:
        # ── Question link + title ────────────────────────────────────────────
        link_tag = card.select_one("a.topic-link")
        if not link_tag:
            continue

        href  = link_tag.get("href", "").strip()
        title = link_tag.get("title", "").strip()

        # Fallback: use the visible <span class="topicTitle"> text
        if not title:
            span = link_tag.select_one("span.topicTitle")
            title = span.get_text(strip=True) if span else ""

        # Normalise relative → absolute URL
        if href.startswith("/"):
            href = "https://gmatclub.com" + href

        # ── Forum category (e.g. "Problem Solving (PS)") ─────────────────────
        category_tag = card.select_one("p > a")
        category = category_tag.get_text(strip=True) if category_tag else ""

        # ── Tags ─────────────────────────────────────────────────────────────
        tags_div = card.select_one("div.topic-tags")
        tag_labels, tag_ids = [], []

        if tags_div:
            for a in tags_div.select("a[href*='tag_id=']"):
                label = a.get_text(strip=True)
                # Extract numeric tag_id from  /forum/search.php?search_id=tag&tag_id=217
                m = re.search(r"tag_id=(\d+)", a.get("href", ""))
                if m:
                    tag_labels.append(label)
                    tag_ids.append(m.group(1))

        questions.append(
            {
                "Title":      title,
                "Link":       href,
                "Category":   category,
                "Tags":       " | ".join(tag_labels),      # human-readable
                "Tag IDs":    " | ".join(tag_ids),         # machine-readable
            }
        )

    return questions, False


# ── Cloudflare Helper ─────────────────────────────────────────────────────────

async def wait_for_cloudflare(page) -> bool:
    """Spin-wait until Cloudflare challenge is gone. Returns True if cleared."""
    for attempt in range(CF_RETRIES):
        content = await page.content()
        if "Just a moment" not in content and "security verification" not in content.lower():
            return True
        print(f"  ⏳ Cloudflare… (attempt {attempt + 1}/{CF_RETRIES})")
        await page.wait_for_timeout(CLOUDFLARE_WAIT)
    return False


# ── Core Scraper ──────────────────────────────────────────────────────────────

async def scrape_tag(
    tag_ids:   list[int],
    mode:      str  = "any",
    test_html: str  = None,
    output:    str  = None,
) -> pd.DataFrame:
    """
    Scrape all pages for the given tag_ids.
    If test_html is provided, parse that file instead of launching a browser.
    """
    label  = "_".join(str(t) for t in tag_ids)
    output = output or f"question_links_{label}.xlsx"

    # ── OFFLINE MODE (for testing / HTML files) ────────────────────────────
    if test_html:
        print(f"📄  Offline mode — reading: {test_html}")
        html = Path(test_html).read_text(encoding="utf-8", errors="replace")
        rows, _ = parse_search_results(html)
        df = pd.DataFrame(rows)
        _save_excel(df, output)
        return df

    # ── ONLINE MODE (Playwright browser) ──────────────────────────────────
    all_rows: list[dict] = []
    seen_links: set[str] = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        page = await browser.new_page()

        # Stealth: hide webdriver flag
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
        )

        start   = 0
        page_no = 1

        while True:
            url = build_search_url(tag_ids, start=start, mode=mode)
            print(f"\n📃  Page {page_no}  (start={start})")
            print(f"    {url}")

            try:
                await page.goto(url, timeout=PAGE_TIMEOUT)
            except Exception as e:
                print(f"  ✗ Navigation failed: {e}")
                break

            if not await wait_for_cloudflare(page):
                print("  ⚠️  Cloudflare did not clear — stopping.")
                break

            html = await page.content()
            rows, done = parse_search_results(html)

            if done:
                print(f"  ✅  '{NO_RESULTS_MSG}' — all pages scraped.")
                break

            if not rows:
                print("  ⚠️  Zero question cards found on this page — stopping.")
                break

            # Deduplicate
            new_rows = [r for r in rows if r["Link"] not in seen_links]
            seen_links.update(r["Link"] for r in new_rows)
            all_rows.extend(new_rows)

            print(f"  ✓  {len(new_rows)} new questions (total so far: {len(all_rows)})")

            # Advance
            start   += PAGE_SIZE
            page_no += 1
            await asyncio.sleep(2)          # polite crawl delay

        await browser.close()

    df = pd.DataFrame(all_rows)
    _save_excel(df, output)
    return df


# ── Excel Writer ──────────────────────────────────────────────────────────────

def _save_excel(df: pd.DataFrame, path: str) -> None:
    if df.empty:
        print("⚠️  No data to save.")
        return

    # Add a sequential index column
    df.insert(0, "No", range(1, len(df) + 1))

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Questions", index=False)

        ws = writer.sheets["Questions"]

        # Auto-size columns
        for col_cells in ws.columns:
            max_len = max(
                len(str(c.value or "")) for c in col_cells
            )
            ws.column_dimensions[col_cells[0].column_letter].width = min(
                max_len + 4, 80
            )

        # Make the Link column clickable (hyperlink style)
        from openpyxl.styles import Font
        link_col_idx = df.columns.get_loc("Link") + 2   # +1 for 0-index, +1 for header row offset... actually openpyxl is 1-indexed
        link_col_letter = ws.cell(row=1, column=link_col_idx).column_letter
        for row_idx, link in enumerate(df["Link"], start=2):
            cell = ws[f"{link_col_letter}{row_idx}"]
            cell.hyperlink = link
            cell.font = Font(color="0563C1", underline="single")

    print(f"\n✅  Saved {len(df)} questions → {path}")
    print(f"    Columns: {list(df.columns)}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scrape GMAT Club search results for given tag IDs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # OG 2025-2026 under Problem Solving
  python scraper_search.py --tags 2067

  # Data Sufficiency OG 2025-2026
  python scraper_search.py --tags 2063

  # Multiple tags (separate output files per tag)
  python scraper_search.py --tags 2067 2063 2061

  # Quick offline test with a saved HTML
  python scraper_search.py --tags 2067 --test-html Search-by-tags.html
        """,
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        type=int,
        required=True,
        help="One or more tag IDs to scrape (space-separated)",
    )
    parser.add_argument(
        "--mode",
        choices=["any", "all"],
        default="any",
        help="'any' = OR logic across tags (default), 'all' = AND logic",
    )
    parser.add_argument(
        "--test-html",
        metavar="FILE",
        help="Parse a locally saved HTML file instead of launching a browser",
    )
    parser.add_argument(
        "--output",
        help="Custom output Excel filename (default: question_links_<tags>.xlsx)",
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Treat all --tags as a single combined search (AND/OR per --mode). "
             "Default: run each tag separately.",
    )
    args = parser.parse_args()

    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass   # Only needed in Jupyter/IPython environments

    if args.combine or len(args.tags) == 1:
        # Single combined run
        asyncio.run(
            scrape_tag(
                tag_ids   = args.tags,
                mode      = args.mode,
                test_html = args.test_html,
                output    = args.output,
            )
        )
    else:
        # Run each tag independently → separate output files
        for tid in args.tags:
            print(f"\n{'='*60}")
            print(f"  Scraping tag: {tid}")
            print(f"{'='*60}")
            asyncio.run(
                scrape_tag(
                    tag_ids   = [tid],
                    mode      = args.mode,
                    test_html = args.test_html,
                    output    = args.output or f"question_links_{tid}.xlsx",
                )
            )


if __name__ == "__main__":
    main()
