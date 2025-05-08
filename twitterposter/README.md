this project was  avibe code in the grok conversation in the attached link https://x.com/i/grok?conversation=1920386341327487435






```markdown
# X Posting Bot

This is a Python-based bot that automatically posts 10 scheduled messages daily to X (formerly Twitter) using the X API. It uses a local SQLite database to manage tasks, preserves all tasks (completed or not), and handles missed posts with random delays. The bot is designed to run on a Linux system, starting automatically at boot and restarting daily via a systemd service and timer.

## Features
- **Daily Posting**: Posts 10 messages per day at scheduled times (08:00–02:00, every 2 hours).
- **Task Management**: Stores tasks in a SQLite database (`bot_tasks.db`), never deleting completed tasks.
- **Dynamic Task Addition**: If no tasks exist for the current day, generates 10 new tasks using a customizable `generate_daily_tasks` function.
- **Retroactive Posting**: Catches up on missed posts with random 1.5–5 minute delays between posts to comply with X API rate limits.
- **Secure Credentials**: Loads X API credentials from a `.env` file using `python-dotenv`.
- **Logging**: Logs all actions (posts, errors, delays) to `logaction.log` with timestamps.
- **Automatic Shutdown**: Stops when all daily tasks are completed.
- **Systemd Integration**: Runs as a systemd service, starting at boot and restarting daily at 00:05.

## Project Structure
```
