import requests
import os
import math
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CALCULATE LIKE THE MESSIAH ---
def percentile_nearest_rank(arr, percentile):
    """Replicates Pine Script's array.percentile_nearest_rank exactly."""
    if len(arr) == 0: return 0
    arr_sorted = sorted(arr)
    # Formula: index = ceil(P / 100 * n) - 1
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def get_1m_levels(ticker_symbol, lookback=500):
    """Fetches 1m data and calculates multipliers based on the 500-period lookback."""
    ticker = yf.Ticker(ticker_symbol)
    # yfinance allows 1m data for up to 7 days. '5d' is safe.
    df = ticker.history(period="5d", interval="1m")
    
    if len(df) < lookback:
        lookback = len(df)
        
    # Get the most recent 500-bar window
    window = df.tail(lookback)
    sess_open = window.iloc[0]['Open'] # The 'Open' at the start of the 500 bars
    
    # Calculate multipliers (High - Open) and (Open - Low) for the window
    aH = (window['High'] - sess_open).tolist()
    aL = (sess_open - window['Low']).tolist()
    
    current_price = window.iloc[-1]['Close']
    return aH, aL, sess_open, current_price

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    chart_key = os.getenv("CHART_IMG_KEY")
    
    assets = [
        {"symbol": "NQ=F", "tv_symbol": "CME_MINI:NQ1!", "name": "Nasdaq"},
        {"symbol": "GC=F", "tv_symbol": "COMEX:GC1!", "name": "Gold"}
    ]
    
    embeds = []
    for asset in assets:
        aH, aL, sess_o, live_p = get_1m_levels(asset["symbol"])
        
        # Calculate P50, P75, P90 levels for the 1m 500-lookback
        drawings = [{"type": "hline", "price": sess_o, "text": "LOOKBACK OPEN", "color": "red"}]
        for p in [50, 75, 90]:
            h_level = sess_o + percentile_nearest_rank(aH, p)
            l_level = sess_o - percentile_nearest_rank(aL, p)
            drawings.append({"type": "hline", "price": h_level, "text": f"P{p} H", "color": "white"})
            drawings.append({"type": "hline", "price": l_level, "text": f"P{p} L", "color": "#008fff"})

        # Advanced Chart Request (1m interval)
        payload = {
            "symbol": asset["tv_symbol"],
            "interval": "1", # 1-minute timeframe
            "drawings": drawings,
            "theme": "dark"
        }
        res = requests.post("https://api.chart-img.com/v2/tradingview/advanced-chart/storage",
                            json=payload, headers={"x-api-key": chart_key})
        
        if res.status_code == 200:
            embeds.append({
                "title": f"🏛️ UWS 1M INTEL: {asset['name']}",
                "color": 0x2ecc71 if "Nasdaq" in asset["name"] else 0xf1c40f,
                "description": f"Current Price: **{round(live_p, 2)}**\nLookback: **500 bars (1m)**",
                "image": {"url": res.json().get('url')},
                "footer": {"text": "Follow the money, not fake gurus. | UWS Intel Desk"}
            })

    if webhook:
        requests.post(webhook, json={"embeds": embeds})

if __name__ == "__main__":
    main()
