import requests
import os

def get_news():
    """Fetches high-impact USD news from a stable JSON mirror."""
    # Using a stable CDN mirror for ForexFactory data
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # High impact USD events only
            return [e['title'] for e in data if e.get('impact') == 'High' and e.get('country') == 'USD']
    except Exception as e:
        print(f"News error: {e}")
    return []

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    api_key = os.getenv("CHART_IMG_KEY")
    layout_id = "Hx0V1y9S" # Your Layout Link ID
    
    # 1. Gather News
    news_list = get_news()
    news_msg = "\n".join([f"🚩 **{n}**" for n in news_list]) if news_list else "✅ No High Impact News Today"
    status = "🛑 **RED FOLDER DAY: SQUAT HANDS**" if news_list else "🟢 Clear for Execution"

    # 2. Capture TV Layout Snapshot (V2 API)
    # Using the 'layout-chart' endpoint captures YOUR exact drawings/indicators
    image_url = ""
    if api_key:
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {"x-api-key": api_key}
        params = {"width": 1000, "height": 600, "theme": "dark"}
        
        try:
            # We use POST for the layout-chart endpoint
            res = requests.post(api_url, headers=headers, json=params, timeout=20)
            if res.status_code == 200:
                image_url = res.json().get('url', "")
        except Exception as e:
            print(f"Chart Error: {e}")

    # Fallback image if API fails
    if not image_url:
        image_url = f"https://api.chart-img.com/v1/tradingview/mini-chart?symbol=CME_MINI:NQ1!&theme=dark"

    # 3. Final Discord Payload
    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": 0xff0000 if news_list else 0x00ff00,
        "description": f"**Market Status:** {status}\n\n**Economic Intel:**\n{news_msg}",
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
