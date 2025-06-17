#!/usr/bin/env python3
"""Run full account discovery in the background.

This script processes all accounts from the CSV files and saves
complete zone and contact information for the dashboard.
"""

import subprocess
import sys
import time
from pathlib import Path


def main():
    """Run the full account discovery process."""
    print("Starting full account discovery process...")
    print("This will process all 863 accounts and may take 30-45 minutes.")
    print("The process will run in the background and save results to:")
    print("- accounts_discovery_results.json")
    print("- accounts_discovery_summary.json")
    print("\nYou can monitor progress in the log file: process_accounts.log")
    
    # Ensure we're in the right directory
    project_dir = Path(__file__).parent
    
    # Run the process
    cmd = [sys.executable, "process_all_accounts.py"]
    
    print("\nStarting background process...")
    
    # Run in background
    process = subprocess.Popen(
        cmd,
        cwd=str(project_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"Process started with PID: {process.pid}")
    print("\nYou can check progress with:")
    print(f"  tail -f process_accounts.log")
    print("\nTo stop the process:")
    print(f"  kill {process.pid}")
    
    # Wait a moment to see if it starts successfully
    time.sleep(2)
    
    if process.poll() is None:
        print("\nProcess is running successfully!")
    else:
        print("\nProcess failed to start!")
        stdout, stderr = process.communicate()
        if stdout:
            print("STDOUT:", stdout.decode())
        if stderr:
            print("STDERR:", stderr.decode())
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())