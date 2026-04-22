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

URLS = [
    "https://gmatclub.com/forum/if-today-the-price-of-an-item-is-3-600-what-was-the-price-of-the-ite-189749.html",
    "https://gmatclub.com/forum/by-what-percent-has-the-price-of-an-overcoat-been-reduced-189750.html",
    "https://gmatclub.com/forum/if-the-longfellow-playground-is-rectangular-what-is-its-width-189751.html",
    "https://gmatclub.com/forum/what-is-the-value-of-x-1-1-x-1-3-2-x-399547.html",
    "https://gmatclub.com/forum/is-william-taller-than-jane-1-william-is-taller-than-anna-2-anna-189752.html",
]

OUTPUT_FILE = "gmatclub_clean.xlsx"


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


        for i, url in enumerate(URLS, 1):
            print(f"\n[{i}/{len(URLS)}] Opening...")

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
                "URL": url,
                "Question + Text": cleaned,
                "question-stem": question_stem,
                "Statement 1": s1,
                "Statement 2": s2,
                "answer-by": answer_by,
                "answer-detail": answer_detail,
            })

            await asyncio.sleep(3)

        await browser.close()

    df = pd.DataFrame(results)
    df.to_excel(OUTPUT_FILE, index=False)

    print("\n✅ Saved:", OUTPUT_FILE)


# Run
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
