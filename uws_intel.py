import requests
import os
import time
from datetime import datetime, timezone

def main():
    # --- DEBUG: CHECK SECRETS ---
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    layout_id = "Hx0V1y9S"

    print(f"Checking Secrets...")
    print(f"Webhook URL found: {'Yes' if webhook else 'No'}")
    print(f"Chart API Key found: {'Yes' if chart_key else 'No'}")
    print(f"Finnhub Key found: {'Yes' if finnhub_key else 'No'}")

    if not webhook:
        print("ERROR: DISCORD_WEBHOOK_URL is missing. Check GitHub Secrets.")
        return

    # --- 1. GET CHART ---
    image_url = ""
    if chart_key:
        print(f"Requesting chart for layout {layout_id}...")
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {"x-api-key": chart_key}
        payload = {"width": 800, "height": 600, "theme": "dark"}
        
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=30)
            res_data = res.json()
            image_url = res_data.get('url', "")
            if image_url:
                print(f"Chart generated successfully: {image_url}")
            else:
                print(f"Chart API Error: {res_data.get('message', 'No URL returned')}")
        except Exception as e:
            print(f"Chart Connection Failed: {e}")

    # --- 2. SEND TO DISCORD ---
    print("Sending message to Discord...")
    embed = {
        "title": "🏛️ UNDERGROUND UPDATE",
        "color": 0x2ecc71,
        "description": "System Online. Testing data feeds.",
        "image": {"url": image_url} if image_url else None,
        "footer": {"text": f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
    }
    
    try:
        response = requests.post(webhook, json={"embeds": [embed]})
        print(f"Discord Response Code: {response.status_code}")
        if response.status_code != 204:
            print(f"Discord Error: {response.text}")
    except Exception as e:
        print(f"Discord Send Failed: {e}")

if __name__ == "__main__":
    main()
