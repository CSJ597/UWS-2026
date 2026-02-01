import requests
import os
from datetime import datetime, timezone

def get_ticker_news(api_key):
    """Fetches one shortened article for Gold, Nasdaq, and ES."""
    if not api_key:
        return "⚠️ *System Error: FINNHUB_API_KEY mapping failed.*"
    
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Mapping assets to search keywords
        assets = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"], "ES": ["s&p 500", "sp500", "market"]}
        found = {asset: None for asset in assets}
        
        for item in data:
            headline = item['headline']
            for asset, keywords in assets.items():
                if any(k in headline.lower() for k in keywords) and found[asset] is None:
                    # Shorten to 50 characters for the Underground look
                    title = (headline[:47] + '...') if len(headline) > 50 else headline
                    found[asset] = f"• **{asset}**: [{title}]({item['url']})"
        
        brief = [found[a] for a in assets if found[a]]
        return "\n".join(brief) if brief else "• No specific asset intel found."
    except:
        return "⚠️ *Market intelligence feed temporarily throttled.*"

def get_economic_calendar():
    """Identifies Today's Red Folders vs the next Upcoming Event."""
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        response = requests.get(url, timeout=15).json()
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%m-%d-%Y")
        
        today_events, future_events = [], []
        for e in response:
            if e.get('impact') == 'High' and e.get('country') == 'USD':
                # Parse event time for comparison
                dt = datetime.strptime(f"{e['date']} {e['time']}", "%m-%d-%Y %I:%M%p").replace(tzinfo=timezone.utc)
                if e['date'] == today_str:
                    today_events.append(f"🚩 {e['title']} at {e['time']}")
                elif dt > now:
                    future_events.append(e)
        return today_events, future_events
    except:
        return [], []

def main():
    """The Terminal Engine: Builds the Discord Embed and Captures the Chart."""
    # Environment Secret Mapping
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    layout_id = "Hx0V1y9S"
    
    # 1. Gather Intelligence
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_ticker_news(finnhub_key)
    
    # 2. Logic for Status and Sidebar
    if today_news:
        status_text, side_color = "⚠️ **VOLATILITY ALERT**", 0xe74c3c # Red
        status_sub = "Heightened Volatility Anticipated"
        intel_title = "Today's High Impact News"
        intel_detail = "\n".join([f"-# {e}" for e in today_news])
    else:
        status_text, side_color = "🟢 **CONDITIONS FAVORABLE**", 0x2ecc71 # Green
        status_sub = "Clear for Execution"
        intel_title = "Upcoming Economic Intelligence"
        if upcoming_news:
            next_e = upcoming_news[0]
            intel_detail = f"-# Next: {next_e['title']} ({next_e['date']} @ {next_e['time']})"
        else:
            intel_detail = "-# No major releases scheduled."

    # 3. Chart-Img Logic (Fixed for 800x600 Layout-Chart)
    image_url = ""
    if chart_key:
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {"x-api-key": chart_key}
        payload = {"width": 800, "height": 600, "theme": "dark"}
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=25)
            image_url = res.json().get('url', "")
        except:
            pass

    # 4. Construct and Send the Embed
    embed = {
        "title": "🏛️ UNDERGROUND UPDATE",
        "color": side_color,
        "description": f"{status_text}\n{status_sub}\n\n**{intel_title}**\n{intel_detail}",
        "fields": [
            {"name": "🗞️ Market Briefing", "value": headlines, "inline": False}
        ],
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

# This line ensures the script runs the main logic when called
if __name__ == "__main__":
    main()
