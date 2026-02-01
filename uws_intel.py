import requests
import os
import yfinance as yf
from datetime import datetime, timezone

def get_economic_calendar():
    """Fetches high-impact news and identifies Today vs. Next Upcoming."""
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%m-%d-%Y")
        
        today_events = []
        future_events = []

        for event in data:
            if event.get('impact') == 'High' and event.get('country') == 'USD':
                event_date = event.get('date')
                event_time = event.get('time')
                event_dt = datetime.strptime(f"{event_date} {event_time}", "%m-%d-%Y %I:%M%p").replace(tzinfo=timezone.utc)

                if event_date == today_str:
                    today_events.append(f"🚩 {event['title']} at **{event_time}**")
                elif event_dt > now:
                    future_events.append(event)

        return today_events, future_events
    except Exception:
        return [], []

def get_market_news():
    """Pulls 3 fresh headlines for the Nasdaq."""
    try:
        news = yf.Ticker("NQ=F").news[:3]
        return "\n".join([f"• [{n['title']}]({n['link']})" for n in news])
    except:
        return "Awaiting fresh data."

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    api_key = os.getenv("CHART_IMG_KEY")
    chart_id = "Hx0V1y9S"
    
    today_news, upcoming_news = get_economic_calendar()
    
    # --- Institutional Status Logic ---
    if today_news:
        status_title = "⚠️ VOLATILITY ALERT: HIGH IMPACT DATA"
        status_desc = "Institutional participation may be limited due to scheduled high-impact releases. Market Status: **Heightened Volatility Anticipated**"
        side_color = 0xe74c3c  # Red
        intel_field = "\n".join(today_news)
        intel_header = "Today's High Impact Releases"
    else:
        status_title = "🟢 CONDITIONS FAVORABLE"
        status_desc = "No high-impact USD data scheduled. Market Status: **Clear for Execution**"
        side_color = 0x2ecc71  # Green
        
        if upcoming_news:
            next_e = upcoming_news[0]
            intel_field = f"Next Event: {next_e['title']}\nScheduled: {next_e['date']} at {next_e['time']}"
        else:
            intel_field = "No major USD releases scheduled for the remainder of the week."
        intel_header = "Upcoming Economic Intelligence"

    # --- Chart & Headlines ---
    headlines = get_market_news()
    chart_url = f"https://api.chart-img.com/v1/tradingview/advanced-chart/storage?symbol=CME_MINI:NQ1!&layout={chart_id}&height=600&width=1000"

    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": side_color,
        "description": f"**Current Status:** {status_title}\n{status_desc}",
        "fields": [
            {"name": intel_header, "value": f"```\n{intel_field}\n```", "inline": False},
            {"name": "🗞️ Market Briefing", "value": headlines, "inline": False}
        ],
        "image": {"url": chart_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
