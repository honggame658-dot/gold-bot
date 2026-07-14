import urllib.request
import json

def test_ff():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Fetched {len(data)} events")
            print(data[0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ff()
