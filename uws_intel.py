import requests
import os
from datetime import datetime, timezone

def get_ticker_news(api_key):
    if not api_key: return "⚠️ *FINNHUB_API_KEY mapping failed.*"
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        assets = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"], "ES": ["s&p 500", "sp500", "market"]}
        found = {asset: None for asset in assets}
        for item in data:
            headline = item['headline']
            for asset, keywords in assets.items():
                if any(k in headline.lower() for k in keywords) and found[asset] is None:
                    title = (headline[:47] + '...') if len(headline) > 50 else headline
                    found[asset] = f"• **{asset}**: [{title}]({item['url']})"
        brief = [found[a] for a in assets if found[a]]
        return "\n".join(brief) if brief else "• No specific asset intel found."
    except: return "⚠️ *News feed throttled.*"

def get_economic_calendar():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        response = requests.get(url, timeout=15).json()
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%m-%d-%Y")
        today, future = [], []
        for e in response:
            if e.get('impact') == 'High' and e.get('country') == 'USD':
                dt = datetime.strptime(f"{e['date']} {e['time']}", "%m-%d-%Y %I:%M%p").replace(tzinfo=timezone.utc)
                if e['date'] == today_str:
                    today.append(f"🚩 {e['title']} at {e['time']}")
                elif dt > now:
                    future.append(e)
        return today, future
    except: return [], []

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    layout_id = "Hx0V1y9S"
    
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_ticker_news(finnhub_key)
    
    status, color = ("⚠️ **VOLATILITY ALERT**", 0xe74c3c) if today_news else ("🟢 **CONDITIONS FAVORABLE**", 0x2ecc71)
    sub = "Heightened Volatility Anticipated" if today_news else "Clear for Execution"
    title = "Upcoming Economic Intelligence" if not today_news else "Today's High Impact News"
    detail = "\n".join([f"-# {e}" for e in today_news]) if today_news else f"-# Next: {upcoming_news[0]['title']} ({upcoming_news[0]['date']} @ {upcoming_news[0]['time']})" if upcoming_news else "-# No releases."

    # --- THE STORAGE FIX (Ensures Discord shows the image) ---
    image_url = ""
    if chart_key:
        # Advanced Chart To Storage is the most reliable endpoint for Discord
        api_url = "https://api.chart-img.com/v2/tradingview/advanced-chart/storage"
        headers = {"x-api-key": chart_key}
        payload = {
            "symbol": "CME_MINI:NQ1!", # Primary ticker
            "layout": layout_id,
            "width": 800, 
            "height": 600, 
            "theme": "dark"
        }
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=25)
            # The API returns a 'url' key pointing to the saved file
            image_url = res.json().get('url', "")
        except: pass

    embed = {
        "title": "🏛️ UNDERGROUND UPDATE",
        "color": color,
        "description": f"{status}\n{sub}\n\n**{title}**\n{detail}",
        "fields": [{"name": "🗞️ Market Briefing", "value": headlines}],
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
