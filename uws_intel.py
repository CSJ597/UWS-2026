import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import json
import base64
from io import BytesIO
from datetime import datetime, time
import pytz
import matplotlib.pyplot as plt
from PIL import Image

# --- LOGO CONFIG ---
LOGO_BASE64 = """YOUR_BASE64_STRING_HERE"""

def add_watermark(image_path, base64_str):
    """Decodes Base64 logo and centers it at the very top of the chart."""
    if not base64_str or "YOUR_BASE64" in base64_str:
        return
    try:
        logo_data = base64.b64decode(base64_str)
        logo = Image.open(BytesIO(logo_data)).convert("RGBA")
        
        base_img = Image.open(image_path).convert("RGBA")
        base_w, base_h = base_img.size
        
        # Keep logo size consistent (10% of width)
        logo_w = int(base_w * 0.10)
        w_percent = (logo_w / float(logo.size[0]))
        logo_h = int((float(logo.size[1]) * float(w_percent)))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        
        # Position: MATHEMATICAL CENTER
        center_x = (base_w - logo_w) // 2
        position = (center_x, 15) # 15px from the absolute top
        
        transparent = Image.new('RGBA', base_img.size, (0,0,0,0))
        transparent.paste(base_img, (0,0))
        transparent.paste(logo, position, mask=logo)
        
        transparent.convert("RGB").save(image_path)
    except Exception as e:
        print(f"Branding Error: {e}")

# --- 1. CORE LOGIC ---
def percentile_nearest_rank(arr, percentile):
    if not arr: return 0
    arr_sorted = sorted(arr)
    index = math.ceil((percentile / 100) * len(arr_sorted)) - 1
    return arr_sorted[max(0, index)]

def format_est_time():
    est = pytz.timezone('US/Eastern')
    return datetime.now(est).strftime('%I:%M %p EST')

def get_economic_intel(api_key):
    if not api_key: return "No News Today.", 0x2ecc71
    tz_est = pytz.timezone('US/Eastern')
    now = datetime.now(tz_est)
    url = f"https://finnhub.io/api/v1/calendar/economic?token={api_key}"
    try:
        response = requests.get(url, timeout=10).json()
        calendar = response.get('economicCalendar', [])
        today, future = [], []
        for e in calendar:
            if e.get('impact') == 3 and e.get('country') == 'US':
                e_date_raw = e.get('date', '')
                if not e_date_raw: continue
                e_dt = datetime.strptime(e_date_raw, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(tz_est)
                if e_dt.date() == now.date():
                    diff = int((e_dt - now).total_seconds() // 60)
                    timer = f" (In {diff}m)" if diff > 0 else " (JUST RELEASED)" if diff > -60 else ""
                    today.append(f"🚩 **{e.get('event')}**{timer}")
                elif e_dt > now: future.append(e_dt)
        if today: return "\n".join(today), 0xe74c3c
        if future:
            next_ev = min(future)
            day = "Tomorrow" if (next_ev.date() - now.date()).days == 1 else next_ev.strftime('%A')
            return f"No News Today. Next Major Intel: **{day}**", 0x2ecc71
        return "No News Today.", 0x2ecc71
    except: return "No News Today.", 0x2ecc71

def get_finnhub_news(api_key, assets):
    if not api_key: return "No News"
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        data = requests.get(url, timeout=10).json()
        found = {}
        for item in data[:50]:
            h, l = item['headline'], item['url']
            for name, keys in assets.items():
                if name not in found and any(k in h.lower() for k in keys):
                    found[name] = f"• **{name}**: [{h[:75]}...]({l})"
        return "\n".join(found.values()) if found else "No News"
    except: return "No News"

# --- 2. DATA & LEVELS ---
def get_precision_data(ticker):
    df = yf.download(ticker, period="5d", interval="1m", multi_level_index=False, progress=False)
    if df.empty: return None, None, None
    df.index = df.index.tz_convert('US/Eastern')
    session_start = datetime.combine(df.index[-1].date(), time(8, 30)).replace(tzinfo=pytz.timezone('US/Eastern'))
    window = df[df.index >= session_start]
    if window.empty: window = df.tail(500)
    sess_o = window.iloc[0]['Open']
    aH, aL = (window['High'] - sess_o).tolist(), (sess_o - window['Low']).tolist()
    
    lvls = {
        "P50 H": sess_o + percentile_nearest_rank(aH, 50), "P50 L": sess_o - percentile_nearest_rank(aL, 50),
        "P75 H": sess_o + percentile_nearest_rank(aH, 75), "P75 L": sess_o - percentile_nearest_rank(aL, 75),
        "P90 H": sess_o + percentile_nearest_rank(aH, 90), "P90 L": sess_o - percentile_nearest_rank(aL, 90)
    }
    return window, lvls

# --- 3. MAIN EXECUTION ---
def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    finnhub_key = os.getenv("FINNHUB_KEY")
    current_est = format_est_time()
    
    eco_intel, embed_color = get_economic_intel(finnhub_key)
    briefing = get_finnhub_news(finnhub_key, {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]})
    
    status_header = "\n\n🟢 **CONDITIONS FAVORABLE**\n*Clear for Execution*" if embed_color == 0x2ecc71 else "\n\n🔴 **CAUTION: HIGH VOLATILITY**\n*Red Folder Intelligence Detected*"
    
    centered_title = f"{'\u2002' * 12}🏦  UNDERGROUND UPDATE  🏦"

    embeds = [{
        "title": centered_title,
        "description": status_header,
        "color": embed_color,
        "fields": [
            {"name": "\u200B", "value": "\u200B", "inline": False},
            {"name": "📅 Upcoming Economic Events", "value": eco_intel, "inline": False},
            {"name": "\u200B", "value": "\u200B", "inline": False},
            {"name": "🗞️ Market Briefing", "value": briefing, "inline": False},
            {"name": "\u200B", "value": "\u200B", "inline": False}
        ],
        "footer": {"text": f"Follow the money, not the fake gurus. | UWS Intel Desk | {current_est}"}
    }]

    assets = [{"symbol": "GC=F", "name": "GC", "color": 0xf1c40f}, {"symbol": "NQ=F", "name": "NQ", "color": 0x2ecc71}]
    mc = mpf.make_marketcolors(up='#00ffbb', down='#ff3366', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#1a1a1a', facecolor='#050505')

    files = {}
    for i, asset in enumerate(assets):
        df, lvls = get_precision_data(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}.png"
            
            # --- OVERLAP FIX: Added pad and top adjustment ---
            fig, axlist = mpf.plot(df, type='candle', style=s, 
                                   title=f"\n1m OPENING LEVELS: {asset['name']} | {df.index[0].strftime('%b %d, %Y')}",
                                   datetime_format='%I:%M %p', 
                                   hlines=dict(hlines=list(lvls.values()), colors='#C0C0C0', linewidths=1.2, alpha=0.5),
                                   returnfig=True, figscale=1.8)
            
            # Subplot Adjustments: push top down (0.85) and right side in (0.85)
            plt.subplots_adjust(top=0.82, right=0.85)
            ax = axlist[0]
            
            # Extra padding for the title text to clear the logo height
            ax.set_title(ax.get_title(), pad=80, fontweight='bold') 

            for label, price in lvls.items():
                ax.text(len(df) + 2.5, price, f"{round(price, 2)} - {label}", 
                        color='#C0C0C0', fontsize=8, fontweight='bold', va='center')

            fig.savefig(fname, facecolor=fig.get_facecolor(), bbox_inches='tight')
            plt.close(fig)
            
            # Applying Watermark (Now has clearance)
            add_watermark(fname, LOGO_BASE64)
            
            files[f"file{i}"] = (fname, open(fname, 'rb'), 'image/png')
            embeds.append({
                "title": f"📈 {asset['name']} 1m OPENING LEVELS",
                "color": asset["color"],
                "image": {"url": f"attachment://{fname}"},
                "footer": {"text": f"Follow the money, not the fake gurus."}
            })

    if webhook:
        requests.post(webhook, files=files, data={"payload_json": json.dumps({"embeds": embeds})})
        for _, ftup in files.items(): ftup[1].close()

if __name__ == "__main__":
    main()
