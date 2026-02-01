import requests
import os
from datetime import datetime, timezone

def get_ticker_news(api_key):
    """Fetches one shortened article for GC (Gold), NQ (Nasdaq), and ES (S&P 500)."""
    if not api_key:
        return "⚠️ *System Error: FINNHUB_API_KEY mapping failed.*"
    
    # Mapping Finnhub categories/symbols for your specific assets
    # Note: Finnhub uses general market categories for futures-related news
    symbols = {"Gold": "GC=F", "Nasdaq": "NQ=F", "ES": "ES=F"}
    news_brief = []
    
    # Category 'general' is most reliable for broad index/commodity news
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # We search the general feed for relevant keywords to ensure one per asset
        assets = ["Gold", "Nasdaq", "S&P 500"]
        found_articles = {asset: None for asset in assets}
        
        for item in data:
            headline = item['headline']
            for asset in assets:
                if asset.lower() in headline.lower() and found_articles[asset] is None:
                    # Shorten title to 50 chars for the "Underground" look
                    short_title = (headline[:47] + '...') if len(headline) > 50 else headline
                    found_articles[asset] = f"• **{asset}**: [{short_title}]({item['url']})"
        
        # Collect results, use fallbacks if specific keyword not found in recent 50 articles
        for asset in assets:
            if found_articles[asset]:
                news_brief.append(found_articles[asset])
            else:
                news_brief.append(f"• **{asset}**: Awaiting specific {asset} intel...")
                
        return "\n".join(news_brief)
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
    finnhub_key = os.getenv("FINNHUB_KEY")
    layout_id = "Hx0V1y9S"
    
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_ticker_news(finnhub_key)
    
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
        # We use the layout-chart endpoint specifically for your Hx0V1y9S setup
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {"x-api-key": chart_key}
        payload = {"width": 1200, "height": 800, "theme": "dark"}
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=20)
            image_url = res.json().get('url', "")
        except: pass

    embed = {
        "title": "🏛️ UNDERGROUND UPDATE",
        "color": side_color,
        "description": f"{status_text}\n{status_sub}\n\n**{intel_title}**\n{intel_detail}",
        "fields": [{"name": "🗞️ Market Briefing", "value": headlines}],
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
