import requests
import os

# ---------------- CONFIG ----------------

CF_API = "https://codeforces.com/api/contest.list"

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

LAST_FILE = "last_contest.txt"
LAST_REG_FILE = "last_registration.txt"

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
relative_time = latest.get("relativeTimeSeconds", None)  # negative = seconds until start

print("Found Contest:")
print(contest_name)

# ---- Read last announced contest ----
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r") as f:
        last = f.read().strip()
else:
    last = ""

# ---- Read last registration reminder ----
if os.path.exists(LAST_REG_FILE):
    with open(LAST_REG_FILE, "r") as f:
        last_reg = f.read().strip()
else:
    last_reg = ""

# ---- 1. ANNOUNCEMENT NOTIFICATION ----
if contest_id != last:
    payload = {
        "embeds": [
            {
                "title": "🚀 New Codeforces Contest Announced!",
                "description": f"**{contest_name}**",
                "color": 3447003,  # Blue
                "fields": [
                    {
                        "name": "Contest ID",
                        "value": contest_id,
                        "inline": True
                    },
                    {
                        "name": "Contest Page",
                        "value": "[Click here to view](https://codeforces.com/contests)",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Codeforces Notifier • Announcement"
                }
            }
        ]
    }

    r = requests.post(DISCORD_WEBHOOK, json=payload)

    if r.status_code == 204:
        print("Announcement sent to Discord!")
        with open(LAST_FILE, "w") as f:
            f.write(contest_id)
    else:
        print("Error sending announcement")
        print(r.text)

else:
    print("Announcement already sent.")

# ---- 2. REGISTRATION OPEN NOTIFICATION (within 24 hours) ----
if relative_time is not None:
    seconds_until_start = -relative_time  # positive = time remaining
    hours_until_start = seconds_until_start / 3600

    print(f"Contest starts in {hours_until_start:.1f} hours")

    if hours_until_start <= 24 and contest_id != last_reg:
        payload_reg = {
            "embeds": [
                {
                    "title": "📋 Registration is Open!",
                    "description": f"**{contest_name}** starts in less than 24 hours!\nRegister now before it's too late!",
                    "color": 15844367,  # Orange/Gold
                    "fields": [
                        {
                            "name": "⏰ Starts In",
                            "value": f"{hours_until_start:.1f} hours",
                            "inline": True
                        },
                        {
                            "name": "🔗 Register Now",
                            "value": "[Click here to register](https://codeforces.com/contests)",
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": "Codeforces Notifier • Registration Reminder"
                    }
                }
            ]
        }

        r2 = requests.post(DISCORD_WEBHOOK, json=payload_reg)

        if r2.status_code == 204:
            print("Registration reminder sent to Discord!")
            with open(LAST_REG_FILE, "w") as f:
                f.write(contest_id)
        else:
            print("Error sending registration reminder")
            print(r2.text)

    elif hours_until_start <= 24:
        print("Registration reminder already sent.")
    else:
        print(f"Registration reminder will fire when contest is within 24 hours.")
