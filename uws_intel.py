import os
import math
import yfinance as yf
import pandas as pd
import requests
from lightweight_charts import Chart
from datetime import datetime
import sys

def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_data_and_levels(ticker, lookback=500):
    print(f"Fetching data for {ticker}...")
    df = yf.download(ticker, period="2d", interval="5m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    
    df = df.reset_index().rename(columns={'Datetime': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'})
    window = df.tail(lookback)
    sess_o = window.iloc[0]['open']
    
    aH = (window['high'] - sess_o).tolist()
    aL = (sess_o - window['low']).tolist()
    
    levels = {
        "P50": (sess_o + percentile_nearest_rank(aH, 50), sess_o - percentile_nearest_rank(aL, 50)),
        "P75": (sess_o + percentile_nearest_rank(aH, 75), sess_o - percentile_nearest_rank(aL, 75)),
        "P90": (sess_o + percentile_nearest_rank(aH, 90), sess_o - percentile_nearest_rank(aL, 90))
    }
    return df, levels, sess_o

def generate_chart(df, levels, sess_o, name):
    print(f"Generating chart for {name}...")
    # Headless mode for GitHub Actions
    chart = Chart(width=1200, height=800) 
    chart.layout(background_color='#0c0d10', text_color='#FFFFFF', font_size=12)
    
    chart.set(df)
    
    # Levels
    chart.horizontal_line(sess_o, color='#ff0000', width=2, text="ANCHOR")
    for p_name, (h, l) in levels.items():
        chart.horizontal_line(h, color='#ffffff', width=1, text=f"{p_name} H")
        chart.horizontal_line(l, color='#008fff', width=1, text=f"{p_name} L")
    
    filename = f"{name.lower()}_chart.png"
    
    # Force render and save
    chart.show() 
    img_data = chart.screenshot()
    if img_data:
        with open(filename, 'wb') as f:
            f.write(img_data)
        print(f"Saved: {filename}")
    
    chart.exit()
    return filename

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    assets = [{"symbol": "NQ=F", "name": "Nasdaq"}, {"symbol": "GC=F", "name": "Gold"}]
    
    for asset in assets:
        try:
            df, levels, sess_o = get_data_and_levels(asset["symbol"])
            if df is not None:
                fname = generate_chart(df, levels, sess_o, asset["name"])
                
                with open(fname, 'rb') as f:
                    requests.post(webhook, files={'file': f}, data={'content': f"🏛️ **UWS INTEL: {asset['name']}**\nAnchor: {round(sess_o, 2)}"})
                print(f"Sent {asset['name']} to Discord.")
        except Exception as e:
            print(f"Error on {asset['name']}: {e}")
    
    print("Process complete. Exiting.")
    sys.exit(0) # Force GitHub Action to finish

if __name__ == "__main__":
    main()
