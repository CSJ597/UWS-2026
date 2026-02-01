import requests
import os
from datetime import datetime, timezone

def get_ticker_news(api_key):
    """Fetches one focused article for Gold and Nasdaq only."""
    if not api_key: 
        return "⚠️ *FINNHUB_API_KEY mapping failed.*"
    
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Focused keywords for GC and NQ
        assets = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]}
        found = {asset: None for asset in assets}
        
        for item in data:
            headline = item['headline']
            for asset, keywords in assets.items():
                if any(k in headline.lower() for k in keywords) and found[asset] is None:
                    # Shorten to 45 chars for a tight Underground look
                    title = (headline[:42] + '...') if len(headline) > 45 else headline
                    found[asset] = f"• **{asset}**: [{title}]({item['url']})"
        
        brief = [found[a] for a in assets if found[a]]
        return "\n".join(brief) if brief else "• No specific asset intel found."
    except:
        return "⚠️ *Market intelligence feed temporarily throttled.*"

def get_economic_calendar():
    """Identifies Red Folders for the session."""
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        response = requests.get(url, timeout=15).json()
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%m-%d-%Y")
        
        today_events, future_events = [], []
        for e in response:
            if e.get('impact') == 'High' and e.get('country') == 'USD':
                # Correctly parse time for comparison
                dt = datetime.strptime(f"{e['date']} {e['time']}", "%m-%d-%Y %I:%M%p").replace(tzinfo=timezone.utc)
                if e['date'] == today_str:
                    today_events.append(f"🚩 {e['title']} at {e['time']}")
                elif dt > now:
                    future_events.append(e)
        return today_events, future_events
    except:
        return [], []

def main():
    # Environment Variables from GitHub Secrets
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    layout_id = "Hx0V1y9S" 
    
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_ticker_news(finnhub_key)
    
    # Status and Color Logic
    status, color = ("⚠️ **VOLATILITY ALERT**", 0xe74c3c) if today_news else ("🟢 **CONDITIONS FAVORABLE**", 0x2ecc71)
    status_sub = "Heightened Volatility Anticipated" if today_news else "Clear for Execution"
    
    # Dynamic News Branding
    intel_title = "Today's High Impact News" if today_news else "Upcoming Economic Intelligence"
    if today_news:
        intel_detail = "\n".join([f"-# {e}" for e in today_news])
    elif upcoming_news:
        next_e = upcoming_news[0]
        intel_detail = f"-# Next: {next_e['title']} ({next_e['date']} @ {next_e['time']})"
    else:
        intel_detail = "-# No major releases scheduled."

    # --- THE SAVED LAYOUT FIX ---
    image_url = ""
    if chart_key:
        # Layout-chart endpoint is required to see your indicators/panes
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {"x-api-key": chart_key}
        # Stay at 800x600 for Basic tier compliance
        payload = {"width": 800, "height": 600, "theme": "dark"}
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=25)
            image_url = res.json().get('url', "")
        except:
            pass

    embed = {
        "title": "🏛️ UNDERGROUND UPDATE",
        "color": color,
        "description": f"{status}\n{status_sub}\n\n**{intel_title}**\n{intel_detail}",
        "fields": [
            {"name": "🗞️ Market Briefing", "value": headlines, "inline": False}
        ],
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
