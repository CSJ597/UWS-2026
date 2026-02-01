import requests
import os
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
        brief = [found[a] for a in assets if found[a]]
        return "\n".join(brief) if brief else "• No specific asset intel found."
    except: return "⚠️ *News feed throttled.*"

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    
    # --- GET YOUR SESSION INFO ---
    # In your browser: F12 > Application > Cookies > sessionid
    session_id = os.getenv("TV_SESSION_ID") 
    layout_id = "Hx0V1y9S" 
    
    headlines = get_ticker_news(finnhub_key)
    
    # --- THE V6 RENDER FIX ---
    image_url = ""
    if chart_key:
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {
            "x-api-key": chart_key,
            "tradingview-session-id": session_id # This forces v6 indicators to load
        }
        payload = {"width": 800, "height": 600, "theme": "dark"}
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=25)
            if res.status_code == 200:
                image_url = res.json().get('url', "")
        except: pass

    embed = {
        "title": "🏛️ UNDERGROUND UPDATE",
        "color": 0x2ecc71,
        "description": "🟢 **CONDITIONS FAVORABLE**\nClear for Execution",
        "fields": [{"name": "🗞️ Market Briefing", "value": headlines}],
        "image": {"url": image_url} if image_url else None,
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
