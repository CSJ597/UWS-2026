import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests as std_requests # Use standard requests for Discord
from curl_cffi import requests as anti_bot_requests # Use curl_cffi for news
import json
import base64
import sys
from io import BytesIO
from datetime import datetime, time as dtime
import pytz
import matplotlib.pyplot as plt
from PIL import Image

# --- LOGO CONFIG ---
LOGO_BASE64 = """iVBORw0KGgoAAAANSUhEUgAABAAAAAQACAYAAAB/HSuDAAAACXBIWXMAAAsTAAALEwEAmpwYAAZrLUlEQVR4nOz9d7QlSXrYB35fROTN6++7z3tX3nd197S3024Mxs8AAwIDRxAAKZKQqF26w5W4h0dcrnQOVxRXu8ulxCOK0uFSFFcLGpAgBIIAAQyAccD0zPRM++6q6nLvvXrvXZcmIr79I/2991VVz7Sb7u/XXe/emxkZGRmZERmfiS+w1Wyp3b1dDQzDMAzDMAzDMAzDvG8RQETvdiEYhmEYhmEYhmEYhnl7Ee92ARiGYRiGYRiGYRiGefsRhIDvdiEYhmEYhmEYhmEYhnl7YQ8AhmEYhmEYhmEYhvkAIICAYwAwDMMwDMMwDMMwzPsc9gBgGIZhGIZhGIZhmA8AAohDADAMwzAMwzAMwzDM+"""

# --- UTILITIES ---
def add_watermark(image_path, base64_str):
    if not base64_str or len(base64_str) < 50: return
    try:
        # Fix padding issue
        missing_padding = len(base64_str) % 4
        if missing_padding:
            base64_str += '=' * (4 - missing_padding)
            
        logo_data = base64.b64decode(base64_str)
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

def get_forex_factory_intel():
    url = "https://www.forexfactory.com/ff_calendar_thisweek.json"
    tz_est = pytz.timezone('US/Eastern')
    now = datetime.now(tz_est)
    try:
        # Use curl_cffi only for news to bypass protection
        response = anti_bot_requests.get(url, impersonate="chrome110", timeout=15)
        data = response.json()
        today_reds, future_reds = [], []
        for event in data:
            if event.get('currency') == 'USD' and event.get('impact') == 'High':
                dt_utc = datetime.fromisoformat(event.get('date').replace('Z', '+00:00'))
                dt_est = dt_utc.astimezone(tz_est)
                if dt_est.date() == now.date():
                    status = "✅" if dt_est < now else "🚩"
                    today_reds.append(f"{status} **{event.get('title')}** @ {dt_est.strftime('%I:%M %p')}")
                elif dt_est > now:
                    future_reds.append((dt_est, event.get('title')))
        if today_reds: return "\n".join(today_reds), 0xe74c3c 
        if future_reds:
            future_reds.sort(key=lambda x: x[0])
            next_dt, next_name = future_reds[0]
            day = "Tomorrow" if (next_dt.date() - now.date()).days == 1 else next_dt.strftime('%A')
            return f"No High Impact Today. Next: {next_name} ({day} @ {next_dt.strftime('%I:%M %p')})", 0x2ecc71
        return "No High Impact Scheduled.", 0x2ecc71
    except: return "Economic Intel Stream Offline.", 0x2ecc71

def get_finnhub_news(api_key, assets):
    if not api_key: return "News Feed Offline."
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        response = std_requests.get(url, timeout=10)
        data = response.json()
        found = {}
        for item in data[:50]:
            h, l = item['headline'], item['url']
            for name, keys in assets.items():
                if name not in found and any(k in h.lower() for k in keys):
                    found[name] = f"• **{name}**: [{h[:70]}...]({l})"
        return "\n".join(found.values()) if found else "No relevant headlines."
    except: return "News Feed Offline."

def get_precision_data(ticker):
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
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    finnhub_key = os.getenv("FINNHUB_KEY")
    current_est = datetime.now(pytz.timezone('US/Eastern')).strftime('%I:%M %p EST')
    eco_intel, embed_color = get_forex_factory_intel()
    briefing = get_finnhub_news(finnhub_key, {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]})
    
    embeds = [{"title": f"{'\u2002' * 12}🏦  UNDERGROUND UPDATE  🏦",
               "description": "🟢 **FAVORABLE**" if embed_color == 0x2ecc71 else "🔴 **CAUTION: VOLATILITY**",
               "color": embed_color,
               "fields": [{"name": "📅 Economic Intel", "value": eco_intel, "inline": False},
                          {"name": "🗞️ Market Briefing", "value": briefing, "inline": False}],
               "footer": {"text": f"Follow the money, not the fake gurus. | {current_est}"}}]

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
        # Use standard requests for Discord to avoid NotImplementedError
        std_requests.post(webhook, files=files, data={"payload_json": json.dumps({"embeds": embeds})})
        for _, ftup in files.items(): ftup[1].close()

if __name__ == "__main__":
    main()
