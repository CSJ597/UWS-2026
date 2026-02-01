import os
import math
import yfinance as yf
import pandas as pd
import requests
from lightweight_charts import Chart
from datetime import datetime

def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_data_and_levels(ticker, lookback=500):
    df = yf.download(ticker, period="2d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    
    # Format for lightweight-charts: time | open | high | low | close
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
    chart = Chart(width=800, height=600, inner_width=1, inner_height=1)
    chart.layout(background_color='#0c0d10', text_color='#FFFFFF', font_size=12)
    chart.candle_style(up_color='#26a69a', down_color='#ef5350', border_up_color='#26a69a', border_down_color='#ef5350')
    
    chart.set(df)
    
    # Draw Anchor and Percentile Levels
    chart.horizontal_line(sess_o, color='#ff0000', width=2, text="ANCHOR")
    for p_name, (h, l) in levels.items():
        chart.horizontal_line(h, color='#ffffff', width=1, text=f"{p_name} H")
        chart.horizontal_line(l, color='#008fff', width=1, text=f"{p_name} L")
    
    chart.watermark(name, color='rgba(255, 255, 255, 0.1)')
    
    filename = f"{name.lower()}_chart.png"
    # Take screenshot and save
    img_data = chart.screenshot()
    with open(filename, 'wb') as f:
        f.write(img_data)
    chart.exit()
    return filename

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    assets = [{"symbol": "NQ=F", "name": "Nasdaq"}, {"symbol": "GC=F", "name": "Gold"}]
    
    for asset in assets:
        df, levels, sess_o = get_data_and_levels(asset["symbol"])
        if df is not None:
            fname = generate_chart(df, levels, sess_o, asset["name"])
            
            # Send file to Discord
            with open(fname, 'rb') as f:
                requests.post(webhook, files={'file': f}, data={'content': f"🏛️ **UWS 1M INTEL: {asset['name']}**\nAnchor: {round(sess_o, 2)}"})

if __name__ == "__main__":
    main()
