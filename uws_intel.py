import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import json
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
    est = pytz.timezone('US/Eastern')
    return datetime.now(est).strftime('%I:%M %p EST')

def get_market_briefing(api_key):
    if not api_key: return "• News feed offline (Check Secret)."
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        data = requests.get(url, timeout=10).json()
        assets = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]}
        found = {asset: "• No major headlines found." for asset in assets}
        for item in data[:30]:
            headline = item['headline']
            for asset, keywords in assets.items():
                if any(k in headline.lower() for k in keywords) and found[asset] == "• No major headlines found.":
                    found[asset] = f"• **{asset}**: {headline[:85]}..."
        return "\n".join(found.values())
    except: return "• Market Briefing throttled."

def get_data_and_levels(ticker, lookback=500):
    df = yf.download(ticker, period="2d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    window = df.tail(lookback)
    sess_o = window.iloc[0]['Open']
    aH = (window['High'] - sess_o).tolist()
    aL = (sess_o - window['Low']).tolist()
    lvls = {
        "ANCHOR": sess_o,
        "P50 H": sess_o + percentile_nearest_rank(aH, 50), "P50 L": sess_o - percentile_nearest_rank(aL, 50),
        "P75 H": sess_o + percentile_nearest_rank(aH, 75), "P75 L": sess_o - percentile_nearest_rank(aL, 75),
        "P90 H": sess_o + percentile_nearest_rank(aH, 90), "P90 L": sess_o - percentile_nearest_rank(aL, 90)
    }
    return window, lvls, sess_o

# --- 2. MAIN EXECUTION ---
def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    finnhub_key = os.getenv("FINNHUB_KEY")
    current_est = format_est_time()
    briefing = get_market_briefing(finnhub_key)
    
    assets = [
        {"symbol": "GC=F", "name": "GC", "color": 0xf1c40f},
        {"symbol": "NQ=F", "name": "NQ", "color": 0x2ecc71}
    ]
    
    mc = mpf.make_marketcolors(up='#00ffbb', down='#ff3366', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#1a1a1a', facecolor='#050505')

    # Start the "Multipart" payload
    files = {}
    embeds = [{
        "title": "🏛️ UNDERGROUND UPDATE",
        "description": "🟢 **CONDITIONS FAVORABLE**\nClear for Execution",
        "color": 0x2ecc71,
        "fields": [
            {"name": "📅 Upcoming Economic Intelligence", "value": "No major releases. Watch session extremes."},
            {"name": "🗞️ Market Briefing", "value": briefing}
        ],
        "footer": {"text": f"Follow the money, not fake gurus. | UWS Intel Desk | {current_est}"}
    }]

    for i, asset in enumerate(assets):
        df, lvls, sess_o = get_data_and_levels(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}.png"
            fig, axlist = mpf.plot(df, type='candle', style=s, 
                                   title=f"\nUWS INTEL: {asset['name']} (1m) | {current_est}",
                                   hlines=dict(hlines=list(lvls.values()), colors='#C0C0C0', linewidths=1.2, alpha=0.6),
                                   returnfig=True, figscale=1.6, tight_layout=True)
            
            # Label the levels on the right margin
            ax = axlist[0]
            for label, price in lvls.items():
                ax.text(len(df) + 2, price, label, color='#C0C0C0', fontsize=8, va='center')

            fig.savefig(fname, facecolor=fig.get_facecolor())
            plt.close(fig)
            
            # Add file to the upload dictionary
            files[f"file{i}"] = (fname, open(fname, 'rb'), 'image/png')
            
            # Add analysis card linked to the image
            embeds.append({
                "title": f"📈 {asset['name']} ANALYSIS",
                "color": asset["color"],
                "image": {"url": f"attachment://{fname}"},
                "footer": {"text": f"8:30 AM Anchor: {round(sess_o, 2)}"}
            })

    if webhook:
        # THE FIX: Wrap the json in 'payload_json' for multipart requests
        payload = {"payload_json": json.dumps({"embeds": embeds})}
        response = requests.post(webhook, files=files, data=payload)
        
        # Cleanup
        for _, file_tuple in files.items(): file_tuple[1].close()
        
        if response.status_code in [200, 204]:
            print("UWS Update Delivered Successfully.")
        else:
            print(f"Failed to send. Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    main()
