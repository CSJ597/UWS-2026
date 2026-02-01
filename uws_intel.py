import requests
import os
import math
import yfinance as yf
import pandas as pd
from datetime import datetime, time

# --- PINE SCRIPT RECREATION LOGIC ---
PERCENTILES = [50, 75, 90]
COLORS = {"Upper": "#ffffff", "Lower": "#008fff", "Mid": "#ff0000"}

def percentile_nearest_rank(arr, percentile):
    """Replicates Pine Script's array.percentile_nearest_rank exactly."""
    if not arr: return 0
    arr_sorted = sorted(arr)
    # Formula: index = ceil(P / 100 * n) - 1
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_session_intel(ticker_symbol):
    """Fetches real 8:30 AM open and historical session multipliers."""
    ticker = yf.Ticker(ticker_symbol)
    # Pull 60 days of 1-hour data
    df = ticker.history(period="60d", interval="1h")
    
    aH, aL = [], []
    # Identify historical moves from 8:30 open to session high/low
    for date, day_data in df.groupby(df.index.date):
        if len(day_data) >= 3:
            sess_o = day_data.iloc[0]['Open']
            sess_h = day_data.iloc[0:3]['High'].max() # 8:30 - 11:30
            sess_l = day_data.iloc[0:3]['Low'].min()
            aH.append(sess_h - sess_o)
            aL.append(sess_o - sess_l)
            
    live_open = df.iloc[-1]['Open']
    return aH, aL, live_open

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    
    assets = [
        {"symbol": "NQ=F", "tv_symbol": "CME_MINI:NQ1!", "name": "Nasdaq"},
        {"symbol": "GC=F", "tv_symbol": "COMEX:GC1!", "name": "Gold"}
    ]
    
    embeds = []
    for asset in assets:
        try:
            aH, aL, sess_o = get_session_intel(asset["symbol"])
            
            # Recreate drawings
            drawings = [{"type": "hline", "price": sess_o, "text": "8:30 OPEN", "color": COLORS["Mid"]}]
            
            for p in PERCENTILES:
                h_level = sess_o + percentile_nearest_rank(aH, p)
                l_level = sess_o - percentile_nearest_rank(aL, p)
                drawings.append({"type": "hline", "price": h_level, "text": f"P{p} H", "color": COLORS["Upper"]})
                drawings.append({"type": "hline", "price": l_level, "text": f"P{p} L", "color": COLORS["Lower"]})

            # Fetch the chart from API
            payload = {
                "symbol": asset["tv_symbol"],
                "width": 800, "height": 600, "theme": "dark",
                "drawings": drawings
            }
            res = requests.post("https://api.chart-img.com/v2/tradingview/advanced-chart/storage",
                                json=payload, headers={"x-api-key": chart_key})
            
            if res.status_code == 200:
                embeds.append({
                    "title": f"🏛️ UWS INTEL: {asset['name']}",
                    "color": 0x2ecc71 if "NQ" in asset["name"] else 0xf1c40f,
                    "description": f"Session Open: **{round(sess_o, 2)}**\nCalculated 8:30-11:30 Percentiles.",
                    "image": {"url": res.json().get('url')},
                    "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
                })
        except Exception as e:
            print(f"Error processing {asset['name']}: {e}")

    if webhook and embeds:
        requests.post(webhook, json={"embeds": embeds})

if __name__ == "__main__":
    main()
