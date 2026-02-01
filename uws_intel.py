import requests
import os
import math
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CALCULATE EXACTLY LIKE PINESCRIPT ---
def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    # Replicates TV: ceil(P/100 * n) - 1
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_1m_intel(ticker_symbol, lookback=500):
    """Fetches 1m data and fixes the Multi-Index issue."""
    # Pull 2 days to ensure we have enough 1m bars
    df = yf.download(ticker_symbol, period="2d", interval="1m", multi_level_index=False, progress=False)
    
    if df.empty:
        print(f"Error: No data found for {ticker_symbol}")
        return None, None, None

    # Get the last 500 bars
    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open'] # Anchor Open
    
    # Replicate aH and aL multipliers
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

        # Build Drawings
        drawings = [{"type": "hline", "price": sess_o, "text": "LOOKBACK OPEN", "color": "red"}]
        for p in [50, 75, 90]:
            drawings.append({"type": "hline", "price": sess_o + percentile_nearest_rank(aH, p), "text": f"P{p} H", "color": "white"})
            drawings.append({"type": "hline", "price": sess_o - percentile_nearest_rank(aL, p), "text": f"P{p} L", "color": "#008fff"})

        # Chart-Img API Request
        payload = {
            "symbol": asset["tv_symbol"],
            "interval": "1",
            "drawings": drawings,
            "theme": "dark"
        }
        res = requests.post("https://api.chart-img.com/v2/tradingview/advanced-chart/storage",
                            json=payload, headers={"x-api-key": chart_key})
        
        if res.status_code == 200:
            embeds.append({
                "title": f"🏛️ UWS 1M INTEL: {asset['name']}",
                "color": 0x2ecc71 if "Nasdaq" in asset["name"] else 0xf1c40f,
                "description": f"Lookback: **500 bars (1m)**\nAnchor: **{round(sess_o, 2)}**",
                "image": {"url": res.json().get('url')},
                "footer": {"text": "UWS Intel Desk | Follow the Money"}
            })

    if webhook and embeds:
        requests.post(webhook, json={"embeds": embeds})

if __name__ == "__main__":
    main()
