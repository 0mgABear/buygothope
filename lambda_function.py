import os
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
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
            "temperature": 0.7
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
            next_draw_date = page.locator("div.toto-draw-date").first.inner_text().strip()

        parts = next_draw_date.split(",")
        date_part , time_part = parts[1].strip(), parts[2].strip()

        if date_part ==  date.today().strftime('%d %b %Y'):
            msg = f"🎰 TOTO Update\nNext Jackpot: {jackpot}\nNext Draw: Tonight, {time_part}"
        else:
            msg = f"🎰 TOTO Update\nNext Jackpot: {jackpot}\nNext Draw: {next_draw_date}"

        if comment:
            msg += f"\n\n{comment}"
        

        send_telegram(msg)

        return {"statusCode": 200}
    
    if mode == "results":
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws)
            context_pw = browser.new_context()
            page = context_pw.new_page()

            url = "https://www.singaporepools.com.sg/en/product/pages/toto_results.aspx"
            page.goto(url, wait_until="domcontentloaded", timeout=20000)

            draw_date = page.locator("th.drawDate").first.inner_text().strip()
            todays_date = date.today().strftime("%a, %d %b %Y")
            draw_no = page.locator("th.drawNumber").first.inner_text().strip()

            if draw_date != todays_date:
                browser.close()
                return {"statusCode": 200, "body": f"No results today (latest: {draw_date})"}

            winning_nums = page.locator("td.win1, td.win2, td.win3, td.win4, td.win5, td.win6").all_inner_texts()
            winning_nums = [n.strip() for n in winning_nums if n.strip()][:6]

            additional_num = page.locator("td.additional").first.inner_text().strip()

            g1_cells = page.locator("table.tableWinningShares tbody tr").nth(1).locator("td").all_inner_texts()
            g1_cells = [c.strip() for c in g1_cells]
            g1_share_amt = g1_cells[1]
            g1_winners = g1_cells[2]
            g1_winners_int = int("".join(c for c in g1_winners if c.isdigit()) or "0")
 
            group1_outlets = []
            if g1_winners_int >= 1:
                details_link = page.locator("a:has-text('Winning Ticket Details')").first
                details_href = details_link.get_attribute("href")


                if details_href:
                    details_url = (
                        details_href
                        if details_href.startswith("http")
                        else "https://www.singaporepools.com.sg" + details_href
                    )

                    page.goto(details_url, wait_until="domcontentloaded", timeout=20000)

                    page.wait_for_selector("div.divWinningOutlets strong", state="attached", timeout=20000)

                    label = page.locator(
                        "div.divWinningOutlets strong",
                        has_text="Group 1 winning tickets sold at:"
                    ).first

                    if label.count() > 0:
                        ul = label.locator("xpath=ancestor::p[1]/following-sibling::ul[1]")
                        group1_outlets = [x.strip() for x in ul.locator("li").all_inner_texts() if x.strip()]

            browser.close()
                  
        msg = (
            f"🏆 TOTO Results ({draw_date})\n"
            f"{draw_no}\n"
            f"Winning Numbers: {' '.join(winning_nums)}\n"
            f"Additional Number: {additional_num}\n"
            f"Group 1: {g1_share_amt} each ({g1_winners} winner(s))"
        )

        if group1_outlets:
            msg += "\n\n🏪 Group 1 sold at:\n" + "\n".join(f"• {o}" for o in group1_outlets)

        send_telegram(msg)

        return {"statusCode": 200}

if __name__ == "__main__":
    lambda_handler({"mode": "results"}, None)
