import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
from datetime import datetime

# --- 1. CORE MATH ---
def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

# --- 2. INTEL GATHERING ---
def get_market_briefing(api_key):
    if not api_key: return "• News feed currently offline."
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        data = requests.get(url, timeout=10).json()
        assets = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]}
        found = {asset: "• No specific intel found." for asset in assets}
        for item in data[:20]:
            for asset, keywords in assets.items():
                if any(k in item['headline'].lower() for k in keywords):
                    found[asset] = f"• **{asset}**: {item['headline'][:75]}..."
        return "\n".join(found.values())
    except: return "• Intel desk throttled."

def get_data_and_levels(ticker, lookback=500):
    df = yf.download(ticker, period="2d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open']
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    levels = [
        sess_o, 
        sess_o + percentile_nearest_rank(aH, 50), sess_o - percentile_nearest_rank(aL, 50),
        sess_o + percentile_nearest_rank(aH, 75), sess_o - percentile_nearest_rank(aL, 75),
        sess_o + percentile_nearest_rank(aH, 90), sess_o - percentile_nearest_rank(aL, 90)
    ]
    return window, levels, sess_o

# --- 3. MAIN EXECUTION ---
def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    finnhub_key = os.getenv("FINNHUB_KEY")
    
    briefing = get_market_briefing(finnhub_key)
    assets = [{"symbol": "NQ=F", "name": "Nasdaq"}, {"symbol": "GC=F", "name": "Gold"}]
    
    # Styles
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#222222', facecolor='#0c0d10')

    for asset in assets:
        df, levels, sess_o = get_data_and_levels(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}_uws.png"
            mpf.plot(df, type='candle', style=s, 
                     hlines=dict(hlines=levels, 
                                 colors=['#ff0000', '#ffffff', '#ffffff', '#008fff', '#008fff', '#ffff00', '#ffff00'], 
                                 linewidths=1.2, alpha=0.8),
                     savefig=fname, figscale=1.5, tight_layout=True)
            
            # THE EMBED
            embed = {
                "title": "🏛️ UNDERGROUND UPDATE",
                "description": "🟢 **CONDITIONS FAVORABLE**\nClear for Execution",
                "color": 0x2ecc71,
                "fields": [
                    {"name": "📅 Upcoming Economic Intelligence", "value": "No major releases today. Watch Asian Open."},
                    {"name": "🗞️ Market Briefing", "value": briefing}
                ],
                "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
            }
            
            with open(fname, 'rb') as f:
                requests.post(webhook, files={'file': f}, data={"payload_json": requests.utils.quote(str({"embeds": [embed]}))})

if __name__ == "__main__":
    main()
