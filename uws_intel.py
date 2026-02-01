import requests
import os
from datetime import datetime, timezone

def get_market_news():
    """Fetches high-impact news from Finnhub (Stable alternative to Yahoo)."""
    api_key = os.getenv("FINNHUB_KEY")
    # Category 'general' provides the best institutional headlines
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        # Takes the top 3 headlines
        return "\n".join([f"• [{n['headline']}]({n['url']})" for n in data[:3]])
    except:
        return "⚠️ *Market intelligence feed temporarily throttled.*"

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
    chart_id = "Hx0V1y9S"
    
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_market_news()
    
    # --- Professional Logic & Sidebar ---
    if today_news:
        status_text, side_color = "⚠️ **VOLATILITY ALERT**", 0xe74c3c # Red
        intel_detail = "\n".join([f"-# {e}" for e in today_news])
    else:
        status_text, side_color = "🟢 **CONDITIONS FAVORABLE**", 0x2ecc71 # Green
        next_e = upcoming_news[0] if upcoming_news else None
        intel_detail = f"-# Next Event: {next_e['title']} ({next_e['date']} @ {next_e['time']})" if next_e else "-# No major releases."

    # --- ADVANCED CHART FIX ---
    # Using POST to the v2 storage endpoint with your Chart ID
    chart_url = f"https://api.chart-img.com/v2/tradingview/advanced-chart/storage"
    payload = {
        "symbol": "CME_MINI:NQ1!",
        "layout": chart_id,
        "theme": "dark",
        "height": 600,
        "width": 1000
    }
    headers = {"x-api-key": chart_key}
    
    try:
        res = requests.post(chart_url, json=payload, headers=headers, timeout=20)
        image_url = res.json().get('url', "")
    except:
        image_url = ""

    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": side_color,
        "description": f"{status_text}\n\n**Economic Intel**\n{intel_detail}",
        "fields": [{"name": "🗞️ Market Briefing", "value": headlines}],
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
