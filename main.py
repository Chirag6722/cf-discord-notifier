import requests
import os
from datetime import datetime, timezone, timedelta

# ---------------- CONFIG ----------------

CF_API = "https://codeforces.com/api/contest.list"
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
LAST_FILE = "last_contest.txt"
LAST_REMINDER_FILE = "last_reminder.txt"
IST = timezone(timedelta(hours=5, minutes=30))
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


def get_logged_ids(filepath):
    """Read logged contest/reminder IDs from a file and return as a set."""
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, "r") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return set()


def log_id(filepath, identifier):
    """Append a contest/reminder ID to a file."""
    try:
        with open(filepath, "a") as f:
            f.write(f"{identifier}\n")
    except Exception as e:
        print(f"Error writing {identifier} to {filepath}: {e}")


def format_ist_time(unix_timestamp):
    """Convert Unix timestamp to IST formatted string."""
    utc_time = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    ist_time = utc_time.astimezone(IST)
    day = ist_time.day
    # e.g., "5 July"
    date_str = f"{day} {ist_time.strftime('%B')}"
    # e.g., "8:35 PM IST"
    time_str = ist_time.strftime("%I:%M %p IST").lstrip("0")
    return date_str, time_str


def format_duration(seconds):
    """Convert seconds to human-readable duration."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if minutes:
        return f"{hours}h {minutes}m"
    return f"{hours} hours"


def format_hours(hours):
    """Format remaining hours as a neat string."""
    if hours.is_integer():
        return f"{int(hours)} Hours"
    return f"{hours:.1f} Hours"


def send_discord_webhook(payload):
    """Send payload to Discord Webhook and return True if successful."""
    try:
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        if r.status_code in (200, 204):
            return True
        else:
            send_error_alert(f"Failed to send Discord message.\nStatus: `{r.status_code}`\n```{r.text}```")
            return False
    except Exception as e:
        send_error_alert(f"Webhook connection error:\n```{str(e)}```")
        return False


def main():
    try:
        response = requests.get(CF_API, timeout=10)

        if response.status_code != 200:
            send_error_alert(f"Failed to connect to Codeforces API.\nStatus: `{response.status_code}`")
            return

        data = response.json()

        if data["status"] != "OK":
            send_error_alert(f"Codeforces API returned an error:\n```{data.get('comment', 'Unknown error')}```")
            return

        contests = data["result"]
        upcoming_contests = []

        # Find all upcoming Div. 3/Div. 4 contests
        for contest in contests:
            if contest.get("phase") != "BEFORE":
                continue
            name = contest.get("name", "")
            if "Div. 3" in name or "Div. 4" in name:
                upcoming_contests.append(contest)

        if not upcoming_contests:
            print("No upcoming Div.3/Div.4 contests found.")
            return

        print(f"Found {len(upcoming_contests)} upcoming Div.3/Div.4 contest(s).")

        # Read logged state files
        announced_contests = get_logged_ids(LAST_FILE)
        sent_reminders = get_logged_ids(LAST_REMINDER_FILE)

        # Process from earliest starting to latest starting
        upcoming_contests.sort(key=lambda c: c.get("startTimeSeconds", 0))

        for contest in upcoming_contests:
            contest_id = str(contest["id"])
            contest_name = contest["name"]
            start_time_unix = contest.get("startTimeSeconds")
            duration_secs = contest.get("durationSeconds")

            if not start_time_unix:
                print(f"Skipping contest {contest_name} (ID: {contest_id}) as it has no start time.")
                continue

            current_time = datetime.now(timezone.utc).timestamp()
            seconds_until_start = start_time_unix - current_time
            hours_until_start = seconds_until_start / 3600

            print(f"Processing: {contest_name} (ID: {contest_id}) | Starts in {hours_until_start:.2f} hours")

            if hours_until_start <= 0:
                # Contest has already started or is in the past, skip
                continue

            date_str, time_str = format_ist_time(start_time_unix)
            duration_str = format_duration(duration_secs) if duration_secs else "TBA"
            contest_link = f"https://codeforces.com/contest/{contest_id}"

            # ---- 1. ANNOUNCEMENT NOTIFICATION ----
            if contest_id not in announced_contests:
                payload = {
                    "content": "@everyone",
                    "embeds": [
                        {
                            "title": "🚨 Codeforces Div.3/4 Announced",
                            "description": (
                                f"**━━━━━━━━━━━━━━━━━━━━━━**\n"
                                f"🏆 **{contest_name}**\n\n"
                                f"📅 **{date_str}**\n"
                                f"🕒 **{time_str}**\n"
                                f"⏳ **Starts in {format_hours(hours_until_start)}**\n\n"
                                f"🔗 **[Open Contest]({contest_link})**\n"
                                f"**━━━━━━━━━━━━━━━━━━━━━━**"
                            ),
                            "color": 5793266,  # Blurple
                            "thumbnail": {"url": CF_THUMBNAIL},
                            "footer": {"text": "Codeforces Notifier • Announcement"}
                        }
                    ]
                }
                print(f"Sending announcement for {contest_name}...")
                if send_discord_webhook(payload):
                    log_id(LAST_FILE, contest_id)
                    announced_contests.add(contest_id)

            # ---- 2. 24-HOUR REMINDER ----
            # Fire reminder if contest is less than 24 hours away
            reminder_key_24h = f"{contest_id}_24h"
            if hours_until_start <= 24 and reminder_key_24h not in sent_reminders:
                payload = {
                    "content": "@everyone",
                    "embeds": [
                        {
                            "title": "⏰ Codeforces Contest Reminder!",
                            "description": (
                                f"**━━━━━━━━━━━━━━━━━━━━━━**\n"
                                f"🏆 **{contest_name}**\n\n"
                                f"📅 **{date_str}**\n"
                                f"🕒 **{time_str}**\n"
                                f"⏳ **Starts in less than 24 hours ({format_hours(hours_until_start)})**\n\n"
                                f"🔗 **[Register Now]({contest_link})**\n"
                                f"**━━━━━━━━━━━━━━━━━━━━━━**"
                            ),
                            "color": 15844367,  # Gold/Yellow
                            "thumbnail": {"url": CF_THUMBNAIL},
                            "footer": {"text": "Codeforces Notifier • 24h Reminder"}
                        }
                    ]
                }
                print(f"Sending 24-hour reminder for {contest_name}...")
                if send_discord_webhook(payload):
                    log_id(LAST_REMINDER_FILE, reminder_key_24h)
                    sent_reminders.add(reminder_key_24h)



    except Exception as e:
        send_error_alert(f"Unexpected bot error:\n```{str(e)}```")
        raise


if __name__ == "__main__":
    main()
