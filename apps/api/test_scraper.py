import urllib.request, json
req = urllib.request.Request('https://hs-consumer-api.espncricinfo.com/v1/pages/matches/current?lang=en&latest=true', headers={'User-Agent': 'Mozilla/5.0'})
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    matches = data.get('matches', [])
    for m in matches[:5]:
        status_raw = m.get('state', '')
        teams = [t.get('team', {}).get('longName', 'Unknown') for t in m.get('teams', [])]
        print(f"Match: {' vs '.join(teams)} (Status: {status_raw})")
except Exception as e:
    print('Error:', e)
