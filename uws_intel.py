import requests
import os
import math
import yfinance as yf
import pandas as pd

# --- THE MESSIAH MATH ---
def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_1m_intel(ticker_symbol, lookback=500):
    print(f"Fetching data for {ticker_symbol}...")
    # multi_level_index=False is critical for flattened columns
    df = yf.download(ticker_symbol, period="2d", interval="1m", multi_level_index=False, progress=False)
    
    if df.empty:
        print(f"FAILED: No data found for {ticker_symbol}")
        return None, None, None

    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open']
    
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    
    return aH, aL, sess_o

def make_hline(price, label, color):
    """Helper to build the exact JSON object the Chart-Img API needs for hlines."""
    return {
        "name": "horizontal_line",
        "input": {"price": price},
        "overrides": {
            "linecolor": color,
            "showLabel": True,
            "text": label,
            "textcolor": color,
            "fontsize": 10
        }
    }

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

        # --- CORRECT DRAWING FORMAT ---
        drawings = [make_hline(sess_o, "ANCHOR", "#ff0000")]
        for p in [50, 75, 90]:
            drawings.append(make_hline(sess_o + percentile_nearest_rank(aH, p), f"P{p} H", "#ffffff"))
            drawings.append(make_hline(sess_o - percentile_nearest_rank(aL, p), f"P{p} L", "#008fff"))

        # --- CORRECT API PAYLOAD ---
        payload = {
            "symbol": asset["tv_symbol"],
            "interval": "1m", # Fixed from "1" to "1m"
            "drawings": drawings,
            "theme": "dark",
            "width": 800,
            "height": 600
        }
        
        headers = {"x-api-key": chart_key}
        res = requests.post("https://api.chart-img.com/v2/tradingview/advanced-chart/storage",
                            json=payload, headers=headers, timeout=60)
        
        if res.status_code == 200:
            image_url = res.json().get('url', "")
            embeds.append({
                "title": f"🏛️ UWS 1M INTEL: {asset['name']}",
                "color": 0x2ecc71 if "NQ" in asset["name"] else 0xf1c40f,
                "description": f"Lookback: **500 bars (1m)**\nAnchor Open: **{round(sess_o, 2)}**",
                "image": {"url": image_url},
                "footer": {"text": "UWS Intel Desk | Follow the Money"}
            })
            print(f"Chart Success for {asset['name']}")
        else:
            print(f"Chart API Error {res.status_code}: {res.text}")

    if webhook and embeds:
        requests.post(webhook, json={"embeds": embeds})
        print("Update pushed to Discord.")

if __name__ == "__main__":
    main()
