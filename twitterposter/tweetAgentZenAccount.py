import tweepy
import sqlite3
import schedule
import time
import random
import os
import logging
import sys
from datetime import datetime
from dotenv import load_dotenv

# Configure logging to write to logaction.log
logging.basicConfig(
    filename="logaction.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Load environment variables from .env file
load_dotenv()

# X API credentials from environment variables
CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")

# Verify credentials
missing_credentials = [
    key for key, value in [
        ("CONSUMER_KEY", CONSUMER_KEY),
        ("CONSUMER_SECRET", CONSUMER_SECRET),
        ("ACCESS_TOKEN", ACCESS_TOKEN),
        ("ACCESS_TOKEN_SECRET", ACCESS_TOKEN_SECRET)
    ] if value is None
]
if missing_credentials:
    logging.error(f"Missing environment variables: {', '.join(missing_credentials)}")
    raise ValueError(f"Missing environment variables: {', '.join(missing_credentials)}")

# Initialize Tweepy
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# SQLite database setup
def init_db():
    conn = sqlite3.connect("bot_tasks.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, content TEXT, done INTEGER, date TEXT)''')
    conn.commit()
    conn.close()

# Populate or reset tasks for the current day
def reset_tasks():
    conn = sqlite3.connect("bot_tasks.db")
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if tasks exist for today
    c.execute("SELECT COUNT(*) FROM tasks WHERE date = ?", (today,))
    count = c.fetchone()[0]
    
    if count == 0:
        # Clear old tasks
        c.execute("DELETE FROM tasks")
        # Insert 10 new tasks for today (customize content as needed)
        sample_tasks = [
            "Task 1: Sharing a cool fact!",
            "Task 2: Did you know this?",
            "Task 3: Stay tuned for more!",
            "Task 4: Loving this day!",
            "Task 5: Here's a tip!",
            "Task 6: Fun fact incoming!",
            "Task 7: Keep it real!",
            "Task 8: What's up, X?",
            "Task 9: Almost done!",
            "Task 10: Last post of the day!"
        ]
        for task in sample_tasks:
            c.execute("INSERT INTO tasks (content, done, date) VALUES (?, 0, ?)", (task, today))
    else:
        # Reset done flags for existing tasks
        c.execute("UPDATE tasks SET done = 0 WHERE date = ?", (today,))
    
    conn.commit()
    conn.close()

# Post a single task and mark it as done
def post_task():
    conn = sqlite3.connect("bot_tasks.db")
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get an unposted task
    c.execute("SELECT id, content FROM tasks WHERE done = 0 AND date = ? LIMIT 1", (today,))
    task = c.fetchone()
    
    if task:
        task_id, content = task
        try:
            # Post to X
            api.update_status(content)
            logging.info(f"Posted: {content}")
            # Mark as done
            c.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
            conn.commit()
        except tweepy.TweepyException as e:
            logging.error(f"Error posting: {e}")
    else:
        logging.info("No tasks left to post today.")
    
    conn.close()

# Catch up on unposted tasks from today with random delay
def catch_up_tasks():
    conn = sqlite3.connect("bot_tasks.db")
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get all unposted tasks for today
    c.execute("SELECT id, content FROM tasks WHERE done = 0 AND date = ?", (today,))
    tasks = c.fetchall()
    
    if tasks:
        logging.info(f"Found {len(tasks)} unposted tasks for today. Posting now...")
        for task_id, content in tasks:
            try:
                # Post to X
                api.update_status(content)
                logging.info(f"Catch-up posted: {content}")
                # Mark as done
                c.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
                conn.commit()
                # Random delay between 1.5 and 5 minutes (90 to 300 seconds)
                if tasks.index((task_id, content)) < len(tasks) - 1:  # No delay after the last task
                    delay = random.uniform(90, 300)
                    logging.info(f"Waiting {delay:.1f} seconds before next post...")
                    time.sleep(delay)
            except tweepy.TweepyException as e:
                logging.error(f"Error posting catch-up task: {e}")
    else:
        logging.info("No unposted tasks to catch up on.")
    
    conn.close()

# Check if any tasks remain for today
def has_remaining_tasks():
    conn = sqlite3.connect("bot_tasks.db")
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM tasks WHERE done = 0 AND date = ?", (today,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

# Schedule 10 posts throughout the day (e.g., every 2 hours from 8 AM to 2 AM)
def schedule_posts():
    schedule.clear()
    # Spread 10 posts over ~18 hours (every 2 hours)
    times = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00", "00:00", "02:00"]
    for t in times:
        schedule.every().day.at(t).do(post_task)
    # Schedule task reset for midnight
    schedule.every().day.at("00:01").do(reset_tasks)

# Main loop
def main():
    init_db()
    catch_up_tasks()  # Handle any unposted tasks from today on startup
    reset_tasks()     # Ensure tasks are set for today
    schedule_posts()  # Set up the daily schedule
    while True:
        schedule.run_pending()
        # Check if there are any remaining tasks for today
        if not has_remaining_tasks():
            logging.info("All tasks for today completed. Stopping bot.")
            sys.exit(0)
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()