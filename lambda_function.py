import os
import shutil
import subprocess
import re
from playwright.sync_api import sync_playwright

def ensure_chromium_cached():
    if os.path.exists(CHROMIUM_DST):
        return
    shutil.copytree(CHROMIUM_SRC, CHROMIUM_DST)
    os.chmod(CHROME_PATH, 0o755)

def scrape_next_draw():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--no-zygote",
                "--single-process",
            ],
        )

        page = browser.new_page()
        page.goto(
            "https://www.singaporepools.com.sg/en/product/pages/toto_results.aspx",
            wait_until="networkidle",
            timeout=15000
        )

        text = page.inner_text("body")

        jackpot_match = re.search(r"Next Jackpot\s*\$([0-9,]+)\s*est", text)
        jackpot = (
            f"Next Jackpot: ${jackpot_match.group(1)} est"
            if jackpot_match else "Next Jackpot: Not found"
        )

        draw_match = re.search(
            r"Next Draw\s*\n?\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*\d{1,2}\s*[A-Za-z]{3}\s*\d{4}\s*,\s*\d{1,2}\.\d{2}[ap]m",
            text,
        )
        draw = (
            draw_match.group().replace("\n", " ").strip()
            if draw_match else "Next Draw: Not found"
        )

        browser.close()
        return jackpot, draw


def lambda_handler(event, context):
    jackpot, draw = scrape_next_draw()
    message = jackpot + "\n" + draw
    print(message)
    return {"statusCode": 200, "body": message}