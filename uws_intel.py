import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests

def percentile_nearest_rank(arr, percentile):
    """Replicates Pine Script's array.percentile_nearest_rank exactly."""
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_data_and_levels(ticker, lookback=500):
    print(f"Fetching {ticker} data...")
    # Pulling 2 days of 1m data to ensure a full 500-bar window
    df = yf.download(ticker, period="2d", interval="1m", multi_level_index=False, progress=False)
    
    if df.empty:
        print(f"Error: No data for {ticker}")
        return None, None, None
    
    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open']
    
    # Calculate multipliers for historical session movement
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    
    # Organize levels for the hlines plot
    levels = [
        sess_o, # Anchor (Index 0)
        sess_o + percentile_nearest_rank(aH, 50), sess_o - percentile_nearest_rank(aL, 50), # P50 (Indices 1, 2)
        sess_o + percentile_nearest_rank(aH, 75), sess_o - percentile_nearest_rank(aL, 75), # P75 (Indices 3, 4)
        sess_o + percentile_nearest_rank(aH, 90), sess_o - percentile_nearest_rank(aL, 90)  # P90 (Indices 5, 6)
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
    
    # Custom UWS Brand Styling
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#222222', facecolor='#0c0d10')

    for asset in assets:
        df, levels, sess_o = get_data_and_levels(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}_uws.png"
            
            # Plot the chart with your percentile levels
            mpf.plot(df, type='candle', style=s, 
                     title=f"\nUWS INTEL: {asset['name']} (1m)",
                     hlines=dict(hlines=levels, 
                                 colors=['red', 'white', 'white', '#008fff', '#008fff', 'yellow', 'yellow'], 
                                 linewidths=1, alpha=0.7),
                     savefig=fname, width_config=dict(candle_linewidth=0.8),
                     tight_layout=True)
            
            # Upload the actual file to Discord
            with open(fname, 'rb') as f:
                payload = {"content": f"🏛️ **UWS 1M INTEL: {asset['name']}**\nLookback: 500 bars | Anchor: {round(sess_o, 2)}"}
                requests.post(webhook, files={'file': f}, data=payload)
            print(f"Successfully sent {asset['name']} update.")

if __name__ == "__main__":
    main()
