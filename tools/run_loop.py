import time
import subprocess
import sys
import datetime

# Define Python Path (Adjust if needed or use sys.executable)
PYTHON_EXE = sys.executable

def run_fetch():
    print(f"[{datetime.datetime.now()}] Running Fetch Cycle...")
    result = subprocess.run([PYTHON_EXE, "tools/fetch_articles.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

def main():
    print("Starting AI Pulse Automation Loop (24h)...")
    print("Press Ctrl+C to stop.")
    
    while True:
        try:
            run_fetch()
            # Sleep for 24 hours (86400 seconds)
            print(f"[{datetime.datetime.now()}] Sleeping for 24 hours...")
            time.sleep(86400)
        except KeyboardInterrupt:
            print("\nStopping Automation Loop.")
            break
        except Exception as e:
            print(f"Critical Error: {e}")
            time.sleep(60) # Retry after 1 min on crash

if __name__ == "__main__":
    main()
