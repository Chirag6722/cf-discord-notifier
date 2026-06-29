import requests
import os

# ---------------- CONFIG ----------------

CF_API = "https://codeforces.com/api/contest.list"

# Local testing
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1519927236084371547/NS0GqKUdTDc6zTb35QQ1fXk8qDgaZTy1lvjbFBKDr3OfHG5ZrHasSowLl2gIO1MIQ7yy"

LAST_FILE = "last_contest.txt"

# ----------------------------------------

response = requests.get(CF_API)

if response.status_code != 200:
    print("Failed to connect to Codeforces API")
    exit()

data = response.json()

if data["status"] != "OK":
    print("Codeforces API Error")
    exit()

contests = data["result"]

latest = None

for contest in contests:

    if contest["phase"] != "BEFORE":
        continue

    name = contest["name"]

    if "Div. 3" in name or "Div. 4" in name:
        latest = contest
        break

if latest is None:
    print("No upcoming Div.3/Div.4 contest found.")
    exit()

contest_id = str(latest["id"])
contest_name = latest["name"]

print("Found Contest:")
print(contest_name)

# Read last contest
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r") as f:
        last = f.read().strip()
else:
    last = ""

# Already notified?
if contest_id == last:
    print("Already notified.")
    exit()

# Discord Embed
payload = {
    "embeds": [
        {
            "title": "🚀 New Codeforces Contest!",
            "description": f"**{contest_name}**",
            "color": 3447003,
            "fields": [
                {
                    "name": "Contest ID",
                    "value": contest_id,
                    "inline": True
                },
                {
                    "name": "Contest Page",
                    "value": "https://codeforces.com/contests",
                    "inline": False
                }
            ],
            "footer": {
                "text": "Codeforces Notifier"
            }
        }
    ]
}

r = requests.post(DISCORD_WEBHOOK, json=payload)

if r.status_code == 204:

    print("Discord message sent!")

    with open(LAST_FILE, "w") as f:
        f.write(contest_id)

else:
    print("Error sending Discord message")
    print(r.text)
