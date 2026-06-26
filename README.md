# 🚀 Codeforces Div.3/Div.4 Discord Notifier

A Python automation tool that checks for new upcoming **Codeforces Div.3** and **Div.4** contests and sends a notification to a Discord channel using a **Discord Webhook**.

The project is automated using **GitHub Actions**, so it runs every morning without requiring your computer to be on.

---

## ✨ Features

- ✅ Detects newly announced Codeforces Div.3 and Div.4 contests
- ✅ Sends Discord notifications automatically
- ✅ Prevents duplicate notifications
- ✅ Uses the official Codeforces API
- ✅ Runs every morning using GitHub Actions
- ✅ Lightweight and easy to set up

---

## 📂 Project Structure

```
cf-discord-notifier/
│
├── .github/
│   └── workflows/
│       └── notify.yml
│
├── main.py
├── requirements.txt
├── last_contest.txt
├── .gitignore
└── README.md
```

---

## 🛠️ Technologies Used

- Python 3
- Requests
- Discord Webhooks
- GitHub Actions
- Codeforces API

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/Chirag6722/cf-discord-notifier.git
```

Move into the project folder:

```bash
cd cf-discord-notifier
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔑 Discord Webhook Setup

1. Open your Discord Server.
2. Go to **Server Settings → Integrations → Webhooks**.
3. Create a new webhook.
4. Copy the webhook URL.

For security, store it as a GitHub Secret or an environment variable instead of hardcoding it in your code.

---

## ▶️ Run Locally

```bash
python main.py
```

---

## 🤖 GitHub Actions

The workflow automatically runs every morning and:

1. Fetches upcoming contests from the Codeforces API.
2. Checks for new Div.3 or Div.4 contests.
3. Sends a Discord notification if a new contest is found.
4. Updates `last_contest.txt` to avoid duplicate notifications.

You can also trigger the workflow manually from the **Actions** tab in GitHub.

---

## 📸 Sample Discord Notification

```
🚀 New Codeforces Contest!

Codeforces Round (Div. 3)

https://codeforces.com/contests
```

---

## 🔮 Future Improvements

- Contest start time in IST
- Countdown until contest starts
- Beautiful Discord embeds
- Support for Div.2, Educational and Global Rounds
- Docker support
- Full Discord Bot version

---

## 🤝 Contributing

Contributions are welcome!

Feel free to fork the repository, improve the project, and create a pull request.

---

## 📜 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Chirag Honnyal**

GitHub: https://github.com/Chirag6722
