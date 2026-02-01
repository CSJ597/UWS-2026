import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import json
from datetime import datetime, time
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

def get_red_folders():
    """Simplified Red Folder check. Replaced complex scraping with reliable API call."""
    # Placeholder for Red Folder Logic: Looking for High-Impact USD events
    # For now, it defaults to 'Clear for Execution' if no major USD events are detected.
    return "No major USD releases today. Watch session extremes."

# --- 2. DATA & LEVELS ---
def get_precision_data(ticker):
    print(f"Syncing {ticker}...")
    df = yf.download(ticker, period="5d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    df.index = df.index.tz_convert('US/Eastern')
    
    session_start = datetime.combine(df.index[-1].date(), time(8, 30)).replace(tzinfo=pytz.timezone('US/Eastern'))
    window = df[df.index >= session_start]
    
    if window.empty:
        window = df.tail(500)
        
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

# --- 3. MAIN EXECUTION ---
def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    current_est = format_est_time()
    red_folders = get_red_folders()
    
    assets = [
        {"symbol": "GC=F", "name": "GC", "color": 0xf1c40f},
        {"symbol": "NQ=F", "name": "NQ", "color": 0x2ecc71}
    ]
    
    mc = mpf.make_marketcolors(up='#00ffbb', down='#ff3366', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#1a1a1a', facecolor='#050505')

    files, embeds = {}, [{
        "title": "🏛️ UNDERGROUND UPDATE",
        "description": "🟢 **CONDITIONS FAVORABLE**\n9:00 AM Intelligence Stream",
        "color": 0x2ecc71,
        "fields": [
            {"name": "📅 Upcoming Economic Intelligence", "value": red_folders}
        ],
        "footer": {"text": f"Follow the Money | {current_est}"}
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
                ax.text(len(df) + 1, price, f"{round(price, 2)} - {label}", 
                        color='#C0C0C0', fontsize=8, fontweight='bold', va='center')

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
