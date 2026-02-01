import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests

def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_data_and_levels(ticker, lookback=500):
    print(f"Fetching {ticker} data...")
    # multi_level_index=False is vital for the 2026 yfinance update
    df = yf.download(ticker, period="2d", interval="1m", multi_level_index=False, progress=False)
    
    if df.empty:
        print(f"Error: No data for {ticker}")
        return None, None, None
    
    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open']
    
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    
    # Organize exactly 7 levels
    levels = [
        sess_o, # Anchor (Red)
        sess_o + percentile_nearest_rank(aH, 50), sess_o - percentile_nearest_rank(aL, 50), # P50 (White)
        sess_o + percentile_nearest_rank(aH, 75), sess_o - percentile_nearest_rank(aL, 75), # P75 (Blue)
        sess_o + percentile_nearest_rank(aH, 90), sess_o - percentile_nearest_rank(aL, 90)  # P90 (Yellow)
    ]
    return window, levels, sess_o

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        print("Error: DISCORD_WEBHOOK_URL not set.")
        return

    assets = [
        {"symbol": "NQ=F", "name": "Nasdaq"}, 
        {"symbol": "GC=F", "name": "Gold"}
    ]
    
    # Brand Styling
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#222222', facecolor='#0c0d10')

    for asset in assets:
        df, levels, sess_o = get_data_and_levels(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}_uws.png"
            
            # Replaced width_config with figscale for better resolution
            mpf.plot(df, type='candle', style=s, 
                     title=f"\nUWS INTEL: {asset['name']} (1m)",
                     hlines=dict(hlines=levels, 
                                 colors=['#ff0000', '#ffffff', '#ffffff', '#008fff', '#008fff', '#ffff00', '#ffff00'], 
                                 linewidths=1.5, alpha=0.8),
                     savefig=fname, 
                     figscale=1.5,
                     tight_layout=True)
            
            with open(fname, 'rb') as f:
                payload = {"content": f"🏛️ **UWS 1M INTEL: {asset['name']}**\nLookback: 500 bars | Anchor: {round(sess_o, 2)}"}
                requests.post(webhook, files={'file': f}, data=payload)
            print(f"Successfully sent {asset['name']} update.")

if __name__ == "__main__":
    main()
