import requests
import os
from bs4 import BeautifulSoup

def get_red_folders():
    try:
        url = "https://www.forexfactory.com/calendar.php"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        events = [row.select_one('.calendar__event').text.strip() 
                  for row in soup.select('.calendar__row') 
                  if row.select_one('.calendar__impact span') and 
                  'high' in row.select_one('.calendar__impact span').get('class', []) and 
                  'USD' in row.select_one('.calendar__currency').text]
        return list(set(events))
    except: return []

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    api_key = os.getenv("CHART_IMG_KEY")
    chart_id = "Hx0V1y9S" # Your TV Layout ID
    
    news = get_red_folders()
    news_msg = "\n".join([f"🚩 **{n}**" for n in news]) if news else "✅ No High Impact News Today"
    
    # We use the 'Storage' endpoint to get a URL Discord can render
    api_url = f"https://api.chart-img.com/v2/tradingview/advanced-chart/storage"
    payload = {
        "symbol": "CME_MINI:NQ1!",
        "layout": chart_id,
        "height": 600,
        "width": 1000,
        "theme": "dark"
    }
    headers = {"x-api-key": api_key}
    
    response = requests.post(api_url, json=payload, headers=headers)
    image_url = response.json().get('url', "")

    embed = {
        "title": "🏛️ UWS INSTITUTIONAL TERMINAL: NASDAQ",
        "color": 0x2f3136,
        "description": f"**Economic Intel:**\n{news_msg}",
        "image": {"url": image_url},
        "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
    }
    
    requests.post(webhook, json={"embeds": [embed]})

if __name__ == "__main__":
    main()