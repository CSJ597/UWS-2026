import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
from datetime import datetime
import pytz
import matplotlib.pyplot as plt

# --- 1. CORE LOGIC ---
def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def format_est_time():
    """Returns current time in 12-hour EST format."""
    est = pytz.timezone('US/Eastern')
    return datetime.now(est).strftime('%I:%M %p EST')

def get_data_and_levels(ticker, lookback=500):
    print(f"Fetching {ticker}...")
    df = yf.download(ticker, period="2d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    
    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open']
    
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    
    # Unified Level Map
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

# --- 2. MAIN EXECUTION ---
def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    
    # ORDERED: GC first, then NQ
    assets = [
        {"symbol": "GC=F", "name": "GC"},
        {"symbol": "NQ=F", "name": "NQ"}
    ]
    
    # Premium UWS Brand Colors
    mc = mpf.make_marketcolors(up='#00ffbb', down='#ff3366', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#1a1a1a', facecolor='#050505')

    current_est = format_est_time()

    for asset in assets:
        df, lvls, sess_o = get_data_and_levels(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}_uws.png"
            
            # Create Plot
            fig, axlist = mpf.plot(df, type='candle', style=s, 
                                   title=f"\nUWS INTEL: {asset['name']} | {current_est}",
                                   hlines=dict(hlines=list(lvls.values()), colors='#C0C0C0', linewidths=1.2, alpha=0.6),
                                   returnfig=True, figscale=1.6, tight_layout=True)
            
            # --- ADD LABELS MANUALLY TO THE AXIS ---
            # This places text labels on the right side for clear UWS branding
            ax = axlist[0]
            for label, price in lvls.items():
                ax.text(len(df) + 2, price, label, color='#C0C0C0', fontsize=8, va='center')

            fig.savefig(fname, facecolor=fig.get_facecolor())
            plt.close(fig)
            
            embed = {
                "title": f"🏛️ UNDERGROUND UPDATE: {asset['name']}",
                "description": f"🟢 **CONDITIONS FAVORABLE**\nClear for Execution\n\n**EST Time:** {current_est}",
                "color": 0xf1c40f if asset['name'] == "GC" else 0x2ecc71,
                "fields": [
                    {"name": "📊 Anchor Price", "value": f"`{round(sess_o, 2)}`", "inline": True},
                    {"name": "📅 Intelligence", "value": "No major releases. Follow the levels.", "inline": True},
                    {"name": "🗞️ Market Briefing", "value": "Follow the money, not fake gurus."}
                ],
                "footer": {"text": f"UWS Intel Desk | 1m Timeframe | {current_est}"}
            }
            
            with open(fname, 'rb') as f:
                payload = {"payload_json": requests.utils.quote(str({"embeds": [embed]}))}
                requests.post(webhook, files={'file': f}, data=payload)
            print(f"Sent {asset['name']} update.")

if __name__ == "__main__":
    main()
