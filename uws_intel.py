import requests
import os
import time
from datetime import datetime, timezone

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    session_id = os.getenv("TV_SESSION_ID")
    layout_id = "Hx0V1y9S"

    image_url = ""
    if chart_key:
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {
            "x-api-key": chart_key,
            "tradingview-session-id": session_id 
        }
        
        try:
            # We give it a small head-start for the Private V6 to load
            time.sleep(3) 
            res = requests.post(api_url, json={"width": 800, "height": 600, "theme": "dark"}, headers=headers, timeout=60)
            
            if res.status_code == 200:
                image_url = res.json().get('url', "")
                print(f"Success! V6 Render: {image_url}")
            else:
                print(f"Status {res.status_code}: {res.text}")
                # Fallback to the advanced storage method to bypass direct permission blocks
                print("Switching to Advanced Storage Bypass...")
                fallback = requests.post("https://api.chart-img.com/v2/tradingview/advanced-chart/storage",
                    json={"symbol": "CME_MINI:NQ1!", "layout": layout_id, "width": 800, "height": 600, "theme": "dark"},
                    headers=headers)
                image_url = fallback.json().get('url', "")
        except Exception as e:
            print(f"Error: {e}")

    embed = {
        "title": "🏛️ UNDERGROUND UPDATE",
        "color": 0x2ecc71,
        "description": "🟢 **CONDITIONS FAVORABLE**\nPrivate V6 Indicators Active.",
        "image": {"url": image_url} if image_url else None,
        "footer": {"text": "UWS Intel Desk | Follow the Money"}
    }
    
    if webhook:
        requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
