import os
import math
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import json
import base64
import time # Added for sync delay
from io import BytesIO
from datetime import datetime, time as dtime
import pytz
import matplotlib.pyplot as plt
from PIL import Image

# --- LOGO CONFIG ---
LOGO_BASE64 = """YOUR_BASE64_STRING_HERE"""

def add_watermark(image_path, base64_str):
    """Improved Base64 overlay with transparency fix."""
    if not base64_str or len(base64_str) < 50:
        print("⚠️ Watermark Skipped: Base64 string looks empty or invalid.")
        return
    try:
        # 1. Prepare Logo
        logo_data = base64.b64decode(base64_str)
        logo = Image.open(BytesIO(logo_data)).convert("RGBA")
        
        # 2. Open Chart
        base_img = Image.open(image_path).convert("RGBA")
        bw, bh = base_img.size
        
        # 3. Dynamic Resize
        logo_w = int(bw * 0.15) # Increased to 15% for better visibility
        w_percent = (logo_w / float(logo.size[0]))
        logo_h = int((float(logo.size[1]) * float(w_percent)))
        logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        
        # 4. Create Overlay Layer
        overlay = Image.new('RGBA', base_img.size, (0,0,0,0))
        # Position: Top Right
        pos = (bw - logo_w - 40, 40)
        overlay.paste(logo, pos, mask=logo)
        
        # 5. Composite and Save
        final_img = Image.alpha_composite(base_img, overlay)
        final_img.convert("RGB").save(image_path, "PNG")
        print(f"✅ Logo applied successfully to {image_path}")
    except Exception as e:
        print(f"❌ Branding Error: {str(e)}")

# --- [REST OF YOUR CORE FUNCTIONS REMAIN THE SAME] ---

def main():
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    finnhub_key = os.getenv("FINNHUB_KEY")
    current_est = format_est_time()
    
    eco_intel, embed_color = get_economic_intel(finnhub_key)
    briefing = get_finnhub_news(finnhub_key, {"Gold": ["gold", "xau"], "Nasdaq": ["nasdaq", "tech", "nq"]})
    
    status_header = "\n\n\u200B\n🟢 **CONDITIONS FAVORABLE**\n*Clear for Execution*" if embed_color == 0x2ecc71 else "\n\n\u200B\n🔴 **CAUTION: HIGH VOLATILITY**\n*Red Folder Intelligence Detected*"
    
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
            fig, axlist = mpf.plot(df, type='candle', style=s, 
                                   title=f"\n1m OPENING LEVELS: {asset['name']} | {df.index[0].strftime('%b %d, %Y')}",
                                   datetime_format='%I:%M %p', 
                                   hlines=dict(hlines=list(lvls.values()), colors='#C0C0C0', linewidths=1.2, alpha=0.5),
                                   returnfig=True, figscale=1.8)
            
            plt.subplots_adjust(right=0.85)
            ax = axlist[0]
            for label, price in lvls.items():
                ax.text(len(df) + 2.5, price, f"{round(price, 2)} - {label}", color='#C0C0C0', fontsize=8, fontweight='bold', va='center')

            fig.savefig(fname, facecolor=fig.get_facecolor(), bbox_inches='tight')
            plt.close(fig)
            
            # --- BRANDING ---
            add_watermark(fname, LOGO_BASE64)
            
            # Use binary read for Discord
            files[f"file{i}"] = (fname, open(fname, 'rb'), 'image/png')
            embeds.append({
                "title": f"📈 {asset['name']} 1m OPENING LEVELS",
                "color": asset["color"],
                "image": {"url": f"attachment://{fname}"},
                "footer": {"text": f"Follow the money, not the fake gurus."}
            })

    if webhook:
        # FINAL PUSH
        requests.post(webhook, files=files, data={"payload_json": json.dumps({"embeds": embeds})})
        for _, ftup in files.items(): ftup[1].close()

if __name__ == "__main__":
    main()
