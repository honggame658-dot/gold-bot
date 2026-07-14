import urllib.request
import json
from datetime import datetime, timezone, timedelta

def get_daily_high_impact_news():
    """
    Fetches the ForexFactory economic calendar and returns a formatted string of
    all High Impact USD events for the current day. Used for AI context.
    """
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            events = json.loads(response.read().decode())
            
            today_events = []
            now = datetime.now(timezone.utc)
            
            for event in events:
                if event.get('country') == 'USD' and event.get('impact') == 'High':
                    event_time_str = event.get('date')
                    if not event_time_str:
                        continue
                        
                    event_time = datetime.fromisoformat(event_time_str).astimezone(timezone.utc)
                    
                    # Check if the event is today
                    if event_time.date() == now.date():
                        # Convert to Cambodia time (UTC+7)
                        kh_time = event_time + timedelta(hours=7)
                        time_str = kh_time.strftime("%I:%M %p (ម៉ោងនៅស្រុកខ្មែរ)")
                        today_events.append(f"- {time_str}: {event.get('title')}")
            
            if today_events:
                return "Today's High Impact USD Events:\n" + "\n".join(today_events)
            else:
                return "No High Impact USD Events today."
                
    except Exception as e:
        print(f"Error checking daily economic calendar: {e}")
        return "Failed to fetch calendar."

def check_upcoming_high_impact_news():
    """
    Checks if there are any High Impact USD events happening within the next 30 minutes. 
    Returns a formatted alert message for Telegram or None.
    """
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            events = json.loads(response.read().decode())
            
            upcoming_events = []
            now = datetime.now(timezone.utc)
            
            for event in events:
                if event.get('country') == 'USD' and event.get('impact') == 'High':
                    event_time_str = event.get('date')
                    if not event_time_str:
                        continue
                        
                    event_time = datetime.fromisoformat(event_time_str).astimezone(timezone.utc)
                    time_diff = event_time - now
                    minutes_until = time_diff.total_seconds() / 60
                    
                    if 0 < minutes_until <= 30:
                        upcoming_events.append({
                            'title': event.get('title'),
                            'minutes': int(minutes_until)
                        })
            
            if upcoming_events:
                msg = "⚠️ <b>[High Impact News Alert]</b>\n"
                msg += "របាយការណ៍សេដ្ឋកិច្ចអាមេរិក (USD) សំខាន់ៗនឹងចេញផ្សាយក្នុងពេលបន្តិចទៀតនេះ៖\n\n"
                for ev in upcoming_events:
                    msg += f"🔥 <b>{ev['title']}</b> ក្នុងរយៈពេល {ev['minutes']} នាទីទៀត!\n"
                msg += "\n<i>សូមប្រុងប្រយ័ត្ន! ទីផ្សារមាស (XAU/USD) អាចនឹងមានការប្រែប្រួលខ្លាំង!</i>"
                return msg
                
            return None
            
    except Exception as e:
        print(f"Error checking economic calendar: {e}")
        return None

if __name__ == "__main__":
    print(get_daily_high_impact_news())
    print("\n---\n")
    print(check_upcoming_high_impact_news())
