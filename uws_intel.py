import requests
import os
from datetime import datetime, timezone

def get_market_news(finnhub_key):
    """Fetches high-impact news from Finnhub."""
    if not finnhub_key or finnhub_key == "":
        return "⚠️ *FINNHUB_KEY is missing in GitHub Secrets.*"
    
    url = f"https://finnhub.io/api/v1/news?category=general&token={finnhub_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return "\n".join([f"• [{n['headline']}]({n['url']})" for n in data[:3]])
        else:
            return "⚠️ *No fresh headlines found in the last hour.*"
    except Exception as e:
        return f"⚠️ *News Feed Error: {str(e)}*"

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
                # Parse time
                event_dt = datetime.strptime(f"{event_date} {event_time}", "%m-%d-%Y %I:%M%p").replace(tzinfo=timezone.utc)

                if event_date == today_str:
                    today_events.append(f"🚩 {event['title']} at {event_time}")
                elif event_dt > now:
                    future_events.append(event)
        return today_events, future_events
    except: return [], []

def main():
    # Fetch all secrets
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    chart_id = "Hx0V1y9S"
    
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_market_news(finnhub_key)
    
    # Status Logic
    if today_news:
        status_text, side_color = "⚠️ **VOLATILITY ALERT**", 0xe74c3c
        intel_detail = "\n".join([f"-# {e}" for e in today_news])
    else:
        status_text, side_color = "🟢 **CONDITIONS FAVORABLE**", 0x2ecc71
        next_e = upcoming_news[0] if upcoming_news else None
        intel_detail = f"-# Next Event: {next_e['title']} ({next_e['date']} @ {next_e['time']})" if next_e else "-# No major releases."

    # --- THE CHART FIX ---
    image_url = ""
    if chart_key:
        # We use the 'layout-chart' endpoint which is more reliable for custom IDs
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{chart_id}"
        headers = {"x-api-key": chart_key}
        params = {"width": 1000, "height": 600, "theme": "dark"}
        try:
            res = requests.post(api_url, json=params, headers=headers, timeout=20)
            image_url = res.json().get('url', "")
        except: pass

    # Build Embed
    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": side_color,
        "description": f"{status_text}\n-# Clear for Execution\n\n**Economic Intel**\n{intel_detail}",
        "fields": [
            {"name": "🗞️ Market Briefing", "value": headlines, "inline": False}
        ],
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
