# Discord Auto‑Command Sender (with Web Dashboard)

> **⚠️ FOR EDUCATIONAL USE ONLY**  
> Automating Discord may break their Terms of Service. Use at your own risk. This is for learning how APIs, threads, and web dashboards work.

---

## What does this do?

This script sends commands like `!crime` or `!work` to a Discord channel automatically, on a schedule. It's often used with the **"Unbelievable Boat"** bot to farm coins. It also runs a **live dashboard** (a webpage) where you can see what's happening – commands sent, success/fail, network status, and more.

---

## What you need

- Python 3.6 or newer installed on your computer.
- A Discord **user token** (not a bot token).  
  *How to get it: log in to Discord in your browser, press F12 → go to the "Network" tab → find any request to `discord.com` → copy the value of the `authorization` header.*  
  *Keep this token secret – anyone with it can control your account!*

- The **Channel ID** of the text channel where you want commands sent.  
  *Enable Developer Mode in Discord settings, then right‑click the channel and choose "Copy ID".*

---

## Files you need

Save these three files in the same folder:

- `main.py` – the main script.
- `dashboard.html` – the webpage for the dashboard.
- `style.css` – styles for the dashboard.

---

## How to set it up (no coding knowledge needed)

Open `main.py` in a text editor (like Notepad or VS Code). Look for these lines at the very top:

```python
TOKEN = "YOUR_TOKEN_HERE"
CHANNEL_ID = "1512956231919337482"
```

- Replace `"YOUR_TOKEN_HERE"` with your actual token (keep the quotes).
- Replace the channel ID with your own channel ID.

Next, look for these sections:

```python
COMMANDS = [
    "!crime",
    "!dep all"
]
```
This is the **main loop** – these commands run one after another, then the script sleeps for 5 minutes and repeats.  
You can add or remove any commands you like – just put them inside the brackets, with quotes and commas.

```python
SCHEDULED_COMMANDS = {
    "!work": 60,
    "!slut": 120,
}
```
These are **scheduled commands** – they run on their own timers in the background.  
The number is the **interval in seconds**. Change it to any number you want.

You can also change:

- `DELAY_BETWEEN = 0.0005` – how long to wait between commands in the main loop (in seconds).
- `SLEEP_CYCLE = 300` – how long the main loop sleeps after finishing all commands (in seconds).
- `DASHBOARD_PORT = 8080` – the port for the web dashboard. Change it if port 8080 is already used.

---

## How to run it

1. Open a terminal / command prompt in the folder where the files are.
2. Type:
   ```bash
   python main.py
   ```
3. You'll see logs in the terminal. If everything is fine, it will say "Token valid" and start sending commands.

To stop the script, press `Ctrl + C`.

---

## The Dashboard

While the script is running, open your web browser and go to:

```
http://localhost:8080
```

You'll see a page that shows:

- Network status (Online / Offline)
- Whether your token is valid
- Total commands sent so far
- How long the script has been running
- A card for each command with last send time and success/fail
- A log of recent activity

The dashboard updates every 5 seconds automatically.

---

## If something goes wrong

| Problem | What to check |
|---------|---------------|
| "Invalid token" | Your token is wrong or expired – get a new one. |
| "Forbidden" | Your token doesn't have permission to send in that channel. |
| "Channel not found" | The channel ID is wrong – copy it again. |
| Dashboard shows nothing | Make sure `dashboard.html` and `style.css` are in the same folder as `main.py`. Also check if another program is using port 8080 – change `DASHBOARD_PORT` if needed. |
| Network offline | The script will keep trying every 5 seconds – just wait. |

---

## I don't know programming – how do I add my own commands?

- To add a command to the **main loop**: open `main.py`, find the `COMMANDS` list, and add a new line like `"!newcommand"` (don't forget the comma after the previous one).
- To add a **scheduled command**: find `SCHEDULED_COMMANDS`, add a line like `"!newcommand": 90,` – this will run it every 90 seconds.
- You can change intervals, add or remove commands freely – the script will handle it.

---

## Important warnings

- **Never share your token** – it's like a password.
- **Don't spam too fast** – Discord will rate‑limit you. The script handles that automatically, but if you set very short intervals, you might get temporary bans.
- **This is for learning** – using it to gain unfair advantage in games might be against the game's rules.

---

## License

MIT – use it, change it, share it.

---

**P.S.** This whole thing was vibe‑coded – if it breaks, just restart it. 😎
