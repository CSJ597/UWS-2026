def get_economic_intel(api_key):
    """Detects Today's Red Folders OR finds the Next major USD event."""
    if not api_key: return "No News", 0x2ecc71
    
    tz_est = pytz.timezone('US/Eastern')
    now = datetime.now(tz_est)
    today_str = now.strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/calendar/economic?token={api_key}"
    
    try:
        response = requests.get(url, timeout=10).json()
        calendar = response.get('economicCalendar', [])
        
        today_events = []
        future_events = []

        for event in calendar:
            impact = event.get('impact')
            country = event.get('country')
            e_date_raw = event.get('date', '') # Format: "YYYY-MM-DD HH:MM:SS"
            
            if impact == 3 and country == 'US':
                e_date_str = e_date_raw.split(' ')[0]
                e_time_str = e_date_raw.split(' ')[1] if ' ' in e_date_raw else ""
                
                # Convert event time to EST
                e_dt = datetime.strptime(e_date_raw, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(tz_est)
                
                # Case 1: Today's High Impact
                if e_date_str == today_str:
                    diff = e_dt - now
                    minutes_left = int(diff.total_seconds() // 60)
                    
                    if minutes_left > 0:
                        timer = f" (In {minutes_left}m)"
                    elif minutes_left > -60:
                        timer = f" (JUST RELEASED)"
                    else:
                        timer = ""
                    today_events.append(f"🚩 **{event.get('event')}**{timer}")
                
                # Case 2: Future High Impact (Next 7 Days)
                elif e_dt > now:
                    future_events.append(e_dt)

        # FINAL LOGIC
        if today_events:
            return "\n".join(today_events), 0xe74c3c # 🔴 Red Status
        elif future_events:
            # Sort to find the absolute next one
            next_event_dt = min(future_events)
            days_away = (next_event_dt.date() - now.date()).days
            day_name = "Tomorrow" if days_away == 1 else next_event_dt.strftime('%A')
            return f"No News Today. Next Major Intel: **{day_name}**", 0x2ecc71 # 🟢 Green Status
        
        return "No News", 0x2ecc71
    except:
        return "No News", 0x2ecc71
