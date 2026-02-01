import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
from datetime import datetime
import pytz

# --- 1. CORE MATH & UTILS ---
def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def format_est_time(dt):
    """Converts UTC/Local time to 12-hour EST format."""
    est = pytz.timezone('US/Eastern')
    return dt.astimezone(est).strftime('%I:%M %p EST')

# --- 2. DATA & LEVELS ---
def get_data_and_levels(ticker, lookback=500):
    print(f"Fetching {ticker}...")
    df = yf.download(ticker, period="2d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    
    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open']
    
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    
    # Levels dictionary for easy labeling
    lvls = {
        "ANCHOR": sess_o,
        "P50 H": sess_o + percentile_nearest_rank(aH, 50),
        "P50 L": sess_o - percentile_nearest_rank(aL, 50),
        "P75 H": sess_o + percentile_nearest_rank(aH, 75),
        "P75 L": sess_o - percentile_nearest_rank(aL, 75),
        "P90 H": sess_o + percentile_nearest_rank(aH, 90),
        "P90 L": sess_o - percentile_nearest_rank(aL, 90)
    }
    return window, lvls, sess_o

# --- 3. MAIN EXECUTION ---
def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    finnhub_key = os.getenv("FINNHUB_KEY")
    
    # Reordered: GC first, then NQ
    assets = [
        {"symbol": "GC=F", "tv_symbol": "COMEX:GC1!", "name": "GC"},
        {"symbol": "NQ=F", "tv_symbol": "CME_MINI:NQ1!", "name": "NQ"}
    ]
    
    # Custom UWS Styling
    mc = mpf.make_marketcolors(up='#00ffbb', down='#ff3366', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#1a1a1a', facecolor='#050505')

    for asset in assets:
        df, lvls, sess_o = get_data_and_levels(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}_uws.png"
            current_time_est = format_est_time(datetime.now(pytz.utc))
            
            # Prepare hlines with uniform color
            h_vals = list(lvls.values())
            
            

            mpf.plot(df, type='candle', style=s, 
                     title=f"\nUWS INTEL: {asset['name']} | {current_time_est}",
                     hlines=dict(hlines=h_vals, colors='#C0C0C0', linewidths=0.8, alpha=0.5),
                     savefig=fname, figscale=1.6, tight_layout=True)
            
            embed = {
                "title": f"🏛️ UNDERGROUND UPDATE: {asset['name']}",
                "description": f"🟢 **CONDITIONS FAVORABLE**\nClear for Execution\n\n**8:30 AM Anchor:** {round(sess_o, 2)}",
                "color": 0x00ffbb if asset['name'] == "NQ" else 0xffd700,
                "fields": [
                    {"name": "📅 Intelligence", "value": "No major releases. Watch session extremes."},
                    {"name": "🗞️ Market Briefing", "value": "Follow the money, not fake gurus."}
                ],
                "footer": {"text": f"UWS Intel Desk | {current_time_est}"}
            }
            
            with open(fname, 'rb') as f:
                payload = {"payload_json": requests.utils.quote(str({"embeds": [embed]}))}
                requests.post(webhook, files={'file': f}, data=payload)
            print(f"Sent {asset['name']} update.")

if __name__ == "__main__":
    main()
