import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import json
from datetime import datetime, time, timedelta
import pytz
import matplotlib.pyplot as plt

# --- 1. CORE LOGIC ---
def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def format_est_time():
    est = pytz.timezone('US/Eastern')
    return datetime.now(est).strftime('%I:%M %p EST')

# --- 2. INTEL GATHERING ---
def get_economic_intel(api_key):
    """Checks for 'Red Folders' (High Impact USD events)."""
    if not api_key: return "No major USD releases today. Watch session extremes.", 0x2ecc71
    
    today = datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/calendar/economic?token={api_key}"
    
    try:
        response = requests.get(url, timeout=10).json()
        calendar = response.get('economicCalendar', [])
        
        red_folders = []
        for event in calendar:
            # Check for today, USD, and High Impact (3)
            if event.get('date', '').split(' ')[0] == today and event.get('country') == 'US' and event.get('impact') == 3:
                red_folders.append(f"🚩 **{event.get('event')}** ({event.get('time')})")
        
        if red_folders:
            # Return events and the RED color (0xe74c3c)
            return "\n".join(red_folders), 0xe74c3c
        else:
            return "No News", 0x2ecc71
    except:
        return "No major USD releases today. Watch session extremes.", 0x2ecc71

def get_finnhub_news(api_key, assets):
    """Fetches exactly one fresh article per instrument with clickable links."""
    if not api_key: return "• News feed offline."
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    
    try:
        data = requests.get(url, timeout=10).json()
        found = {}
        for item in data[:50]:
            headline = item['headline']
            link = item['url']
            for asset_name, keywords in assets.items():
                if asset_name not in found and any(k in headline.lower() for k in keywords):
                    found[asset_name] = f"• **{asset_name}**: [{headline[:75]}...]({link})"
        
        return "\n".join(found.values()) if found else "No News"
    except:
        return "No News"

# --- 3. DATA & LEVELS ---
def get_precision_data(ticker):
    df = yf.download(ticker, period="5d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    df.index = df.index.tz_convert('US/Eastern')
    
    session_start = datetime.combine(df.index[-1].date(), time(8, 30)).replace(tzinfo=pytz.timezone('US/Eastern'))
    window = df[df.index >= session_start]
    if window.empty: window = df.tail(500)
        
    sess_o = window.iloc[0]['Open']
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    
    lvls = {
        "ANCHOR": sess_o,
        "P50 H": sess_o + percentile_nearest_rank(aH, 50), "P50 L": sess_o - percentile_nearest_rank(aL, 50),
        "P75 H": sess_o + percentile_nearest_rank(aH, 75), "P75 L": sess_o - percentile_nearest_rank(aL, 75),
        "P90 H": sess_o + percentile_nearest_rank(aH, 90), "P90 L": sess_o - percentile_nearest_rank(aL, 90)
    }
    return window, lvls, sess_o

# --- 4. MAIN EXECUTION ---
def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    finnhub_key = os.getenv("FINNHUB_KEY")
    current_est = format_est_time()
    
    news_keywords = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]}
    briefing = get_finnhub_news(finnhub_key, news_keywords)
    eco_intel, embed_color = get_economic_intel(finnhub_key)
    
    assets = [
        {"symbol": "GC=F", "name": "GC", "color": 0xf1c40f},
        {"symbol": "NQ=F", "name": "NQ", "color": 0x2ecc71}
    ]
    
    mc = mpf.make_marketcolors(up='#00ffbb', down='#ff3366', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#1a1a1a', facecolor='#050505')

    files, embeds = {}, [{
        "title": "🏛️ UNDERGROUND UPDATE",
        "description": "🟢 **CONDITIONS FAVORABLE**\nClear for Execution",
        "color": embed_color,
        "fields": [
            {"name": "📅 Upcoming Economic Intelligence", "value": eco_intel},
            {"name": "🗞️ Market Briefing", "value": briefing}
        ],
        "footer": {"text": f"Follow the money, not fake gurus. | {current_est}"}
    }]

    for i, asset in enumerate(assets):
        df, lvls, sess_o = get_precision_data(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}.png"
            fig, axlist = mpf.plot(df, type='candle', style=s, 
                                   title=f"\nUWS {asset['name']} | {df.index[0].strftime('%b %d, %Y')}",
                                   datetime_format='%I:%M %p',
                                   hlines=dict(hlines=list(lvls.values()), colors='#C0C0C0', linewidths=1.2, alpha=0.5),
                                   returnfig=True, figscale=1.8, tight_layout=True)
            ax = axlist[0]
            for label, price in lvls.items():
                ax.text(len(df) + 1, price, f"{round(price, 2)} - {label}", color='#C0C0C0', fontsize=8, fontweight='bold', va='center')

            fig.savefig(fname, facecolor=fig.get_facecolor())
            plt.close(fig)
            files[f"file{i}"] = (fname, open(fname, 'rb'), 'image/png')
            embeds.append({
                "title": f"📈 {asset['name']} ANALYSIS",
                "color": asset["color"],
                "image": {"url": f"attachment://{fname}"},
                "footer": {"text": f"8:30 AM Anchor: {round(sess_o, 2)}"}
            })

    if webhook:
        payload = {"payload_json": json.dumps({"embeds": embeds})}
        requests.post(webhook, files=files, data=payload)
        for _, ftup in files.items(): ftup[1].close()

if __name__ == "__main__":
    main()
