"""
Step 1 — GMAT Club Tag Extractor
=================================
Parses the locally saved Search.html to extract every tag (value + label)
grouped by question category (Problem Solving, Data Sufficiency, etc.).

Output: gmatclub_tags.xlsx
  Columns: Category | Category Forum ID | Tag ID | Tag Label

Usage:
    python extract_tags.py
    # or point to any saved copy of https://gmatclub.com/forum/search.php?view=search_tags
    python extract_tags.py --html path/to/Search.html
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    import pandas as pd
except ImportError:
    sys.exit(
        "Missing dependencies. Run:  pip install beautifulsoup4 pandas openpyxl"
    )


# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_HTML = Path(__file__).parent / "Search.html"


# ── Core Parsing ──────────────────────────────────────────────────────────────

def extract_tags(html: str) -> list[dict]:
    """
    Walk every  <div class="tagColumn" data-id="...">
    and pull all checkbox → label pairs inside it.

    Returns a list of dicts:
        {category, category_forum_id, tag_id, tag_label}
    """
    soup = BeautifulSoup(html, "html.parser")
    records = []

    # Each question-type section lives in a div.tagColumn with a data-id
    tag_columns = soup.select("div.tagColumn[data-id]")

    if not tag_columns:
        print("⚠️  No <div class='tagColumn'> elements found — check the HTML file.")
        return records

    for col in tag_columns:
        # Category name comes from the <h3> inside the column
        h3 = col.find("h3")
        category = h3.get_text(strip=True) if h3 else "Unknown"
        category_forum_id = col.get("data-id", "")

        # Every tag is wrapped in a <span> with an <input> and <label>
        for span in col.select("span"):
            inp = span.find("input", {"name": "selected_search_tags[]"})
            lbl = span.find("label")

            if inp and lbl:
                tag_id    = inp.get("value", "").strip()
                tag_label = lbl.get_text(strip=True)

                records.append({
                    "Category":           category,
                    "Category Forum ID":  category_forum_id,
                    "Tag ID":             tag_id,
                    "Tag Label":          tag_label,
                })

    return records


# ── Excel Writer ──────────────────────────────────────────────────────────────

def write_excel(records: list[dict], output_path: str = "gmatclub_tags.xlsx") -> None:
    df = pd.DataFrame(records, columns=["Category", "Category Forum ID", "Tag ID", "Tag Label"])

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # ── Sheet 1 : All tags flat ──────────────────────────────────────────
        df.to_excel(writer, sheet_name="All Tags", index=False)

        # ── Sheet 2 : One sheet per category ────────────────────────────────
        for category, group in df.groupby("Category", sort=False):
            # Excel sheet names are max 31 chars; strip the "(PS)" style suffix
            safe_name = category[:31]
            group[["Tag ID", "Tag Label"]].reset_index(drop=True).to_excel(
                writer, sheet_name=safe_name, index=False
            )

        # ── Auto-size columns on "All Tags" sheet ───────────────────────────
        ws = writer.sheets["All Tags"]
        for col_cells in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col_cells)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 60)

    print(f"✅  Saved {len(records)} tags → {output_path}")


# ── Source Tag Quick-Reference (matches note.txt) ─────────────────────────────

def print_source_tags_summary(records: list[dict]) -> None:
    """
    Print a quick lookup table for 'Source: OG …' tags —
    the ones you'll use most often when building search URLs.
    """
    source_tags = [r for r in records if r["Tag Label"].startswith("Source:")]
    if not source_tags:
        return

    print("\n📌  Source Tags (quick reference for building search URLs):")
    print(f"  {'Tag ID':<10} {'Label'}")
    print(f"  {'-'*8}  {'-'*40}")
    for r in source_tags:
        print(f"  {r['Tag ID']:<10} {r['Tag Label']}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract GMAT Club search tags to Excel.")
    parser.add_argument(
        "--html",
        default=str(DEFAULT_HTML),
        help="Path to saved Search.html (default: ./Search.html)",
    )
    parser.add_argument(
        "--output",
        default="gmatclub_tags.xlsx",
        help="Output Excel filename (default: gmatclub_tags.xlsx)",
    )
    args = parser.parse_args()

    html_path = Path(args.html)
    if not html_path.exists():
        sys.exit(f"❌  File not found: {html_path}")

    print(f"📄  Reading: {html_path}")
    html = html_path.read_text(encoding="utf-8", errors="replace")

    records = extract_tags(html)
    if not records:
        sys.exit("❌  No tags extracted — check the HTML structure.")

    print(f"🏷   Found {len(records)} tags across {len(set(r['Category'] for r in records))} categories")

    # Summary grouped by category
    from collections import Counter
    counts = Counter(r["Category"] for r in records)
    for cat, n in counts.items():
        print(f"    • {cat:<40} {n:>4} tags")

    print_source_tags_summary(records)

    write_excel(records, args.output)


if __name__ == "__main__":
    main()
