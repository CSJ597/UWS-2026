import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests as discord_requests
from curl_cffi import requests as news_requests
from bs4 import BeautifulSoup
import json
import base64
import sys
import csv
from io import BytesIO, StringIO
from datetime import datetime, time as dtime
import pytz
import matplotlib.pyplot as plt
from PIL import Image

# --- 🏦 UWS LOGO CONFIG ---
# Your original Base64 string is preserved below
LOGO_BASE64 = """iVBORw0KGgoAAAANSUhEUgAABAAAAAQACAYAAAB/HSuDAAAACXBIWXMAAAsTAAALEwEAmpwYAAZrLUlEQVR4nOz9d7QlSXrYB35fROTN6++7z3tX3nd197S3024Mxs8AAwIDRxAAKZKQqF26w5W4h0dcrnQOVxRXu8ulxCOK0uFSFFcLGpAgBIIAAQyAccD0zPRM++6q6nLvvXrvXZcmIr79I/2991VVz7Sb7u/XXe/emxkZGRmZERmfiS+w1Wyp3b1dDQzDMAzDMAzDMAzDvG8RQETvdiEYhmEYhmEYhmEYhnl7Ee92ARiGYRiGYRiGYRiGefsRhIDvdiEYhmEYhmEYhmEYhnl7YQ8AhmEYhmEYhmEYhvkAIICAYwAwDMMwDMMwDMMwzPsc9gBgGIZhGIZhGIZhmA8AAohDADAMwzAMwzAMwzDM+"""

# --- 🛠️ CORE UTILITIES ---
def add_watermark(image_path, base64_str):
    """Places the logo in the original Top-Right position with padding fix."""
    if not base64_str or len(base64_str) < 50: return
    try:
        clean_str = "".join(base64_str.split())
        rem = len(clean_str) % 4
        if rem > 0: clean_str += "=" * (4 - rem)
        
        logo_data = base64.b64decode(clean_str)
        logo = Image.open(BytesIO(logo_data)).convert("RGBA")
        base_img = Image.open(image_path).convert("RGBA")
        bw, bh = base_img.size
        logo_w = int(bw * 0.10)
        w_percent = (logo_w / float(logo.size[0]))
        logo_h = int((float(logo.size[1]) * float(w_percent)))
        logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        position = (bw - logo_w - 30, 30) 
        transparent = Image.new('RGBA', base_img.size, (0,0,0,0))
        transparent.paste(base_img, (0,0))
        transparent.paste(logo, position, mask=logo)
        transparent.convert("RGB").save(image_path)
    except Exception as e: print(f"Branding Error: {e}")

def get_red_folder_intel():
    """Fetches high-impact news from QuantCrawler with failover sentries."""
    tz_est = pytz.timezone('US/Eastern')
    now = datetime.now(tz_est)
    today_reds = []

    # Sentry 1: QuantCrawler RedFolder Scraper
    try:
        url = "https://www.quantcrawler.com/redfolder"
        resp = news_requests.get(url, impersonate="chrome120", timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # QuantCrawler displays events in a clean list or table
        for event_row in soup.find_all(['div', 'tr']):
            text = event_row.get_text().lower()
            if "usd" in text and ("high" in text or "red" in text):
                today_reds.append(f"🚩 **{event_row.get_text().strip()}**")
        
        if today_reds: return "\n".join(today_reds), 0xe74c3c
    except: pass

    # Sentry 2: Fallback to CSV CDN (Institutional Stability)
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.csv"
        resp = discord_requests.get(url, timeout=10)
        f = StringIO(resp.content.decode('utf-8-sig'))
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Currency') == 'USD' and row.get('Impact') == 'High':
                dt_str = f"{row['Date']} {row['Time']}"
                dt_raw = datetime.strptime(dt_str, '%m-%d-%Y %I:%M%p')
                dt_est = pytz.timezone('GMT').localize(dt_raw).astimezone(tz_est)
                if dt_est.date() == now.date():
                    status = "✅" if dt_est < now else "🚩"
                    today_reds.append(f"{status} **{row['Subject']}** @ {dt_est.strftime('%I:%M %p')}")
        if today_reds: return "\n".join(today_reds), 0xe74c3c
    except: pass
        
    return "No High Impact Today.", 0x2ecc71

def get_finnhub_briefing(api_key):
    """Restores the Gold and Nasdaq sector briefing."""
    if not api_key: return "News feed unavailable."
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        resp = discord_requests.get(url, timeout=10)
        data = resp.json()
        found = []
        assets = {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]}
        for item in data[:40]:
            h, l = item['headline'], item['url']
            for name, keys in assets.items():
                if any(k in h.lower() for k in keys):
                    found.append(f"• **{name}**: [{h[:65]}...]({l})")
                    break
            if len(found) >= 2: break
        return "\n".join(found) if found else "No relevant headlines."
    except: return "Briefing unavailable."

def get_precision_data(ticker):
    """Calculates UWS levels with session logic."""
    df = yf.download(ticker, period="5d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None
    df.index = df.index.tz_convert('US/Eastern')
    session_start = datetime.combine(df.index[-1].date(), dtime(8, 30)).replace(tzinfo=pytz.timezone('US/Eastern'))
    window = df[df.index >= session_start]
    if window.empty: window = df.tail(100)
    sess_o = window.iloc[0]['Open']
    aH, aL = (window['High'] - sess_o).tolist(), (sess_o - window['Low']).tolist()
    def p_rank(arr, p):
        s = sorted(arr)
        return s[max(0, math.ceil((p/100) * len(s)) - 1)]
    lvls = {"P50 H": sess_o + p_rank(aH, 50), "P50 L": sess_o - p_rank(aL, 50),
            "P75 H": sess_o + p_rank(aH, 75), "P75 L": sess_o - p_rank(aL, 75),
            "P90 H": sess_o + p_rank(aH, 90), "P90 L": sess_o - p_rank(aL, 90)}
    return window, lvls

def main():
    print("🚀 Initializing Quant-Messiah Battle Prep...")
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    finnhub_key = os.getenv("FINNHUB_KEY")
    current_est = datetime.now(pytz.timezone('US/Eastern')).strftime('%I:%M %p EST')
    
    eco_intel, embed_color = get_red_folder_intel()
    briefing = get_finnhub_briefing(finnhub_key)
    
    embeds = [{
        "title": f"{'\u2002' * 12}🏦  UNDERGROUND UPDATE  🏦",
        "description": "🟢 **FAVORABLE**" if embed_color == 0x2ecc71 else "🔴 **CAUTION: VOLATILITY**",
        "color": embed_color,
        "fields": [{"name": "📅 Economic Intel", "value": eco_intel, "inline": False},
                   {"name": "🗞️ Market Briefing", "value": briefing, "inline": False}],
        "footer": {"text": f"Follow the money, not the fake gurus. | {current_est}"}
    }]

    assets = [{"symbol": "GC=F", "name": "GC", "color": 0xf1c40f}, {"symbol": "NQ=F", "name": "NQ", "color": 0x2ecc71}]
    mc = mpf.make_marketcolors(up='#00ffbb', down='#ff3366', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, facecolor='#050505')

    files = {}
    for i, asset in enumerate(assets):
        df, lvls = get_precision_data(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}.png"
            fig, axlist = mpf.plot(df, type='candle', style=s, returnfig=True, figscale=1.8,
                                   title=f"\n1m OPENING LEVELS: {asset['name']} | {df.index[0].strftime('%b %d')}")
            plt.subplots_adjust(right=0.85)
            for label, price in lvls.items():
                axlist[0].text(len(df) + 2.5, price, f"{round(price, 2)} - {label}", color='#C0C0C0', fontsize=8, va='center')
            fig.savefig(fname, facecolor='#050505', bbox_inches='tight')
            plt.close(fig)
            add_watermark(fname, LOGO_BASE64)
            files[f"file{i}"] = (fname, open(fname, 'rb'), 'image/png')
            embeds.append({"title": f"📈 {asset['name']} Levels", "color": asset["color"], "image": {"url": f"attachment://{fname}"}})

    if webhook:
        discord_requests.post(webhook, files=files, data={"payload_json": json.dumps({"embeds": embeds})})
        for _, f_ptr in files.items(): f_ptr[1].close()
    print("✅ Intelligence Drop Complete.")

if __name__ == "__main__":
    main()
