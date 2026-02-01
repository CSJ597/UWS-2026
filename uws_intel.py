import requests
import os
from datetime import datetime, timezone

# ... [get_ticker_news and get_economic_calendar functions stay the same] ...

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    finnhub_key = os.getenv("FINNHUB_KEY")
    layout_id = "Hx0V1y9S" # Your layout with indicators
    
    today_news, upcoming_news = get_economic_calendar()
    headlines = get_ticker_news(finnhub_key)
    
    status, color = ("⚠️ **VOLATILITY ALERT**", 0xe74c3c) if today_news else ("🟢 **CONDITIONS FAVORABLE**", 0x2ecc71)
    sub = "Heightened Volatility Anticipated" if today_news else "Clear for Execution"
    title = "Upcoming Economic Intelligence" if not today_news else "Today's High Impact News"
    detail = "\n".join([f"-# {e}" for e in today_news]) if today_news else f"-# Next: {upcoming_news[0]['title']} ({upcoming_news[0]['date']} @ {upcoming_news[0]['time']})" if upcoming_news else "-# No releases."

    # --- THE INDICATOR FIX (Using Layout-Chart) ---
    image_url = ""
    if chart_key:
        # We switch back to 'layout-chart' because it respects your SAVED indicators
        api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{layout_id}"
        headers = {"x-api-key": chart_key}
        # MUST stay at 800x600 for the Free/Basic plan
        payload = {"width": 800, "height": 600, "theme": "dark"} 
        
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=25)
            # The API returns the direct image URL here
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
