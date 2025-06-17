#!/usr/bin/env python3
"""Final comprehensive analysis of account contacts in SYB API."""

import asyncio
import json
from datetime import datetime
import httpx
from config import Config


async def final_contact_analysis():
    """Perform final comprehensive analysis of all accounts and their contacts."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("📊 Final Comprehensive Contact Analysis")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # Query ALL accounts with all available contact information
    comprehensive_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 100) {
                    edges {
                        node {
                            id
                            businessName
                            businessType
                            country
                            createdAt
                            plan {
                                name
                            }
                            access {
                                users(first: 50) {
                                    edges {
                                        node {
                                            id
                                            name
                                            email
                                            companyRole
                                            createdAt
                                            updatedAt
                                        }
                                    }
                                }
                                pendingUsers(first: 50) {
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
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            print("Fetching all accounts with contact information...")
            
            response = await client.post(
                config.syb_api_url,
                json={"query": comprehensive_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    accounts = data["data"]["me"]["accounts"]["edges"]
                    
                    print(f"\n✅ Retrieved {len(accounts)} accounts")
                    
                    # Analyze the data
                    analysis = analyze_accounts(accounts)
                    
                    # Print results
                    print_analysis_results(analysis)
                    
                    # Save detailed results
                    save_results(analysis, accounts)
                    
                else:
                    print("❌ No data returned")
                    
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


def analyze_accounts(accounts):
    """Analyze accounts to understand contact coverage."""
    
    analysis = {
        "total_accounts": len(accounts),
        "accounts_with_active_users": 0,
        "accounts_with_pending_users": 0,
        "accounts_with_any_contact": 0,
        "accounts_with_no_contact": 0,
        "total_active_contacts": 0,
        "total_pending_contacts": 0,
        "accounts_by_plan": {},
        "accounts_by_country": {},
        "no_contact_accounts": [],
        "accounts_with_multiple_users": 0,
        "earliest_user_per_account": []
    }
    
    for edge in accounts:
        account = edge["node"]
        account_id = account["id"]
        business_name = account["businessName"]
        country = account.get("country")
        plan_name = account.get("plan", {}).get("name") if account.get("plan") else "Unknown"
        created_at = account.get("createdAt")
        
        # Count by plan
        if plan_name not in analysis["accounts_by_plan"]:
            analysis["accounts_by_plan"][plan_name] = 0
        analysis["accounts_by_plan"][plan_name] += 1
        
        # Count by country
        if country:
            if country not in analysis["accounts_by_country"]:
                analysis["accounts_by_country"][country] = 0
            analysis["accounts_by_country"][country] += 1
        
        # Get users
        access = account.get("access", {})
        active_users = []
        pending_users = []
        
        if access:
            users_edges = access.get("users", {}).get("edges", [])
            pending_edges = access.get("pendingUsers", {}).get("edges", [])
            
            active_users = [edge["node"] for edge in users_edges]
            pending_users = [edge["node"] for edge in pending_edges]
        
        # Count contacts
        if active_users:
            analysis["accounts_with_active_users"] += 1
            analysis["total_active_contacts"] += len(active_users)
            
            if len(active_users) > 1:
                analysis["accounts_with_multiple_users"] += 1
            
            # Find earliest user (likely the creator)
            earliest_user = None
            for user in active_users:
                user_created = user.get("createdAt")
                if user_created:
                    if not earliest_user or user_created < earliest_user.get("createdAt", "9999"):
                        earliest_user = user
            
            if earliest_user:
                analysis["earliest_user_per_account"].append({
                    "account_id": account_id,
                    "business_name": business_name,
                    "account_created": created_at,
                    "likely_creator": {
                        "name": earliest_user.get("name"),
                        "email": earliest_user.get("email"),
                        "created": earliest_user.get("createdAt")
                    }
                })
        
        if pending_users:
            analysis["accounts_with_pending_users"] += 1
            analysis["total_pending_contacts"] += len(pending_users)
        
        if active_users or pending_users:
            analysis["accounts_with_any_contact"] += 1
        else:
            analysis["accounts_with_no_contact"] += 1
            analysis["no_contact_accounts"].append({
                "id": account_id,
                "name": business_name,
                "plan": plan_name,
                "country": country,
                "created": created_at
            })
    
    return analysis


def print_analysis_results(analysis):
    """Print the analysis results."""
    
    total = analysis["total_accounts"]
    
    print("\n" + "="*60)
    print("CONTACT COVERAGE ANALYSIS")
    print("="*60)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total accounts analyzed: {total}")
    print(f"  Accounts with active users: {analysis['accounts_with_active_users']} ({analysis['accounts_with_active_users']/total*100:.1f}%)")
    print(f"  Accounts with pending users: {analysis['accounts_with_pending_users']} ({analysis['accounts_with_pending_users']/total*100:.1f}%)")
    print(f"  Accounts with ANY contact: {analysis['accounts_with_any_contact']} ({analysis['accounts_with_any_contact']/total*100:.1f}%)")
    print(f"  Accounts with NO contact: {analysis['accounts_with_no_contact']} ({analysis['accounts_with_no_contact']/total*100:.1f}%)")
    
    print(f"\n👥 USER STATISTICS:")
    print(f"  Total active contacts: {analysis['total_active_contacts']}")
    print(f"  Total pending contacts: {analysis['total_pending_contacts']}")
    print(f"  Accounts with multiple users: {analysis['accounts_with_multiple_users']}")
    print(f"  Average users per account: {analysis['total_active_contacts']/total:.2f}")
    
    print(f"\n📋 ACCOUNTS BY PLAN:")
    for plan, count in sorted(analysis["accounts_by_plan"].items()):
        print(f"  {plan}: {count} accounts")
    
    print(f"\n🌍 TOP COUNTRIES:")
    top_countries = sorted(analysis["accounts_by_country"].items(), key=lambda x: x[1], reverse=True)[:10]
    for country, count in top_countries:
        print(f"  {country}: {count} accounts")
    
    if analysis["no_contact_accounts"]:
        print(f"\n⚠️ ACCOUNTS WITHOUT ANY CONTACTS ({len(analysis['no_contact_accounts'])} total):")
        for account in analysis["no_contact_accounts"][:10]:
            print(f"  - {account['name']} ({account['plan']}) - {account['country']}")
        if len(analysis["no_contact_accounts"]) > 10:
            print(f"  ... and {len(analysis['no_contact_accounts']) - 10} more")


def save_results(analysis, accounts):
    """Save detailed results to files."""
    
    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_accounts": analysis["total_accounts"],
            "accounts_with_active_users": analysis["accounts_with_active_users"],
            "accounts_with_pending_users": analysis["accounts_with_pending_users"],
            "accounts_with_any_contact": analysis["accounts_with_any_contact"],
            "accounts_with_no_contact": analysis["accounts_with_no_contact"],
            "total_active_contacts": analysis["total_active_contacts"],
            "total_pending_contacts": analysis["total_pending_contacts"],
            "coverage_percentage": analysis["accounts_with_any_contact"] / analysis["total_accounts"] * 100
        },
        "by_plan": analysis["accounts_by_plan"],
        "by_country": analysis["accounts_by_country"]
    }
    
    with open("contact_coverage_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n💾 Summary saved to contact_coverage_summary.json")
    
    # Save accounts without contacts
    if analysis["no_contact_accounts"]:
        with open("accounts_without_contacts.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": len(analysis["no_contact_accounts"]),
                "accounts": analysis["no_contact_accounts"]
            }, f, indent=2)
        print(f"💾 Accounts without contacts saved to accounts_without_contacts.json")
    
    # Save likely creators
    if analysis["earliest_user_per_account"]:
        with open("likely_account_creators.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": len(analysis["earliest_user_per_account"]),
                "creators": analysis["earliest_user_per_account"]
            }, f, indent=2)
        print(f"💾 Likely account creators saved to likely_account_creators.json")
    
    # Save all account contacts for notification system
    all_contacts = []
    for edge in accounts:
        account = edge["node"]
        access = account.get("access", {})
        
        contacts = []
        
        # Active users
        if access:
            for user_edge in access.get("users", {}).get("edges", []):
                user = user_edge["node"]
                contacts.append({
                    "type": "active",
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "role": user.get("companyRole")
                })
            
            # Pending users
            for pending_edge in access.get("pendingUsers", {}).get("edges", []):
                pending = pending_edge["node"]
                contacts.append({
                    "type": "pending",
                    "email": pending.get("email")
                })
        
        if contacts:
            all_contacts.append({
                "account_id": account["id"],
                "business_name": account["businessName"],
                "plan": account.get("plan", {}).get("name") if account.get("plan") else "Unknown",
                "contacts": contacts
            })
    
    with open("all_account_contacts.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_accounts_with_contacts": len(all_contacts),
            "accounts": all_contacts
        }, f, indent=2)
    print(f"💾 All account contacts saved to all_account_contacts.json")
    
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    
    coverage = analysis["accounts_with_any_contact"] / analysis["total_accounts"] * 100
    
    if coverage < 50:
        print(f"\n⚠️ CRITICAL: Only {coverage:.1f}% of accounts have contact information!")
        print("\nThis is much lower than expected. Every account should have been created by someone.")
        print("\nPOSSIBLE EXPLANATIONS:")
        print("1. The API is not exposing the original account creator/owner")
        print("2. Many accounts were created through a different system")
        print("3. Account creators have been removed from the system")
        print("4. The 'access.users' only shows explicitly added users, not the creator")
        print("\nRECOMMENDATIONS:")
        print("1. Contact SYB support to understand how to access account creator information")
        print("2. Check if there's a separate API or database with account ownership")
        print("3. Consider that the account creator might be stored elsewhere (billing system, CRM, etc.)")
        print("4. For notifications, focus on the accounts that DO have contacts")
    else:
        print(f"\n✅ {coverage:.1f}% of accounts have contact information available")
        print("\nYou can build a notification system using the access.users field")
        print("For accounts without contacts, you may need to:")
        print("1. Request users be added to those accounts")
        print("2. Use alternative contact methods")
        print("3. Skip notification for those accounts")


if __name__ == "__main__":
    print("SYB API - Final Contact Analysis")
    print("Comprehensive analysis of account contact coverage")
    print("="*80)
    
    asyncio.run(final_contact_analysis())