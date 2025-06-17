#!/usr/bin/env python3
"""Comprehensive account contact discovery with corrected query."""

import asyncio
import os
import json
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()


async def comprehensive_contact_discovery():
    """Final comprehensive discovery of all account contacts."""
    
    api_key = os.getenv("SYB_API_KEY")
    api_url = os.getenv("SYB_API_URL", "https://api.soundtrackyourbrand.com/v2")
    
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 COMPREHENSIVE ACCOUNT CONTACT DISCOVERY")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # Corrected query based on what works
    query = """
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
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            print("Fetching all accounts with contact information...")
            
            response = await client.post(
                api_url,
                json={"query": query},
                headers=headers
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ GraphQL Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message')}")
                    return
                
                if "data" in data and data["data"]:
                    accounts = data["data"]["me"]["accounts"]["edges"]
                    
                    print(f"\n✅ Retrieved {len(accounts)} accounts")
                    
                    # Analyze the data
                    analysis = analyze_contact_coverage(accounts)
                    
                    # Print results
                    print_comprehensive_results(analysis)
                    
                    # Save all results
                    save_comprehensive_results(analysis, accounts)
                    
                else:
                    print("❌ No data in response")
                    
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


def analyze_contact_coverage(accounts):
    """Analyze contact coverage across all accounts."""
    
    total_accounts = len(accounts)
    accounts_with_active_users = 0
    accounts_with_pending_users = 0
    accounts_with_any_contact = 0
    accounts_with_no_contact = 0
    total_active_contacts = 0
    total_pending_contacts = 0
    
    contact_coverage_by_country = {}
    no_contact_accounts = []
    all_contacts = []
    likely_creators = []
    
    for edge in accounts:
        account = edge["node"]
        account_id = account["id"]
        business_name = account["businessName"]
        country = account.get("country", "Unknown")
        created_at = account.get("createdAt")
        
        # Initialize country tracking
        if country not in contact_coverage_by_country:
            contact_coverage_by_country[country] = {
                "total": 0,
                "with_contacts": 0
            }
        contact_coverage_by_country[country]["total"] += 1
        
        # Get access data
        access = account.get("access", {})
        active_users = []
        pending_users = []
        
        if access:
            users_edges = access.get("users", {}).get("edges", [])
            pending_edges = access.get("pendingUsers", {}).get("edges", [])
            
            active_users = [edge["node"] for edge in users_edges]
            pending_users = [edge["node"] for edge in pending_edges]
        
        # Count contacts
        has_contacts = False
        
        if active_users:
            accounts_with_active_users += 1
            total_active_contacts += len(active_users)
            has_contacts = True
            
            # Find likely creator (earliest user)
            earliest_user = None
            for user in active_users:
                user_created = user.get("createdAt")
                if user_created:
                    if not earliest_user or user_created < earliest_user.get("createdAt", "9999"):
                        earliest_user = user
            
            if earliest_user:
                likely_creators.append({
                    "account_id": account_id,
                    "business_name": business_name,
                    "account_created": created_at,
                    "likely_creator": {
                        "name": earliest_user.get("name"),
                        "email": earliest_user.get("email"),
                        "created": earliest_user.get("createdAt")
                    }
                })
            
            # Store contacts
            for user in active_users:
                all_contacts.append({
                    "account_id": account_id,
                    "business_name": business_name,
                    "type": "active",
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "role": user.get("companyRole"),
                    "created": user.get("createdAt")
                })
        
        if pending_users:
            accounts_with_pending_users += 1
            total_pending_contacts += len(pending_users)
            has_contacts = True
            
            # Store pending contacts
            for pending_user in pending_users:
                all_contacts.append({
                    "account_id": account_id,
                    "business_name": business_name,
                    "type": "pending",
                    "email": pending_user.get("email")
                })
        
        if has_contacts:
            accounts_with_any_contact += 1
            contact_coverage_by_country[country]["with_contacts"] += 1
        else:
            accounts_with_no_contact += 1
            no_contact_accounts.append({
                "account_id": account_id,
                "business_name": business_name,
                "country": country,
                "created": created_at
            })
    
    return {
        "total_accounts": total_accounts,
        "accounts_with_active_users": accounts_with_active_users,
        "accounts_with_pending_users": accounts_with_pending_users,
        "accounts_with_any_contact": accounts_with_any_contact,
        "accounts_with_no_contact": accounts_with_no_contact,
        "total_active_contacts": total_active_contacts,
        "total_pending_contacts": total_pending_contacts,
        "contact_coverage_by_country": contact_coverage_by_country,
        "no_contact_accounts": no_contact_accounts,
        "all_contacts": all_contacts,
        "likely_creators": likely_creators
    }


def print_comprehensive_results(analysis):
    """Print comprehensive analysis results."""
    
    total = analysis["total_accounts"]
    coverage_percentage = (analysis["accounts_with_any_contact"] / total * 100) if total > 0 else 0
    
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE CONTACT COVERAGE ANALYSIS")
    print("="*60)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total accounts analyzed: {total}")
    print(f"  Accounts with active users: {analysis['accounts_with_active_users']} ({analysis['accounts_with_active_users']/total*100:.1f}%)")
    print(f"  Accounts with pending users: {analysis['accounts_with_pending_users']} ({analysis['accounts_with_pending_users']/total*100:.1f}%)")
    print(f"  Accounts with ANY contact: {analysis['accounts_with_any_contact']} ({coverage_percentage:.1f}%)")
    print(f"  Accounts with NO contact: {analysis['accounts_with_no_contact']} ({analysis['accounts_with_no_contact']/total*100:.1f}%)")
    
    print(f"\n👥 CONTACT STATISTICS:")
    print(f"  Total active contacts: {analysis['total_active_contacts']}")
    print(f"  Total pending contacts: {analysis['total_pending_contacts']}")
    print(f"  Total contacts available: {analysis['total_active_contacts'] + analysis['total_pending_contacts']}")
    print(f"  Average contacts per account: {(analysis['total_active_contacts'] + analysis['total_pending_contacts'])/total:.2f}")
    
    print(f"\n🌍 CONTACT COVERAGE BY COUNTRY:")
    for country, stats in sorted(analysis["contact_coverage_by_country"].items(), 
                                key=lambda x: x[1]["total"], reverse=True)[:10]:
        coverage = (stats["with_contacts"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {country}: {stats['with_contacts']}/{stats['total']} ({coverage:.1f}%)")
    
    print(f"\n⚠️ MISSING CONTACT ANALYSIS:")
    if coverage_percentage < 100:
        print(f"  {analysis['accounts_with_no_contact']} accounts ({analysis['accounts_with_no_contact']/total*100:.1f}%) have NO contact information")
        
        if analysis['no_contact_accounts']:
            print(f"\n  Sample accounts without contacts:")
            for account in analysis['no_contact_accounts'][:5]:
                print(f"    - {account['business_name']} ({account['country']})")
            if len(analysis['no_contact_accounts']) > 5:
                print(f"    ... and {len(analysis['no_contact_accounts']) - 5} more")
    
    print(f"\n🎯 CONCLUSION:")
    if coverage_percentage >= 80:
        print(f"✅ EXCELLENT: {coverage_percentage:.1f}% of accounts have contact information!")
        print("  You can build a comprehensive notification system.")
    elif coverage_percentage >= 60:
        print(f"✅ GOOD: {coverage_percentage:.1f}% of accounts have contact information.")
        print("  You can build a notification system for most accounts.")
    elif coverage_percentage >= 40:
        print(f"⚠️ MODERATE: {coverage_percentage:.1f}% of accounts have contact information.")
        print("  You can notify many accounts, but some will be missed.")
    else:
        print(f"❌ LOW: Only {coverage_percentage:.1f}% of accounts have contact information.")
        print("  This suggests the API doesn't expose primary account owners.")
        print("  Most accounts were likely created by users not shown in access.users")


def save_comprehensive_results(analysis, accounts):
    """Save all results to files."""
    
    timestamp = datetime.now().isoformat()
    
    # Save summary statistics
    summary = {
        "timestamp": timestamp,
        "statistics": {
            "total_accounts": analysis["total_accounts"],
            "accounts_with_active_users": analysis["accounts_with_active_users"],
            "accounts_with_pending_users": analysis["accounts_with_pending_users"],
            "accounts_with_any_contact": analysis["accounts_with_any_contact"],
            "accounts_with_no_contact": analysis["accounts_with_no_contact"],
            "total_active_contacts": analysis["total_active_contacts"],
            "total_pending_contacts": analysis["total_pending_contacts"],
            "coverage_percentage": (analysis["accounts_with_any_contact"] / analysis["total_accounts"] * 100) if analysis["total_accounts"] > 0 else 0
        },
        "coverage_by_country": analysis["contact_coverage_by_country"]
    }
    
    with open("FINAL_CONTACT_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n💾 Summary saved to FINAL_CONTACT_SUMMARY.json")
    
    # Save all contacts for notification system
    if analysis["all_contacts"]:
        notification_data = {
            "timestamp": timestamp,
            "total_contacts": len(analysis["all_contacts"]),
            "accounts_with_contacts": analysis["accounts_with_any_contact"],
            "contacts": analysis["all_contacts"]
        }
        
        with open("NOTIFICATION_CONTACTS.json", "w") as f:
            json.dump(notification_data, f, indent=2)
        print(f"💾 Notification contacts saved to NOTIFICATION_CONTACTS.json")
    
    # Save accounts without contacts
    if analysis["no_contact_accounts"]:
        no_contacts_data = {
            "timestamp": timestamp,
            "total": len(analysis["no_contact_accounts"]),
            "accounts": analysis["no_contact_accounts"]
        }
        
        with open("ACCOUNTS_WITHOUT_CONTACTS.json", "w") as f:
            json.dump(no_contacts_data, f, indent=2)
        print(f"💾 Accounts without contacts saved to ACCOUNTS_WITHOUT_CONTACTS.json")
    
    # Save likely creators
    if analysis["likely_creators"]:
        creators_data = {
            "timestamp": timestamp,
            "total": len(analysis["likely_creators"]),
            "creators": analysis["likely_creators"]
        }
        
        with open("LIKELY_ACCOUNT_CREATORS.json", "w") as f:
            json.dump(creators_data, f, indent=2)
        print(f"💾 Likely account creators saved to LIKELY_ACCOUNT_CREATORS.json")
    
    print(f"\n✅ Analysis complete! All data saved to JSON files.")


if __name__ == "__main__":
    print("SYB GraphQL API - Final Comprehensive Contact Discovery")
    print("="*80)
    
    asyncio.run(comprehensive_contact_discovery())