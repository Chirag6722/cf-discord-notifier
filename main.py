import requests
import os
from datetime import datetime, timezone, timedelta

# ---------------- CONFIG ----------------

CF_API = "https://codeforces.com/api/contest.list"
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
LAST_FILE = "last_contest.txt"
LAST_REG_FILE = "last_registration.txt"
IST = timedelta(hours=5, minutes=30)
CF_THUMBNAIL = "https://codeforces.org/s/0/images/codeforces-logo-with-telegram.png"

# ----------------------------------------

def send_error_alert(message):
    """Send a Discord error alert if something goes wrong."""
    payload = {
        "content": "@everyone ⚠️ **Codeforces Notifier encountered an error!**",
        "embeds": [
            {
                "title": "❌ Bot Error",
                "description": message,
                "color": 15158332,  # Red
                "footer": {"text": "Codeforces Notifier • Error Alert"}
            }
        ]
    }
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
    except Exception:
        pass  # Don't crash while reporting a crash


def format_ist_time(unix_timestamp):
    """Convert Unix timestamp to IST formatted string."""
    utc_time = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    ist_time = utc_time + IST
    return ist_time.strftime("%d %b %Y, %I:%M %p IST")


def format_duration(seconds):
    """Convert seconds to human-readable duration."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if minutes:
        return f"{hours}h {minutes}m"
    return f"{hours} hours"


try:
    response = requests.get(CF_API, timeout=10)

    if response.status_code != 200:
        send_error_alert(f"Failed to connect to Codeforces API.\nStatus: `{response.status_code}`")
        exit()

    data = response.json()

    if data["status"] != "OK":
        send_error_alert(f"Codeforces API returned an error:\n```{data.get('comment', 'Unknown error')}```")
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

    contest_id      = str(latest["id"])
    contest_name    = latest["name"]
    relative_time   = latest.get("relativeTimeSeconds", None)
    start_time_unix = latest.get("startTimeSeconds", None)
    duration_secs   = latest.get("durationSeconds", None)

    print(f"Found Contest: {contest_name}")

    start_time_str = format_ist_time(start_time_unix) if start_time_unix else "TBA"
    duration_str   = format_duration(duration_secs) if duration_secs else "TBA"
    contest_link   = f"https://codeforces.com/contest/{contest_id}"

    # Read tracking files
    last     = open(LAST_FILE).read().strip()     if os.path.exists(LAST_FILE)     else ""
    last_reg = open(LAST_REG_FILE).read().strip() if os.path.exists(LAST_REG_FILE) else ""

    # ---- 1. ANNOUNCEMENT NOTIFICATION ----
    if contest_id != last:
        payload = {
            "content": "@everyone",
            "embeds": [
                {
                    "title": "🚀 New Codeforces Contest Announced!",
                    "description": f"**{contest_name}**",
                    "color": 3447003,  # Blue
                    "thumbnail": {"url": CF_THUMBNAIL},
                    "fields": [
                        {"name": "📅 Start Time", "value": start_time_str,                             "inline": True},
                        {"name": "⏱️ Duration",   "value": duration_str,                               "inline": True},
                        {"name": "🔗 Contest",    "value": f"[View Contest]({contest_link})",           "inline": False},
                    ],
                    "footer": {"text": "Codeforces Notifier • Announcement"}
                }
            ]
        }

        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        if r.status_code == 204:
            print("Announcement sent to Discord!")
            with open(LAST_FILE, "w") as f:
                f.write(contest_id)
        else:
            send_error_alert(f"Failed to send announcement.\nStatus: `{r.status_code}`\n```{r.text}```")
    else:
        print("Announcement already sent.")

    # ---- 2. REGISTRATION REMINDER (within 24 hours) ----
    if relative_time is not None:
        seconds_until_start = -relative_time  # positive = time remaining
        hours_until_start   = seconds_until_start / 3600

        print(f"Contest starts in {hours_until_start:.1f} hours")

        if hours_until_start <= 200 and contest_id != last_reg:  # TEMP: 200h for testing, change back to 24
            payload_reg = {
                "content": "@everyone",
                "embeds": [
                    {
                        "title": "📋 Registration is Open!",
                        "description": f"**{contest_name}** starts in less than 24 hours!\nRegister now before it's too late!",
                        "color": 15844367,  # Orange/Gold
                        "thumbnail": {"url": CF_THUMBNAIL},
                        "fields": [
                            {"name": "📅 Start Time", "value": start_time_str,                       "inline": True},
                            {"name": "⏰ Starts In",  "value": f"{hours_until_start:.1f} hours",    "inline": True},
                            {"name": "⏱️ Duration",   "value": duration_str,                         "inline": True},
                            {"name": "🔗 Register",   "value": f"[Register Now]({contest_link})",    "inline": False},
                        ],
                        "footer": {"text": "Codeforces Notifier • Registration Reminder"}
                    }
                ]
            }

            r2 = requests.post(DISCORD_WEBHOOK, json=payload_reg, timeout=10)
            if r2.status_code == 204:
                print("Registration reminder sent to Discord!")
                with open(LAST_REG_FILE, "w") as f:
                    f.write(contest_id)
            else:
                send_error_alert(f"Failed to send registration reminder.\nStatus: `{r2.status_code}`\n```{r2.text}```")

        elif hours_until_start <= 24:
            print("Registration reminder already sent.")
        else:
            print(f"Registration reminder will fire when contest is within 24 hours.")

except Exception as e:
    send_error_alert(f"Unexpected bot error:\n```{str(e)}```")
    raise
