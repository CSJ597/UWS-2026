import requests
import os
import time
from datetime import datetime, timezone

def get_ticker_news(api_key):
    if not api_key: return "⚠️ *FINNHUB_API_KEY missing.*"
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        data = requests.get(url, timeout=10).json()
        assets = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]}
        found = {asset: None for asset in assets}
        for item in data:
            for asset, keywords in assets.items():
                if any(k in item['headline'].lower() for k in keywords) and not found[asset]:
                    title = (item['headline'][:42] + '...') if len(item['headline']) > 45 else item['headline']
                    found[asset] = f"• **{asset}**: [{title}]({item['url']})"
        return "\n".join([found[a] for a in assets if found[a]])
    except: return "⚠️ *News feed throttled.*"

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    session_id = os.getenv("TV_SESSION_ID")
    layout_id = "Hx0V1y9S"

    headlines = get_ticker_news(finnhub_key)

    image_url = ""
    if chart_key:
        # Layout-chart is the ONLY way to see unpublished draft scripts
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {
            "x-api-key": chart_key,
            "tradingview-session-id": session_id # THIS UNLOCKS UNPUBLISHED V6
        }
        payload = {"width": 800, "height": 600, "theme": "dark"}
        
        try:
            # v6 can be slow to compile; we give it a full 60 seconds
            res = requests.post(api_url, json=payload, headers=headers, timeout=60)
            if res.status_code == 200:
                image_url = res.json().get('url', "")
            else:
                print(f"API Error {res.status_code}: {res.text}")
        except: pass

    embed = {
        "title": "🏛️ UNDERGROUND UPDATE",
        "color": 0x2ecc71,
        "description": "🟢 **CONDITIONS FAVORABLE**\nClear for Execution",
        "fields": [{"name": "🗞️ Market Briefing", "value": headlines}],
        "image": {"url": image_url} if image_url else None,
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    if webhook:
        requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
