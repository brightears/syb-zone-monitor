#!/usr/bin/env python3
"""Simple test to get account contacts ignoring GraphQL errors."""

import asyncio
import os
import json
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()


async def simple_contact_test():
    """Simple test to get account contacts."""
    
    api_key = os.getenv("SYB_API_KEY")
    api_url = os.getenv("SYB_API_URL", "https://api.soundtrackyourbrand.com/v2")
    
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Simple Account Contact Test")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # Simple query that we know works
    query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 50) {
                    edges {
                        node {
                            id
                            businessName
                            access {
                                users(first: 20) {
                                    edges {
                                        node {
                                            id
                                            name
                                            email
                                            companyRole
                                        }
                                    }
                                }
                                pendingUsers(first: 20) {
                                    edges {
                                        node {
                                            email
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            print("Fetching accounts with contact information...")
            
            response = await client.post(
                api_url,
                json={"query": query},
                headers=headers
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Ignore errors and just process data if it exists
                if "data" in data and data["data"]:
                    accounts = data["data"]["me"]["accounts"]["edges"]
                    
                    print(f"\n✅ Retrieved {len(accounts)} accounts")
                    print(f"Errors in response: {len(data.get('errors', []))}")
                    
                    # Analyze the data
                    total_accounts = len(accounts)
                    accounts_with_contacts = 0
                    total_contacts = 0
                    
                    for edge in accounts:
                        account = edge["node"]
                        business_name = account["businessName"]
                        access = account.get("access", {})
                        
                        active_users = []
                        pending_users = []
                        
                        if access:
                            users_edges = access.get("users", {}).get("edges", [])
                            pending_edges = access.get("pendingUsers", {}).get("edges", [])
                            
                            active_users = [edge["node"] for edge in users_edges]
                            pending_users = [edge["node"] for edge in pending_edges]
                        
                        if active_users or pending_users:
                            accounts_with_contacts += 1
                            total_contacts += len(active_users) + len(pending_users)
                            
                            print(f"\n📍 {business_name}")
                            print(f"   Active users: {len(active_users)}")
                            for user in active_users:
                                print(f"     - {user.get('name')} ({user.get('email')})")
                            
                            print(f"   Pending users: {len(pending_users)}")
                            for pending in pending_users:
                                print(f"     - {pending.get('email')}")
                    
                    # Final analysis
                    coverage = (accounts_with_contacts / total_accounts * 100) if total_accounts > 0 else 0
                    
                    print(f"\n" + "="*60)
                    print("FINAL CONTACT ANALYSIS")
                    print("="*60)
                    print(f"Total accounts: {total_accounts}")
                    print(f"Accounts with contacts: {accounts_with_contacts}")
                    print(f"Contact coverage: {coverage:.1f}%")
                    print(f"Total contacts available: {total_contacts}")
                    print(f"Average contacts per account: {total_contacts/total_accounts:.2f}")
                    
                    # Assessment
                    if coverage >= 50:
                        print(f"\n✅ GOOD: {coverage:.1f}% coverage is sufficient for a notification system")
                        print("You can build notifications using the access.users field")
                    else:
                        print(f"\n⚠️ LIMITED: Only {coverage:.1f}% coverage")
                        print("The API does not expose the primary account creator/owner for most accounts")
                        print("This suggests accounts are created through a system that doesn't add the creator to access.users")
                        
                        if accounts_with_contacts > 0:
                            print(f"\nHowever, you can still notify {accounts_with_contacts} accounts that DO have contacts")
                            print("For the rest, you may need to:")
                            print("1. Contact SYB support about accessing account creator information")
                            print("2. Ask account owners to add themselves as users")
                            print("3. Use alternative contact methods")
                    
                else:
                    print("❌ No data in response")
                    
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(simple_contact_test())