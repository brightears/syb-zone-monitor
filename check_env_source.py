#!/usr/bin/env python3
"""Check where .env is being loaded from."""

import os
import sys
from pathlib import Path

# Clear any cached env
if 'WHATSAPP_ACCESS_TOKEN' in os.environ:
    del os.environ['WHATSAPP_ACCESS_TOKEN']

# Show current directory
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {Path(__file__).parent}")

# Manually read .env file
env_path = Path(".env")
print(f"\nReading .env from: {env_path.absolute()}")

if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if 'WHATSAPP_ACCESS_TOKEN' in line:
                print(f"Found in file: {line.strip()[:50]}...")
                break

# Now load with dotenv
from dotenv import load_dotenv, find_dotenv

# Find where dotenv thinks .env is
dotenv_path = find_dotenv()
print(f"\nDotenv found .env at: {dotenv_path}")

# Force reload
load_dotenv(override=True, dotenv_path=".env")

# Check what was loaded
token = os.getenv('WHATSAPP_ACCESS_TOKEN', 'NOT_FOUND')
print(f"\nLoaded token: {token[:30]}...{token[-20:]}")
print(f"Token length: {len(token)}")

# Try direct API call with this token
import httpx
import asyncio

async def test():
    url = "https://graph.facebook.com/v17.0/742462142273418"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(f"\nAPI Test: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.json()}")

asyncio.run(test())