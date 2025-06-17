#!/usr/bin/env python3
"""Final comprehensive test to get all account contacts."""

import asyncio
import os
import json
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()


async def final_comprehensive_test():
    """Final comprehensive test to understand contact coverage."""
    
    api_key = os.getenv("SYB_API_KEY")
    api_url = os.getenv("SYB_API_URL", "https://api.soundtrackyourbrand.com/v2")
    
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 FINAL COMPREHENSIVE ACCOUNT CONTACT TEST")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # Query to get all accounts with contacts
    query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 100) {
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
            print("Fetching ALL accounts with contact information...")
            
            response = await client.post(
                api_url,
                json={"query": query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Process data even if there are errors
                if "data" in data and data["data"]:
                    accounts = data["data"]["me"]["accounts"]["edges"]
                    
                    print(f"\n✅ Retrieved {len(accounts)} accounts")
                    print(f"GraphQL errors: {len(data.get('errors', []))}")
                    
                    # Analyze contact coverage
                    total_accounts = len(accounts)
                    accounts_with_contacts = 0
                    total_active_contacts = 0
                    total_pending_contacts = 0
                    accounts_with_contacts_list = []
                    
                    print(f"\nAnalyzing contact coverage...")
                    
                    for i, edge in enumerate(accounts):
                        try:
                            account = edge["node"]
                            business_name = account.get("businessName", "Unknown")
                            access = account.get("access")
                            
                            active_users = []
                            pending_users = []
                            
                            if access:
                                users_connection = access.get("users", {})
                                pending_connection = access.get("pendingUsers", {})
                                
                                if users_connection and "edges" in users_connection:
                                    active_users = [user_edge["node"] for user_edge in users_connection["edges"]]
                                
                                if pending_connection and "edges" in pending_connection:
                                    pending_users = [pending_edge["node"] for pending_edge in pending_connection["edges"]]
                            
                            # Count contacts
                            has_contacts = len(active_users) > 0 or len(pending_users) > 0
                            
                            if has_contacts:
                                accounts_with_contacts += 1
                                total_active_contacts += len(active_users)
                                total_pending_contacts += len(pending_users)
                                
                                accounts_with_contacts_list.append({
                                    "business_name": business_name,
                                    "active_users": len(active_users),
                                    "pending_users": len(pending_users),
                                    "contacts": [
                                        {
                                            "type": "active",
                                            "name": user.get("name"),
                                            "email": user.get("email"),
                                            "role": user.get("companyRole")
                                        } for user in active_users
                                    ] + [
                                        {
                                            "type": "pending",
                                            "email": user.get("email")
                                        } for user in pending_users
                                    ]
                                })
                                
                                print(f"  ✅ {business_name}: {len(active_users)} active, {len(pending_users)} pending")
                            else:
                                print(f"  ❌ {business_name}: No contacts")
                                
                        except Exception as e:
                            print(f"  ⚠️ Error processing account {i}: {e}")
                            continue
                    
                    # Calculate statistics
                    coverage_percentage = (accounts_with_contacts / total_accounts * 100) if total_accounts > 0 else 0
                    total_contacts = total_active_contacts + total_pending_contacts
                    
                    print(f"\n" + "="*60)
                    print("FINAL COMPREHENSIVE ANALYSIS")
                    print("="*60)
                    print(f"Total accounts analyzed: {total_accounts}")
                    print(f"Accounts with contacts: {accounts_with_contacts}")
                    print(f"Accounts without contacts: {total_accounts - accounts_with_contacts}")
                    print(f"Contact coverage: {coverage_percentage:.1f}%")
                    print(f"Total active contacts: {total_active_contacts}")
                    print(f"Total pending contacts: {total_pending_contacts}")
                    print(f"Total contacts available: {total_contacts}")
                    print(f"Average contacts per account: {total_contacts/total_accounts:.2f}")
                    
                    # Save results
                    results = {
                        "timestamp": datetime.now().isoformat(),
                        "analysis": {
                            "total_accounts": total_accounts,
                            "accounts_with_contacts": accounts_with_contacts,
                            "accounts_without_contacts": total_accounts - accounts_with_contacts,
                            "coverage_percentage": coverage_percentage,
                            "total_active_contacts": total_active_contacts,
                            "total_pending_contacts": total_pending_contacts,
                            "total_contacts": total_contacts,
                            "average_contacts_per_account": total_contacts/total_accounts if total_accounts > 0 else 0
                        },
                        "accounts_with_contacts": accounts_with_contacts_list
                    }
                    
                    with open("FINAL_CONTACT_ANALYSIS.json", "w") as f:
                        json.dump(results, f, indent=2)
                    print(f"\n💾 Results saved to FINAL_CONTACT_ANALYSIS.json")
                    
                    # Final assessment
                    print(f"\n🎯 FINAL ASSESSMENT:")
                    
                    if coverage_percentage >= 70:
                        print(f"✅ EXCELLENT: {coverage_percentage:.1f}% contact coverage!")
                        print("You can build a comprehensive notification system.")
                        print(f"You have {total_contacts} email addresses available for notifications.")
                    elif coverage_percentage >= 50:
                        print(f"✅ GOOD: {coverage_percentage:.1f}% contact coverage.")
                        print("You can build a notification system for most accounts.")
                        print(f"You have {total_contacts} email addresses available.")
                    elif coverage_percentage >= 30:
                        print(f"⚠️ MODERATE: {coverage_percentage:.1f}% contact coverage.")
                        print("You can notify some accounts, but many will be missed.")
                        print(f"You have {total_contacts} email addresses available.")
                    else:
                        print(f"❌ LOW: Only {coverage_percentage:.1f}% contact coverage.")
                        print("This confirms that the SYB GraphQL API does NOT expose")
                        print("the primary account owner/creator for most accounts.")
                        print("\nThe 'access.users' field only shows explicitly added users,")
                        print("not the original account creator.")
                        
                        if total_contacts > 0:
                            print(f"\nHowever, you can still notify {accounts_with_contacts} accounts")
                            print(f"that DO have contacts ({total_contacts} email addresses total).")
                        
                        print(f"\nRECOMMENDATIONS:")
                        print(f"1. Contact SYB support to ask about accessing account creator information")
                        print(f"2. Build notifications for accounts that DO have contacts")
                        print(f"3. Request that account owners add themselves as users in the system")
                        print(f"4. Consider alternative contact methods for accounts without API contacts")
                    
                    print(f"\n📧 NOTIFICATION SYSTEM READINESS:")
                    if total_contacts >= 10:
                        print(f"✅ Ready to implement with {total_contacts} available email addresses")
                        print(f"✅ Can notify {accounts_with_contacts} accounts immediately")
                    else:
                        print(f"⚠️ Limited notification capability with only {total_contacts} contacts")
                        print(f"Consider reaching out to SYB for better API access to account owners")
                    
                else:
                    print("❌ No data in response")
                    
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(final_comprehensive_test())