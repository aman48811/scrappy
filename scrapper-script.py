# Extract expert answer details from post HTML
from bs4 import BeautifulSoup

def extract_expert_answer(html):
    soup = BeautifulSoup(html, 'html.parser')
    # Find all post-wrapper elements (excluding the first post)
    posts = soup.select('.post-wrapper.post-separator')
    for post in posts:
        # Check for expert tag
        expert_tag = post.select_one('.expert.box.top')
        if expert_tag:
            # Get expert name
            expert_name_tag = post.select_one('.poster-name')
            expert_name = expert_name_tag.get_text(strip=True) if expert_name_tag else ''
            # Get answer detail (all text inside .item.text)
            answer_detail_tag = post.select_one('.item.text')
            answer_detail = answer_detail_tag.get_text("\n", strip=True) if answer_detail_tag else ''
            return expert_name, answer_detail
    return 'no expert answer found', 'no expert answer found'

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import os
import math


# Batch config
BATCH_SIZE = 50
INPUT_EXCEL = "1000-DS-GMAT-Club.xlsx"
INPUT_EXCEL_PATH = os.path.join(os.path.dirname(__file__), INPUT_EXCEL)

# Helper to get next batch of valid links
def get_next_batch(batch_num=1):
    df = pd.read_excel(INPUT_EXCEL_PATH)
    # Assume columns: A=Index, B=Link, C=Source1, D=Source2, E=ID
    valid_rows = []
    for idx, row in df.iterrows():
        link = str(row[1]).strip()
        if link.startswith("http://") or link.startswith("https://"):
            valid_rows.append({
                "link": link,
                "source1": row[2] if len(row) > 2 else '',
                "source2": row[3] if len(row) > 3 else '',
                "id": row[4] if len(row) > 4 else '',
            })
    total_batches = math.ceil(len(valid_rows) / BATCH_SIZE)
    start = (batch_num - 1) * BATCH_SIZE
    end = start + BATCH_SIZE
    batch = valid_rows[start:end]
    return batch, total_batches


# 🔥 Clean text (remove junk after Show Answer)

def clean_text(text):
    if "Show Answer" in text:
        text = text.split("Show Answer")[0]
    return text.strip()

# Extract question stem (text up to the first '?')
def extract_question_stem(text):
    idx = text.find('?')
    if idx != -1:
        return text[:idx+1].strip()
    return text.strip()


# 🔥 Extract statements (DS type)
def extract_statements(text):
    s1, s2 = "", ""

    match1 = re.search(r'(?:1\)|Statement \(1\))(.+?)(?:2\)|Statement \(2\))', text, re.S)
    match2 = re.search(r'(?:2\)|Statement \(2\))(.+)', text, re.S)

    if match1:
        s1 = match1.group(1).strip()
    if match2:
        s2 = match2.group(1).strip()

    return s1, s2


async def main():
    # Determine batch number from output files
    batch_num = 1
    while os.path.exists(f"gmatclub_batch_{batch_num}.xlsx"):
        batch_num += 1
    batch, total_batches = get_next_batch(batch_num)
    print(f"Processing batch {batch_num} of {total_batches} ({len(batch)} links)")

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show browser window for manual Cloudflare solving and login
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        page = await browser.new_page()

        # Stealth
        await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """)

        for i, row in enumerate(batch, 1):
            url = row["link"]
            print(f"\n[{i}/{len(batch)}] Opening... {url}")

            try:
                await page.goto(url, timeout=60000)

                # Cloudflare wait (increase retries and wait time)
                cloudflare_cleared = False
                for attempt in range(20):
                    content = await page.content()
                    if "Just a moment" not in content and "security verification" not in content:
                        cloudflare_cleared = True
                        break
                    print(f"⏳ Waiting for Cloudflare... (attempt {attempt+1}/20)")
                    await page.wait_for_timeout(4000)
                if not cloudflare_cleared:
                    print("⚠️ Cloudflare did not clear after retries.")

                # Wait for question container (increase timeout)
                try:
                    await page.wait_for_selector("#posts .post-wrapper.first-post .item.text", timeout=30000)
                except Exception as selector_exc:
                    print(f"⚠️ Selector not found after 30s: {selector_exc}")
                    # Print a snippet of the page content for debugging
                    page_html = await page.content()
                    print("--- PAGE CONTENT START ---")
                    print(page_html[:2000])
                    print("--- PAGE CONTENT END ---")
                    raise selector_exc

                # Extract raw text
                element = await page.query_selector("#posts .post-wrapper.first-post .item.text")

                if element:
                    raw_text = await element.inner_text()
                else:
                    raw_text = "Not found"

                # Clean text
                cleaned = clean_text(raw_text)

                # Extract statements
                s1, s2 = extract_statements(cleaned)

                print("✓ Extracted")

            except Exception as e:
                print("✗ Failed:", e)
                cleaned = "Failed"
                s1, s2 = "", ""

            question_stem = extract_question_stem(cleaned)

            # Get page HTML for expert answer extraction
            page_html = await page.content()
            answer_by, answer_detail = extract_expert_answer(page_html)

            results.append({
                "No": i,
                "ID": row["id"],
                "Source 1": row["source1"],
                "Source 2": row["source2"],
                "Link": url,
                "Question + Text": cleaned,
                "question-stem": question_stem,
                "Statement 1": s1,
                "Statement 2": s2,
                "answer-by": answer_by,
                "answer-detail": answer_detail,
            })

            await asyncio.sleep(3)

        await browser.close()


    # Save batch output
    output_file = f"gmatclub_batch_{batch_num}.xlsx"
    df = pd.DataFrame(results)
    df.to_excel(output_file, index=False)
    print(f"\n✅ Saved batch {batch_num} to {output_file}")


# Run
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
