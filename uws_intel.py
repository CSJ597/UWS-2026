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
            # We only track High Impact USD news for the UWS Desk
            if event.get('impact') == 'High' and event.get('country') == 'USD':
                event_date = event.get('date') # Format: "MM-DD-YYYY"
                event_time = event.get('time') # Format: "9:30am"
                
                event_dt = datetime.strptime(f"{event_date} {event_time}", "%m-%d-%Y %I:%M%p").replace(tzinfo=timezone.utc)

                if event_date == today_str:
                    today_events.append(f"🚩 {event['title']} at **{event_time}**")
                elif event_dt > now:
                    future_events.append(event)

        return today_events, future_events
    except Exception:
        return [], []

def get_market_news():
    news = yf.Ticker("NQ=F").news[:3]
    return "\n".join([f"• [{n['title']}]({n['link']})" for n in news])

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_id = "Hx0V1y9S"
    
    today_news, upcoming_news = get_economic_calendar()
    
    # --- Professional Logic ---
    if today_news:
        status_title = "⚠️ VOLATILITY ALERT: HIGH IMPACT DATA"
        status_desc = "Institutional volatility expected. Focus on liquidity and slippage during release windows."
        side_color = 0xe74c3c  # Professional Red
        intel_field = "\n".join(today_news)
        intel_header = "Today's High Impact Releases"
    else:
        status_title = "🟢 CONDITIONS FAVORABLE"
        status_desc = "No high-impact USD data scheduled for today. Technical structure is the primary driver."
        side_color = 0x2ecc71  # Institutional Green
        
        # Look ahead for the next upcoming event
        if upcoming_news:
            next_e = upcoming_news[0]
            intel_field = f"Next Institutional Event: **{next_e['title']}**\nScheduled: {next_e['date']} at **{next_e['time']}**"
        else:
            intel_field = "No major USD releases scheduled for the remainder of the week."
        intel_header = "Upcoming Economic Intelligence"

    # Charts and Headlines
    intelligence = get_market_news()
    chart_url = f"https://api.chart-img.com/v1/tradingview/advanced-chart/storage?symbol=CME_MINI:NQ1!&layout={chart_id}&height=600&width=1000"

    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": side_color,
        "description": f"**Current Status:** {status_title}\n{status_desc}",
        "fields": [
            {"name": intel_header, "value": f"```\n{intel_field}\n```", "inline": False},
            {"name": "🗞️ Market Briefing", "value": intelligence if intelligence else "Awaiting fresh data.", "inline": False}
        ],
        "image": {"url": chart_url},
        "footer": {"text": "Underground Wall Street | Systematic Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
