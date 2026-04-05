import urllib.request
import json
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://api.github.com/repos/Inayat-0007/teamgenie-ai-PRIVATE-PATENT-2026/actions/runs'
req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')
with urllib.request.urlopen(req, context=ctx) as r:
    data = json.loads(r.read().decode())
    for run in data['workflow_runs'][:5]:
        print(f"ID: {run['id']}, Title: {run['display_title']}, Status: {run['status']}, Conclusion: {run['conclusion']}")
