"""
GMAT Club -- CR x Source: OG  Full Scraper  (with Login)
=========================================================
Scrapes ALL questions tagged with any "Source: OG *" tag
inside the Critical Reasoning (CR) category.

Merged from:
  - scrape_cr_og.py     (Phase 1: link collection, Phase 2: content extraction)
  - scrape_questions.py (rich extraction: difficulty, expert answer, answer-detail)

Answer Strategy
---------------
  Primary answer  : spoiler div (OA set by question poster)
  Fallback answer : regex on expert answer detail text

Login Strategy
--------------
1. Browser opens to GMAT Club login page
2. YOU log in manually (handles Cloudflare + 2FA naturally)
3. Script detects when login is complete and starts scraping automatically
4. Session is saved to disk -- next run skips login entirely

What it does
------------
1. Reads gmatclub_tags.xlsx to get the CR Source:OG tag IDs
2. For each tag ID, paginates through ALL search result pages (start=0,50,100...)
3. From every question card captures: Title, Link, Category, Tags, Tag IDs
4. Deduplicates globally -- a question under multiple OG tags is saved only once
5. Visits each question page and extracts:
      Question Stem, Question + Text, A-E options, Answer (spoiler),
      Difficulty, Source, answer-by, answer-detail
6. Saves progress every BATCH_SIZE questions -- prompts to continue or quit
7. Auto-resumes from existing output file if re-run after a crash

Output
------
  CR_OG_questions_extracted.xlsx

Columns
-------
  No | Title | Link | Category | Tags | Tag IDs | Difficulty | Source |
  Question Stem | Question + Text | A | B | C | D | E | Answer |
  answer-by | answer-detail

Usage
-----
  python scrape_cr_og.py                        # normal run
  python scrape_cr_og.py --fresh-login          # force re-login
  python scrape_cr_og.py --start-row 51         # resume from row 51
  python scrape_cr_og.py --no-prompt            # skip enter-to-continue prompts
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
OUTPUT_EXCEL = "CR_OG_questions_extracted.xlsx"
SESSION_FILE = "gmatclub_session.json"
LOGIN_URL = "https://gmatclub.com/forum/ucp.php?mode=login"
FORUM_HOME = "https://gmatclub.com/forum/"
BASE_SEARCH_URL = "https://gmatclub.com/forum/search.php"
PAGE_SIZE = 50
BATCH_SIZE = 50  # save + prompt every N questions in Phase 2
NO_RESULTS_MSG = "No suitable matches were found."
CF_WAIT_MS = 4000
CF_RETRIES = 20
PAGE_TIMEOUT = 60000
CRAWL_DELAY = 2  # seconds between search-result page requests
CONTENT_DELAY = 1.5  # seconds between individual question page fetches

COL_ORDER = [
    "No",
    "Title",
    "Link",
    "Category",
    "Tags",
    "Tag IDs",
    "Difficulty",
    "Source",
    "Question + Text",
    "Passage",
    "Question Stem",
    "A",
    "B",
    "C",
    "D",
    "E",
    "Answer",
    "answer-by",
    "answer-detail",
]

COL_WIDTHS = {
    "No": 6,
    "Title": 45,
    "Link": 30,
    "Category": 22,
    "Tags": 55,
    "Tag IDs": 25,
    "Difficulty": 22,
    "Source": 35,
    "Question + Text": 80,
    "Passage": 80,
    "Question Stem": 60,
    "A": 55,
    "B": 55,
    "C": 55,
    "D": 55,
    "E": 55,
    "Answer": 10,
    "answer-by": 20,
    "answer-detail": 80,
}


# ── Load Target Tags ──────────────────────────────────────────────────────────


def load_cr_og_tags(tags_excel: str) -> list:
    df = pd.read_excel(tags_excel, sheet_name="All Tags")
    mask = (df["Category"] == "Critical Reasoning (CR)") & (
        df["Tag Label"].str.startswith("Source: OG")
    )
    rows = df[mask][["Tag ID", "Tag Label"]].reset_index(drop=True)
    tags = [
        {"tag_id": int(r["Tag ID"]), "tag_label": str(r["Tag Label"])}
        for _, r in rows.iterrows()
    ]
    print(f"\n🏷   Found {len(tags)} CR Source:OG tags to scrape:")
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


# ── Text Helpers ──────────────────────────────────────────────────────────────

_ILLEGAL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
# Matches option lines: "(A) text", "A) text", "A. text", "A text" (with various spaces)
_OPT_RE = re.compile(r"^\(?([A-E])[).​‏\xad\xa0​  \t]+(.+)$")

# Noise markers — strip from first occurrence to end of text
_NOISE_STOPS = [
    "ID - CR",
    "ID - DS",
    "ID - SC",
    "ID - RC",
    "Need more similar questions?",
    "Run a ",
    "Show Answer",
    "Show Tags",
    "GMAT Club Forum Quiz",
]


def _strip_noise(text: str) -> str:
    """Remove quiz prompts, ID labels, and other trailing noise."""
    for stop in _NOISE_STOPS:
        idx = text.find(stop)
        if idx != -1:
            text = text[:idx].rstrip()
    return text


def _clean(value):
    if isinstance(value, str):
        return _ILLEGAL_CHARS.sub("", value)
    return value


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.applymap(_clean)


def _clean_text(text: str) -> str:
    """Strip zero-width characters and collapse excessive whitespace."""
    text = text.replace("​", "").replace("‏", "").replace("­", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_difficulty(tags: str) -> str:
    for part in tags.split(" | "):
        p = part.strip()
        if re.search(r"\d{3}[-\u2013]\d{3}|Sub \d{3}|700\+|800\+", p):
            return re.sub(r"^Difficulty:\s*", "", p).strip()
    return ""


def extract_sources(tags: str) -> str:
    sources = []
    for part in tags.split(" | "):
        p = part.strip()
        if p.startswith("Source:"):
            sources.append(p.replace("Source:", "").strip())
    return " | ".join(sources)


def extract_answer_letter(text: str) -> str:
    """Regex fallback to find answer letter from expert answer text."""
    patterns = [
        r"[Aa]nswer(?:\s+is)?[:\s]+([A-Ea-e])\b",
        r"\bOA[:\s]+([A-Ea-e])\b",
        r"[Cc]orrect\s+answer\s+is\s+([A-Ea-e])\b",
        r"[Tt]he\s+answer\s+(?:is\s+)?([A-Ea-e])\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1).upper()
    return ""


# ── Search Page Parser ────────────────────────────────────────────────────────


def parse_search_page(html: str):
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


# ── Question Page Parser ──────────────────────────────────────────────────────


def parse_question_page(html: str) -> dict:
    """
    Full extraction from a CR question page.
    Returns dict with all content fields.
    """
    soup = BeautifulSoup(html, "html.parser")

    # ── Tags ──────────────────────────────────────────────────────────────────
    taglist_div = soup.select_one("div#taglist")
    tag_labels, tag_ids = [], []
    if taglist_div:
        for a in taglist_div.select("a.tag_css_link[href*='tag_id=']"):
            lbl = a.get_text(strip=True)
            m = re.search(r"tag_id=(\d+)", a.get("href", ""))
            if lbl and m:
                tag_labels.append(lbl)
                tag_ids.append(m.group(1))

    tags_str = " | ".join(tag_labels)
    tag_ids_str = " | ".join(tag_ids)

    # ── First post ────────────────────────────────────────────────────────────
    item_text = soup.select_one("div.item.text")

    # ── Spoiler answer (primary) ──────────────────────────────────────────────
    spoiler = item_text.select_one("div[id^='spoiler_']") if item_text else None
    raw_spoiler = spoiler.get_text(strip=True) if spoiler else ""
    spoiler_match = re.search(r"[A-E]", raw_spoiler)
    answer = spoiler_match.group(0) if spoiler_match else ""

    if not item_text:
        return {
            "Question + Text": "",
            "Passage": "",
            "Question Stem": "",
            "A": "",
            "B": "",
            "C": "",
            "D": "",
            "E": "",
            "Answer": answer,
            "Tags": tags_str,
            "Tag IDs": tag_ids_str,
            "Difficulty": extract_difficulty(tags_str),
            "Source": extract_sources(tags_str),
            "answer-by": "",
            "answer-detail": "",
        }

    # Remove noise before text extraction
    for sel in (
        "div.twoRowsBlock",
        "div.post_signature",
        "div.answer-block",
        "div[id^='spoiler_']",
        "div.quiz-link",
        "div.quizBlock",
        "p.quiz-prompt",
        "script",
        "style",
    ):
        for el in item_text.select(sel):
            el.decompose()

    for br in item_text.find_all("br"):
        br.replace_with("\n")

    raw_text = item_text.get_text(separator="")
    text = _strip_noise(_clean_text(raw_text))

    # ── Options A-E ───────────────────────────────────────────────────────────
    lines = [l.strip() for l in text.split("\n")]
    options = {}
    opt_start_i = None

    for i, line in enumerate(lines):
        m = _OPT_RE.match(line)
        if m:
            letter = m.group(1)
            if letter not in options:
                options[letter] = m.group(2).strip()
                if opt_start_i is None:
                    opt_start_i = i

    # ── Passage + Question Stem ───────────────────────────────────────────────
    pre_lines = lines[:opt_start_i] if opt_start_i is not None else lines
    pre_text = "\n".join(pre_lines)
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", pre_text) if p.strip()]

    if len(paragraphs) >= 2:
        question_stem = paragraphs[-1]
        passage = "\n\n".join(paragraphs[:-1])
    elif paragraphs:
        question_stem = paragraphs[0]
        passage = ""
    else:
        question_stem = ""
        passage = ""

    option_block = "\n".join(
        f"{letter} {options[letter]}" for letter in "ABCDE" if options.get(letter)
    )
    full_text = "\n\n".join(p for p in [passage, question_stem, option_block] if p)

    # ── Expert Answer ─────────────────────────────────────────────────────────
    answer_by, answer_detail = "", ""
    posts = soup.select(".post-wrapper.post-separator")
    for post in posts:
        if post.select_one(".expert.box.top"):
            name_tag = post.select_one(".poster-name")
            detail_tag = post.select_one(".item.text")
            answer_by = name_tag.get_text(strip=True) if name_tag else ""
            answer_detail = detail_tag.get_text("\n", strip=True) if detail_tag else ""
            break

    # Fallback: if spoiler gave no answer, try expert detail
    if not answer and answer_detail:
        answer = extract_answer_letter(answer_detail)

    return {
        "Question + Text": full_text,
        "Passage": passage,
        "Question Stem": question_stem,
        "A": options.get("A", ""),
        "B": options.get("B", ""),
        "C": options.get("C", ""),
        "D": options.get("D", ""),
        "E": options.get("E", ""),
        "Answer": answer,
        "Tags": tags_str,
        "Tag IDs": tag_ids_str,
        "Difficulty": extract_difficulty(tags_str),
        "Source": extract_sources(tags_str),
        "answer-by": answer_by,
        "answer-detail": answer_detail,
    }


# ── Cloudflare Wait ───────────────────────────────────────────────────────────


async def wait_for_cloudflare(page) -> bool:
    for attempt in range(CF_RETRIES):
        content = await _safe_page_content(page)
        if (
            "Just a moment" not in content
            and "security verification" not in content.lower()
        ):
            return True
        print(f"    ⏳ Cloudflare... ({attempt + 1}/{CF_RETRIES})")
        await page.wait_for_timeout(CF_WAIT_MS)
    return False


async def _safe_page_content(page, retries: int = 3, delay_ms: int = 500) -> str:
    for attempt in range(retries):
        try:
            return await page.content()
        except Exception as exc:
            message = str(exc).lower()
            if "page.content" not in message or "navigating" not in message:
                raise
            if attempt == retries - 1:
                raise
            await page.wait_for_load_state("load", timeout=PAGE_TIMEOUT)
            await page.wait_for_timeout(delay_ms)
    return await page.content()


# ── Login Handler ─────────────────────────────────────────────────────────────


def is_logged_in(html: str) -> bool:
    html_lower = html.lower()
    has_logout = "ucp.php?mode=logout" in html or 'class="icon-svg-logout"' in html
    has_login_form = 'name="username"' in html or 'type="password"' in html
    has_user_area = (
        "my profile" in html_lower
        or "my posts" in html_lower
        or 'class="user-panel"' in html
    )
    return has_logout and not has_login_form and has_user_area


async def login(page, session_file: str, fresh_login: bool = False) -> bool:
    session_path = Path(session_file)

    if not fresh_login and session_path.exists():
        print("\n🔑  Found saved session -- attempting to restore...")
        try:
            cookies = json.loads(session_path.read_text())
            await page.context.add_cookies(cookies)
            await page.goto(FORUM_HOME, timeout=PAGE_TIMEOUT)
            await wait_for_cloudflare(page)
            if is_logged_in(await _safe_page_content(page)):
                print("    ✅  Session restored -- already logged in!")
                return True
            print("    ⚠️  Saved session expired -- need to log in again.")
            try:
                session_path.unlink()
            except:
                pass
        except Exception as e:
            print(f"    ⚠️  Could not restore session: {e}")

    print("\n🔐  Opening GMAT Club login page...")
    print("    👉  Please log in manually in the browser window.")
    print("    👉  Script continues automatically once login is detected.")
    print("    (You have up to 3 minutes)\n")
    await page.goto(LOGIN_URL, timeout=PAGE_TIMEOUT)
    await wait_for_cloudflare(page)

    for i in range(36):
        if is_logged_in(await _safe_page_content(page)):
            print("\n    ✅  Login detected! Starting scrape...\n")
            cookies = await page.context.cookies()
            session_path.write_text(json.dumps(cookies, indent=2))
            print(f"    💾  Session saved to {session_file}")
            return True
        remaining = (36 - i) * 5
        print(f"    ⏳  Waiting for login... ({remaining}s remaining)", end="\r")
        await page.wait_for_timeout(5000)

    print("\n    ❌  Login timeout. Please re-run the script.")
    return False


# ── Phase 1: Collect Links per Tag ────────────────────────────────────────────


async def collect_links_for_tag(
    page, tag: dict, seen_links: set, link_sources: dict
) -> list:
    tag_id = tag["tag_id"]
    tag_label = tag["tag_label"]
    # Strip "Source: " prefix for display in the Source column
    source_label = tag_label.replace("Source: ", "").strip()
    collected = []
    start = 0
    page_num = 1

    print(f"\n  ── {tag_label}  (id={tag_id}) ──────────────────────────")

    while True:
        url = build_url(tag_id, start)
        print(f"    Page {page_num}  start={start}")

        try:
            await page.goto(url, timeout=PAGE_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT)
        except Exception as e:
            print(f"    ✗ Navigation failed: {e}")
            break

        if not await wait_for_cloudflare(page):
            print("    ⚠️  Cloudflare did not clear -- skipping this tag.")
            break

        html = await _safe_page_content(page)
        if not is_logged_in(html):
            print("    ⚠️  Session expired mid-scrape! Please re-run.")
            break

        rows, done = parse_search_page(html)

        if done:
            print(f"    ✅  No more results for this tag.")
            break
        if not rows:
            print(f"    ⚠️  Zero cards found -- stopping this tag.")
            break

        # Track source label for every link on this page (including dupes)
        for r in rows:
            link = r["Link"]
            if source_label not in link_sources.setdefault(link, []):
                link_sources[link].append(source_label)

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


# ── Phase 2: Fetch Question Content ──────────────────────────────────────────


async def fetch_all_content(
    page, rows: list, output_excel: str, no_prompt: bool = False
) -> list:
    total = len(rows)
    results = []

    print(f"\n{'='*60}")
    print(f"  Phase 2: Extracting content for {total} questions")
    print(f"  Saving every {BATCH_SIZE} questions  →  {output_excel}")
    print(f"{'='*60}\n")

    for i, row in enumerate(rows, start=1):
        url = str(row.get("Link", "")).strip()
        if not url.startswith("http"):
            print(f"  [{i:>4}/{total}] Skipping invalid link: {url}")
            continue

        print(f"  [{i:>4}/{total}]  {url}", end="  ")

        try:
            await page.goto(url, timeout=PAGE_TIMEOUT)
            await wait_for_cloudflare(page)

            try:
                await page.wait_for_selector(
                    "#posts .post-wrapper.first-post .item.text", timeout=20000
                )
            except Exception:
                pass

            html = await _safe_page_content(page)
            content = parse_question_page(html)

            # Merge: question-page tags override search-card tags;
            # Source is set from Phase 1 tag collection — do not overwrite from website
            merged = {**row}
            for field in (
                "Tags",
                "Tag IDs",
                "Difficulty",
                "Question + Text",
                "Passage",
                "Question Stem",
                "A",
                "B",
                "C",
                "D",
                "E",
                "Answer",
                "answer-by",
                "answer-detail",
            ):
                merged[field] = content.get(field, "")

            results.append(merged)

            has_all_opts = all(merged.get(l) for l in "ABCDE")
            print(
                f"✓  Answer={merged['Answer'] or '?'}  "
                f"Options={'ABCDE' if has_all_opts else 'partial'}  "
                f"Expert={'yes' if merged['answer-by'] else 'no'}"
            )

        except Exception as e:
            print(f"✗  {e}")
            row.setdefault("Question + Text", "")
            row.setdefault("Passage", "")
            row.setdefault("Question Stem", "")
            for l in "ABCDE":
                row.setdefault(l, "")
            row.setdefault("Answer", "")
            row.setdefault("Difficulty", "")
            row.setdefault("Source", "")
            row.setdefault("answer-by", "")
            row.setdefault("answer-detail", "")
            results.append(row)

        await asyncio.sleep(CONTENT_DELAY)

        # ── Checkpoint every BATCH_SIZE questions ─────────────────────────────
        if i % BATCH_SIZE == 0:
            save_excel_results(results, output_excel)
            print(f"\n  📦  Checkpoint: {len(results)} rows saved → {output_excel}")
            if not no_prompt:
                answer = await asyncio.get_event_loop().run_in_executor(
                    None, input, "  ▶  Press Enter to continue, or type 'q' to stop: "
                )
                if answer.strip().lower() == "q":
                    print("  🛑  Stopped by user.")
                    break
            print()

    return results


# ── Excel Saver ───────────────────────────────────────────────────────────────

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
ALT_FILL = PatternFill("solid", fgColor="EBF3FB")


def _style_sheet(ws):
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

    for row_idx in range(2, ws.max_row + 1):
        if row_idx % 2 == 0:
            for cell in ws[row_idx]:
                cell.fill = ALT_FILL
        if link_col:
            cell = ws.cell(row=row_idx, column=link_col)
            if cell.value and str(cell.value).startswith("http"):
                cell.hyperlink = cell.value
                cell.font = Font(color="0563C1", underline="single")

    for col_cells in ws.columns:
        header = col_cells[0].value
        ws.column_dimensions[col_cells[0].column_letter].width = COL_WIDTHS.get(
            header, 20
        )

    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"


def save_excel_results(results: list, path: str, tag_buckets: dict = None) -> None:
    if not results:
        print("⚠️  No data to save.")
        return

    df = _clean_df(pd.DataFrame(results))
    for col in COL_ORDER[1:]:  # skip "No"
        if col not in df.columns:
            df[col] = ""
    # Drop "No" if already present (e.g. from auto-resumed existing data)
    if "No" in df.columns:
        df = df.drop(columns=["No"])
    df.insert(0, "No", range(1, len(df) + 1))
    df = df[COL_ORDER]

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="All Questions", index=False)
        _style_sheet(writer.sheets["All Questions"])

        if tag_buckets:
            summary_rows = [
                {"Tag Label": lbl, "Question Count": len(rows)}
                for lbl, rows in tag_buckets.items()
                if rows
            ]
            summary_rows.append(
                {"Tag Label": "TOTAL (deduplicated)", "Question Count": len(results)}
            )
            summary_df = pd.DataFrame(summary_rows)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            ws_sum = writer.sheets["Summary"]
            for cell in ws_sum[1]:
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
            ws_sum.column_dimensions["A"].width = 30
            ws_sum.column_dimensions["B"].width = 18

            for tag_label, t_rows in tag_buckets.items():
                if not t_rows:
                    continue
                sheet_name = re.sub(r'[:\\/?*\[\]]+', "-", tag_label.replace("Source: ", "")).strip()[:31]
                t_df = _clean_df(pd.DataFrame(t_rows))
                for col in COL_ORDER[1:]:
                    if col not in t_df.columns:
                        t_df[col] = ""
                t_df.insert(0, "No", range(1, len(t_df) + 1))
                t_df = t_df[COL_ORDER]
                t_df.to_excel(writer, sheet_name=sheet_name, index=False)
                _style_sheet(writer.sheets[sheet_name])

    non_empty = len([b for b in tag_buckets.values() if b]) if tag_buckets else 0
    sheets_info = (
        f"'All Questions' + 'Summary' + {non_empty} tag sheets"
        if tag_buckets
        else "'All Questions'"
    )
    print(f"\n✅  Saved {len(results)} questions → {path}")
    print(f"    Sheets: {sheets_info}")


# ── Master Orchestrator ───────────────────────────────────────────────────────


async def run_scraper(
    tags: list,
    output: str,
    session_file: str,
    fresh_login: bool,
    start_row: int,
    no_prompt: bool,
):
    all_rows = []
    seen_links = set()
    tag_buckets = {}
    link_sources: dict = {}  # {link: [source_label, ...]} — built during Phase 1

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
        await page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

        if not await login(page, session_file, fresh_login):
            await browser.close()
            return

        # ── Phase 1: collect links ────────────────────────────────────────────
        print(f"\n{'='*60}")
        print(f"  Phase 1: Collecting question links...")
        print(f"{'='*60}")

        for tag in tags:
            rows = await collect_links_for_tag(page, tag, seen_links, link_sources)
            tag_buckets[tag["tag_label"]] = rows
            all_rows.extend(rows)
            print(f"    📦  {tag['tag_label']}: {len(rows)} unique questions")

        print(f"\n  Total unique questions found: {len(all_rows)}")

        # Stamp Source on every row from the Phase 1 tag collection
        for row in all_rows:
            row["Source"] = " | ".join(link_sources.get(row["Link"], []))

        # ── Auto-resume: skip already-done links ──────────────────────────────
        output_path_obj = Path(output)
        existing_results = []
        rows_to_fetch = all_rows

        if output_path_obj.exists() and start_row == 1:
            try:
                df_existing = pd.read_excel(output)
                done_links = set(df_existing["Link"].dropna().astype(str))
                rows_to_fetch = [
                    r
                    for r in all_rows
                    if str(r.get("Link", "")).strip() not in done_links
                ]
                existing_results = df_existing.to_dict("records")
                print(
                    f"\n    ♻  Auto-resume: {len(done_links)} already done, "
                    f"{len(rows_to_fetch)} remaining"
                )
            except Exception as e:
                print(f"    ⚠  Could not auto-resume: {e}")

        # Manual --start-row override
        if start_row > 1:
            rows_to_fetch = all_rows[start_row - 1 :]
            print(
                f"\n    ▶  Resuming from row {start_row} "
                f"({len(rows_to_fetch)} questions remaining)"
            )

        # ── Phase 2: fetch content ────────────────────────────────────────────
        new_results = await fetch_all_content(
            page, rows_to_fetch, output, no_prompt=no_prompt
        )

        # Rebuild tag_buckets with extracted content for per-tag sheets
        all_results = existing_results + new_results
        link_to_result = {r.get("Link"): r for r in all_results}
        final_tag_buckets = {
            lbl: [
                link_to_result[r["Link"]] for r in rows if r["Link"] in link_to_result
            ]
            for lbl, rows in tag_buckets.items()
        }

        await browser.close()

    # Final save with all sheets
    print(f"\n{'='*60}")
    print(f"  Done! {len(all_results)} questions total.")
    print(f"{'='*60}")
    save_excel_results(all_results, output, tag_buckets=final_tag_buckets)


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Scrape GMAT Club CR x Source:OG questions (full extraction)"
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
        "--start-row",
        type=int,
        default=1,
        help="Skip to this row in Phase 2 (1-indexed)",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Skip the Enter-to-continue prompt at each checkpoint",
    )
    args = parser.parse_args()

    tags_excel = args.tags_excel
    if not Path(tags_excel).exists():
        alt = Path(__file__).parent / tags_excel
        if alt.exists():
            tags_excel = str(alt)
        else:
            sys.exit(f"Cannot find {tags_excel}.")

    tags = load_cr_og_tags(tags_excel)
    if not tags:
        sys.exit("No CR Source:OG tags found in gmatclub_tags.xlsx.")

    print(f"\n{'='*60}")
    print(f"  GMAT Club CR Scraper -- Full Extraction")
    print(f"{'='*60}")
    print(f"  Output  : {args.output}")
    print(f"  Session : {args.session}")
    print(f"  Start row (Phase 2): {args.start_row}")
    print(f"  Auto-prompt at checkpoint: {not args.no_prompt}")

    try:
        import nest_asyncio

        nest_asyncio.apply()
    except ImportError:
        pass

    asyncio.run(
        run_scraper(
            tags=tags,
            output=args.output,
            session_file=args.session,
            fresh_login=args.fresh_login,
            start_row=args.start_row,
            no_prompt=args.no_prompt,
        )
    )


if __name__ == "__main__":
    main()
