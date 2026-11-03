import json
import urllib.request

req = urllib.request.Request(
    'http://127.0.0.1:8000/studio/projects/prj-2b1d7c6f93ed',
    headers={'X-API-Key': 'QIIteTN3BpwDCYc2bTmK_VFbiM5x1A6W3HPE-iC3vm0'}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())

print(f"PROJECT: {data['name']} ({data['id']})")
print(f"Status: {data['status']} | is_running: {data['is_running']}")
print(f"Branch: {data['branch']}")
print(f"Tokens: {data['usage']['total_tokens']} (in: {data['usage']['input_tokens']}, out: {data['usage']['output_tokens']})")

print("\n=== TICKETS ===")
for t in data.get('tickets', []):
    print(f"#{t['sequence']} [{t['status']}] {t['title']} (attempts={t['attempts']}) - commit={t['commit_sha'][:8] if t['commit_sha'] else 'none'}")
