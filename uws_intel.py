import requests
import os
import json

def get_institutional_news():
    """Fetches high-impact news from the official JSON feed (Scrape-proof)."""
    try:
        # official FF JSON feed is much more reliable than scraping HTML
        url = "https://nfs.forexfactory.com/ff_calendar_thisweek.json"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Filter for High Impact USD news
        high_impact = [event['title'] for event in data if event['impact'] == 'High' and event['country'] == 'USD']
        return list(set(high_impact))
    except Exception as e:
        print(f"News Error: {e}")
        return []

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    api_key = os.getenv("CHART_IMG_KEY")
    chart_id = "Hx0V1y9S" # Your TV Layout
    
    # 1. Get Reliable News
    news = get_institutional_news()
    news_msg = "\n".join([f"🚩 **{n}**" for n in news]) if news else "✅ No High Impact News Today"
    status = "🛑 **RED FOLDER DAY: SQUAT HANDS**" if news else "🟢 Clear for Execution"

    # 2. Get Chart Snapshot
    # If no API key, we use a public mini-chart as a fallback
    if api_key:
        chart_url = f"https://api.chart-img.com/v2/tradingview/advanced-chart/storage?symbol=CME_MINI:NQ1!&layout={chart_id}&height=600&width=1000"
        headers = {"x-api-key": api_key}
        response = requests.get(chart_url, headers=headers)
        
        # Try to get the URL from the response
        try:
            image_url = response.json().get('url', "")
        except:
            image_url = ""
    else:
        # Public Fallback (Still professional, but doesn't need a key)
        image_url = f"https://api.chart-img.com/v1/tradingview/mini-chart?symbol=NASDAQ:NQ1!&theme=dark&width=800&height=400"

    # 3. Build and Send Embed
    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": 0xff0000 if news else 0x00ff00, # Red if news, Green if clear
        "description": f"**Market Status:** {status}\n\n**Economic Intel:**\n{news_msg}",
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
