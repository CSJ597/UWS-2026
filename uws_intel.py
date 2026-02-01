import requests
import os
from datetime import datetime, timezone

def get_market_news(api_key):
    """Fetches news and shortens titles for a cleaner terminal look."""
    if not api_key:
        return "⚠️ *System Error: FINNHUB_API_KEY mapping failed.*"
    
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            headlines = []
            for n in data[:3]:
                title = n['headline']
                # Shorten to 60 characters for institutional look
                short_title = (title[:57] + '...') if len(title) > 60 else title
                headlines.append(f"• [{short_title}]({n['url']})")
            return "\n".join(headlines)
        return "⚠️ *No fresh headlines found.*"
    except:
        return "⚠️ *Finnhub API connection error.*"

def get_economic_calendar():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%m-%d-%Y")
        
        today_events, future_events = [], []
        for event in data:
            if event.get('impact') == 'High' and event.get('country') == 'USD':
                event_date, event_time = event.get('date'), event.get('time')
                event_dt = datetime.strptime(f"{event_date} {event_time}", "%m-%d-%Y %I:%M%p").replace(tzinfo=timezone.utc)
                if event_date == today_str:
                    today_events.append(f"🚩 {event['title']} at {event_time}")
                elif event_dt > now:
                    future_events.append(event)
        return today_events, future_events
    except: return [], []

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    layout_id = "Hx0V1y9S"
    
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_market_news(finnhub_key)
    
    # Status Logic
    status_text, side_color = ("⚠️ **VOLATILITY ALERT**", 0xe74c3c) if today_news else ("🟢 **CONDITIONS FAVORABLE**", 0x2ecc71)
    status_sub = "Heightened Volatility Anticipated" if today_news else "Clear for Execution"
    
    if today_news:
        intel_title = "Today's High Impact News"
        intel_detail = "\n".join([f"-# {e}" for e in today_news])
    else:
        intel_title = "Upcoming Economic Intelligence"
        next_e = upcoming_news[0] if upcoming_news else None
        intel_detail = f"-# Next Event: {next_e['title']} ({next_e['date']} @ {next_e['time']})" if next_e else "-# No major releases."

    # --- THE CHART FIX ---
    image_url = ""
    if chart_key:
        # Using the advanced storage endpoint to ensure Discord unfurls the image
        api_url = f"https://api.chart-img.com/v2/tradingview/advanced-chart/storage"
        headers = {"x-api-key": chart_key}
        payload = {
            "symbol": "CME_MINI:NQ1!",
            "layout": layout_id,
            "width": 1200, 
            "height": 800, 
            "theme": "dark"
        }
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=20)
            image_url = res.json().get('url', "")
        except: pass

    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": side_color,
        "description": f"{status_text}\n{status_sub}\n\n**{intel_title}**\n{intel_detail}",
        "fields": [{"name": "🗞️ Market Briefing", "value": headlines}],
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
