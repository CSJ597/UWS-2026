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
# Paste your long Base64 string between the triple quotes below
LOGO_BASE64 = """YOUR_BASE64_STRING_HERE"""

def add_watermark(image_path, base64_str):
    """Centers the logo at the absolute top of the canvas with high clearance."""
    if not base64_str or "YOUR_BASE64" in base64_str:
        return
    try:
        logo_data = base64.b64decode(base64_str)
        logo = Image.open(BytesIO(logo_data)).convert("RGBA")
        base_img = Image.open(image_path).convert("RGBA")
        bw, bh = base_img.size
        
        logo_w = int(bw * 0.12)
        w_percent = (logo_w / float(logo.size[0]))
        logo_h = int((float(logo.size[1]) * float(w_percent)))
        logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        
        center_x = (bw - logo_w) // 2
        position = (center_x, 30) # Fixed at the top
        
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

def get_forex_factory_intel():
    """Fetches official Forex Factory JSON feed for USD High Impact events."""
    url = "https://nfs.forexfactory.com/ff_calendar_thisweek.json"
    tz_est = pytz.timezone('US/Eastern')
    now = datetime.now(tz_est)
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        today_reds, future_reds = [], []
        
        for event in data:
            if event.get('currency') == 'USD' and event.get('impact') == 'High':
                # Parse ISO date and convert to EST
                dt_utc = datetime.fromisoformat(event.get('date').replace('Z', '+00:00'))
                dt_est = dt_utc.astimezone(tz_est)
                
                if dt_est.date() == now.date():
                    time_str = dt_est.strftime('%I:%M %p')
                    today_reds.append(f"🚩 **{event.get('title')}** @ {time_str}")
                elif dt_est > now:
                    future_reds.append((dt_est, event.get('title')))
        
        if today_reds:
            return "\n".join(today_reds), 0xe74c3c # Alert Red
        
        if future_reds:
            future_reds.sort(key=lambda x: x[0])
            next_dt, next_name = future_reds[0]
            return f"No High Impact Today.\n**Next Intel:** {next_name} ({next_dt.strftime('%A @ %I:%M %p')})", 0x2ecc71
            
        return "No High Impact Scheduled.", 0x2ecc71
    except:
        return "Forex Factory Sync Offline.", 0x2ecc71

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
    if df.empty: return None, None
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
    
    eco_intel, embed_color = get_forex_factory_intel()
    briefing = get_finnhub_news(finnhub_key, {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]})
    
    status_header = "\n\n🟢 **CONDITIONS FAVORABLE**" if embed_color == 0x2ecc71 else "\n\n🔴 **CAUTION: HIGH VOLATILITY**"
    centered_title = f"{'\u2002' * 12}🏦  UNDERGROUND UPDATE  🏦"

    embeds = [{
        "title": centered_title,
        "description": status_header,
        "color": embed_color,
        "fields": [
            {"name": "\u200B", "value": "\u200B", "inline": False},
            {"name": "📅 Forex Factory Intel (USD)", "value": eco_intel, "inline": False},
            {"name": "\u200B", "value": "\u200B", "inline": False},
            {"name": "🗞️ Market Briefing", "value": briefing, "inline": False}
        ],
        "footer": {"text": f"Follow the money, not the fake gurus. | {current_est}"}
    }]

    assets = [{"symbol": "GC=F", "name": "GC", "color": 0xf1c40f}, {"symbol": "NQ=F", "name": "NQ", "color": 0x2ecc71}]
    mc = mpf.make_marketcolors(up='#00ffbb', down='#ff3366', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#1a1a1a', facecolor='#050505')

    files = {}
    for i, asset in enumerate(assets):
        df, lvls = get_precision_data(asset["symbol"])
        if df is not None:
            fname = f"{asset['name'].lower()}.png"
            fig, axlist = mpf.plot(df, type='candle', style=s, datetime_format='%I:%M %p', 
                                   hlines=dict(hlines=list(lvls.values()), colors='#C0C0C0', linewidths=1.2, alpha=0.5),
                                   returnfig=True, figscale=1.8)
            
            # ABSOLUTE SEPARATION: Shove chart down to y=0.65
            plt.subplots_adjust(top=0.65, right=0.85)
            
            # MANUAL TITLE: Placed at y=0.75
            title_text = f"1m OPENING LEVELS: {asset['name']} | {df.index[0].strftime('%b %d, %Y')}"
            fig.text(0.5, 0.75, title_text, color='white', ha='center', fontsize=14, fontweight='bold')
            
            ax = axlist[0]
            for label, price in lvls.items():
                ax.text(len(df) + 2.5, price, f"{round(price, 2)} - {label}", 
                        color='#C0C0C0', fontsize=8, fontweight='bold', va='center')

            fig.savefig(fname, facecolor=fig.get_facecolor(), bbox_inches='tight')
            plt.close(fig)
            
            # WATERMARK: Placed at y=30px
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
