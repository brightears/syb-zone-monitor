#!/usr/bin/env python3
"""Extract unique account IDs from CSV files and save to JSON."""

import csv
import json

def extract_account_ids():
    """Extract unique account IDs from both CSV files."""
    account_ids = set()
    
    # Read from new_token_soundtrack_accounts.csv
    try:
        with open('new_token_soundtrack_accounts.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'account_id' in row and row['account_id']:
                    account_ids.add(row['account_id'])
        print(f"Found {len(account_ids)} unique account IDs in new_token_soundtrack_accounts.csv")
    except Exception as e:
        print(f"Error reading new_token_soundtrack_accounts.csv: {e}")
    
    # Read from new_token_soundtrack_accounts_with_zones.csv
    initial_count = len(account_ids)
    try:
        with open('new_token_soundtrack_accounts_with_zones.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'account_id' in row and row['account_id']:
                    account_ids.add(row['account_id'])
        print(f"Found {len(account_ids) - initial_count} additional unique account IDs in new_token_soundtrack_accounts_with_zones.csv")
    except Exception as e:
        print(f"Error reading new_token_soundtrack_accounts_with_zones.csv: {e}")
    
    # Convert to sorted list
    account_ids_list = sorted(list(account_ids))
    
    # Save to JSON file
    with open('account_ids.json', 'w', encoding='utf-8') as f:
        json.dump(account_ids_list, f, indent=2)
    
    print(f"\nTotal unique account IDs: {len(account_ids_list)}")
    print(f"Saved to account_ids.json")
    
    return account_ids_list

if __name__ == "__main__":
    extract_account_ids()