import requests
import os
import yfinance as yf
from datetime import datetime, timezone

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

def get_market_news():
    """Improved news fetcher with a backup to avoid 'Awaiting data' messages."""
    try:
        # We try NQ=F first, but fallback to general market news if blocked
        ticker = yf.Ticker("NQ=F")
        news = ticker.news[:3]
        if not news:
            news = yf.Search("Nasdaq News", news_count=3).news
        return "\n".join([f"• [{n['title']}]({n['link']})" for n in news])
    except:
        return "⚠️ *Data feed temporarily throttled. Check TradingView for live headlines.*"

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_id = "Hx0V1y9S"
    
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_market_news()
    
    # --- Professional Logic & Styling ---
    if today_news:
        status_text = "⚠️ **VOLATILITY ALERT**"
        status_sub = "Heightened Volatility Anticipated"
        side_color = 0xe74c3c # Red
        intel_detail = "\n".join([f"-# {e}" for e in today_news])
    else:
        status_text = "🟢 **CONDITIONS FAVORABLE**"
        status_sub = "Clear for Execution"
        side_color = 0x2ecc71 # Green
        if upcoming_news:
            next_e = upcoming_news[0]
            intel_detail = f"-# Next Event: {next_e['title']} ({next_e['date']} @ {next_e['time']})"
        else:
            intel_detail = "-# No major USD releases scheduled."

    chart_url = f"https://api.chart-img.com/v1/tradingview/advanced-chart/storage?symbol=CME_MINI:NQ1!&layout={chart_id}&height=600&width=1000"

    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": side_color,
        "description": f"{status_text}\n{status_sub}\n\n**Economic Intel**\n{intel_detail}",
        "fields": [
            {"name": "🗞️ Market Briefing", "value": headlines, "inline": False}
        ],
        "image": {"url": chart_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
