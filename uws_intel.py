import requests
import os
import math
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- PINE SCRIPT MATH REPLICATION ---
def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    # Replicates TV: ceil(P/100 * n) - 1
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_1m_intel(ticker_symbol, lookback=500):
    print(f"Fetching data for {ticker_symbol}...")
    # FIX: multi_level_index=False flattens the data so 'Open', 'High' etc. work
    df = yf.download(ticker_symbol, period="2d", interval="1m", multi_level_index=False, progress=False)
    
    if df.empty:
        print(f"FAILED: No data found for {ticker_symbol}")
        return None, None, None

    # Get the last 500 minutes
    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open']
    
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    
    return aH, aL, sess_o

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    
    assets = [
        {"symbol": "NQ=F", "tv_symbol": "CME_MINI:NQ1!", "name": "Nasdaq"},
        {"symbol": "GC=F", "tv_symbol": "COMEX:GC1!", "name": "Gold"}
    ]
    
    embeds = []
    for asset in assets:
        aH, aL, sess_o = get_1m_intel(asset["symbol"])
        if sess_o is None: continue

        # Calculate Levels
        drawings = [{"type": "hline", "price": sess_o, "text": "ANCHOR", "color": "red"}]
        for p in [50, 75, 90]:
            drawings.append({"type": "hline", "price": sess_o + percentile_nearest_rank(aH, p), "text": f"P{p} H", "color": "white"})
            drawings.append({"type": "hline", "price": sess_o - percentile_nearest_rank(aL, p), "text": f"P{p} L", "color": "#008fff"})

        # Request Chart
        payload = {"symbol": asset["tv_symbol"], "interval": "1", "drawings": drawings, "theme": "dark"}
        res = requests.post("https://api.chart-img.com/v2/tradingview/advanced-chart/storage",
                            json=payload, headers={"x-api-key": chart_key})
        
        if res.status_code == 200:
            embeds.append({
                "title": f"🏛️ UWS 1M INTEL: {asset['name']}",
                "color": 0x2ecc71 if "NQ" in asset["name"] else 0xf1c40f,
                "description": f"Lookback: **500 bars (1m)**\nAnchor Open: **{round(sess_o, 2)}**",
                "image": {"url": res.json().get('url')},
                "footer": {"text": "UWS Intel Desk | Follow the Money"}
            })
            print(f"Chart generated for {asset['name']}")
        else:
            print(f"Chart-Img Error {res.status_code}: {res.text}")

    if webhook and embeds:
        final_res = requests.post(webhook, json={"embeds": embeds})
        print(f"Discord Response: {final_res.status_code}")

if __name__ == "__main__":
    main()
