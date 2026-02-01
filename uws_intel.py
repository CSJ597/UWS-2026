import requests
import os
from datetime import datetime, timezone

def get_ticker_news(api_key):
    if not api_key: return "⚠️ *FINNHUB_API_KEY missing.*"
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        assets = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]}
        found = {asset: None for asset in assets}
        for item in data:
            headline = item['headline']
            for asset, keywords in assets.items():
                if any(k in headline.lower() for k in keywords) and found[asset] is None:
                    title = (headline[:42] + '...') if len(headline) > 45 else headline
                    found[asset] = f"• **{asset}**: [{title}]({item['url']})"
        brief = [found[a] for a in assets if found[a]]
        return "\n".join(brief) if brief else "• No specific asset intel found."
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
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {"x-api-key": chart_key}
        if session_id:
            headers["tradingview-session-id"] = session_id
        
        payload = {"width": 800, "height": 600, "theme": "dark"}
        
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=60)
            print(f"API Status: {res.status_code}")
            
            if res.status_code == 200:
                image_url = res.json().get('url', "")
            elif res.status_code == 403:
                print("FORBIDDEN: Layout sharing is OFF on TradingView.")
                # FALLBACK: Try a generic Nasdaq chart so the message isn't empty
                print("Attempting fallback to generic Nasdaq chart...")
                fallback_res = requests.post(
                    "https://api.chart-img.com/v2/tradingview/advanced-chart/storage",
                    json={"symbol": "CME_MINI:NQ1!", "width": 800, "height": 600, "theme": "dark"},
                    headers={"x-api-key": chart_key}
                )
                image_url = fallback_res.json().get('url', "")
        except Exception as e:
            print(f"Request failed: {e}")

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
