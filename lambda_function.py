import os
import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from datetime import date

load_dotenv()

def generate_comment(jackpot_value):
    if jackpot_value < 3000000:
        return ""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ""

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    prompt = (
    f"TOTO jackpot ${jackpot_value:,}. "
    "Write ONE Singlish sentence (10–14 words) encouraging to buy, with increasing excitement for bigger jackpots. "
    "No emojis, no profanity."
    )   

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 30,
            "temperature": 0.7,
            "responseMimeType": "text/plain"
        }
    }
    data={}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(e)
        try:
            return data.get("candidates", [{}])[0].get("text", "").strip()
        except Exception:
            return ""

def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text})
    r.raise_for_status()

def lambda_handler(event, context):
    mode = event.get("mode")
    token = os.environ.get("BROWSERLESS_TOKEN")
    if not token:
        return {"statusCode": 500, "body": "Missing Browserless token"}

    ws = f"wss://chrome.browserless.io?token={token}"

    if mode == "next_draw":
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws)
            context_pw = browser.new_context()
            page = context_pw.new_page()

            url = "https://www.singaporepools.com.sg/en/product/pages/toto_results.aspx"
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            next_jackpot = page.locator("xpath=//div[normalize-space()='Next Jackpot']/following-sibling::span[1]").inner_text().strip()
            jackpot_value = int("".join(c for c in next_jackpot if c.isdigit()))
            jackpot = f"${jackpot_value:,}"
            comment = generate_comment(jackpot_value)
            draw_date = page.locator("div.toto-draw-date").first.inner_text().strip()

        parts = draw_date.split(",")
        date_part , time_part = parts[1].strip(), parts[2].strip()

        if date_part ==  date.today().strftime('%d %b %Y'):
            msg = f"🎰 TOTO Update\nNext Jackpot: {jackpot}\nNext Draw: Tonight, {time_part}"
        else:
            msg = f"🎰 TOTO Update\nNext Jackpot: {jackpot}\nNext Draw: {draw_date}"

        if comment:
            msg += f"\n\n{comment}"
        

        send_telegram(msg)

        return {"statusCode": 200}
    
    if mode == "results":
        return {"statusCode": 200, "body": "results mode not implemented yet"}


if __name__ == "__main__":
    lambda_handler({"mode": "next_draw"}, None)
