#!/usr/bin/env python3
"""Final test to get working account contact information."""

import asyncio
import json
from datetime import datetime

import httpx
from config import Config


async def test_final_contact_query():
    """Test the corrected query for account contacts."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Final Account Contact Information Test")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # Corrected query based on introspection findings
    working_query = """
    query GetAccountContacts {
        me {
            ... on PublicAPIClient {
                accounts(first: 10) {
                    edges {
                        node {
                            id
                            businessName
                            access {
                                users(first: 10) {
                                    edges {
                                        node {
                                            id
                                            name
                                            email
                                            companyRole
                                        }
                                    }
                                }
                                pendingUsers(first: 10) {
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
            print("Executing final corrected query...")
            
            response = await client.post(
                config.syb_api_url,
                json={"query": working_query},
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ Errors in query:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', str(error))}")
                    return False
                
                if "data" in data and data["data"]:
                    me_data = data["data"].get("me", {})
                    accounts_data = me_data.get("accounts", {})
                    account_edges = accounts_data.get("edges", [])
                    
                    print(f"✅ SUCCESS! Retrieved {len(account_edges)} accounts")
                    
                    notification_targets = []
                    total_contacts = 0
                    
                    for edge in account_edges:
                        account = edge.get("node", {})
                        account_id = account.get("id")
                        business_name = account.get("businessName", "Unknown").strip()
                        
                        print(f"\n📊 Account: {business_name}")
                        print(f"  ID: {account_id}")
                        
                        access = account.get("access", {})
                        account_contacts = []
                        
                        # Get active users
                        users_connection = access.get("users", {})
                        if users_connection:
                            users_edges = users_connection.get("edges", [])
                            print(f"  Active Users: {len(users_edges)}")
                            
                            for user_edge in users_edges:
                                user = user_edge.get("node", {})
                                if user:
                                    name = user.get("name", "Unknown")
                                    email = user.get("email")
                                    company_role = user.get("companyRole")
                                    user_id = user.get("id")
                                    
                                    print(f"    User: {name}")
                                    print(f"      ID: {user_id}")
                                    
                                    if email:
                                        print(f"      ✅ Email: {email}")
                                        account_contacts.append({
                                            "id": user_id,
                                            "name": name,
                                            "email": email,
                                            "role": company_role,
                                            "type": "active"
                                        })
                                        total_contacts += 1
                                    else:
                                        print(f"      ❌ Email: None")
                                    
                                    if company_role:
                                        print(f"      Role: {company_role}")
                        
                        # Get pending users
                        pending_connection = access.get("pendingUsers", {})
                        if pending_connection:
                            pending_edges = pending_connection.get("edges", [])
                            print(f"  Pending Users: {len(pending_edges)}")
                            
                            for pending_edge in pending_edges:
                                pending_user = pending_edge.get("node", {})
                                if pending_user:
                                    email = pending_user.get("email")
                                    
                                    if email:
                                        print(f"    ✅ Pending: {email}")
                                        account_contacts.append({
                                            "name": f"Pending User ({email})",
                                            "email": email,
                                            "role": "pending",
                                            "type": "pending"
                                        })
                                        total_contacts += 1
                        
                        # Store account if it has contacts
                        if account_contacts:
                            notification_targets.append({
                                "account_id": account_id,
                                "business_name": business_name,
                                "contacts": account_contacts
                            })
                            print(f"  📧 Total contacts: {len(account_contacts)}")
                        else:
                            print(f"  ❌ No contacts found")
                    
                    print(f"\n🎯 FINAL RESULTS:")
                    print(f"  Total accounts queried: {len(account_edges)}")
                    print(f"  Accounts with contacts: {len(notification_targets)}")
                    print(f"  Total contact emails available: {total_contacts}")
                    
                    if notification_targets:
                        print(f"\n🎉 SUCCESS! Contact information IS available!")
                        print(f"✅ You CAN build the targeted notification system!")
                        
                        # Save results for implementation
                        output_file = "account_contacts.json"
                        with open(output_file, "w") as f:
                            json.dump(notification_targets, f, indent=2)
                        
                        print(f"\n💾 Contact data saved to: {output_file}")
                        
                        print(f"\n📋 Working GraphQL Query:")
                        print(working_query)
                        
                        return True
                    else:
                        print(f"\n❌ No accounts have contact information available")
                        print(f"  This means:")
                        print(f"    - API access may be limited")
                        print(f"    - No users are configured for these accounts")
                        print(f"    - Contact information is restricted")
                        
                        return False
                else:
                    print("❌ No data returned")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False


async def test_single_account_detailed():
    """Test getting detailed info for a single account."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print("DETAILED SINGLE ACCOUNT CONTACT TEST")
    print(f"{'='*60}")
    
    # First get an account ID
    account_list_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 1) {
                    edges {
                        node {
                            id
                            businessName
                        }
                    }
                }
            }
        }
    }
    """
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Get account ID first
            response = await client.post(
                config.syb_api_url,
                json={"query": account_list_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    accounts = data["data"]["me"]["accounts"]["edges"]
                    if accounts:
                        account = accounts[0]["node"]
                        account_id = account["id"]
                        business_name = account["businessName"]
                        
                        print(f"Testing detailed query for: {business_name}")
                        print(f"Account ID: {account_id}")
                        
                        # Now test detailed individual account query
                        detailed_query = f"""
                        query {{
                            me {{
                                ... on PublicAPIClient {{
                                    accounts(first: 1, after: "{account_id.replace('/', '\\/')}") {{
                                        edges {{
                                            node {{
                                                id
                                                businessName
                                                access {{
                                                    users(first: 20) {{
                                                        edges {{
                                                            node {{
                                                                id
                                                                name
                                                                email
                                                                companyRole
                                                            }}
                                                        }}
                                                    }}
                                                    pendingUsers(first: 20) {{
                                                        edges {{
                                                            node {{
                                                                email
                                                            }}
                                                        }}
                                                    }}
                                                }}
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}
                        """
                        
                        response = await client.post(
                            config.syb_api_url,
                            json={"query": detailed_query},
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            if "errors" in data:
                                print("❌ Errors:")
                                for error in data["errors"]:
                                    print(f"  - {error.get('message')}")
                            
                            if "data" in data and data["data"]:
                                print("✅ Detailed query successful")
                                print(json.dumps(data["data"], indent=2))
                        else:
                            print(f"❌ Detailed query failed: {response.status_code}")
                    else:
                        print("❌ No accounts found")
                else:
                    print("❌ No account data")
            else:
                print(f"❌ Account list query failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Detailed test failed: {e}")


def print_implementation_guide(has_contacts):
    """Print implementation guidance based on results."""
    
    print(f"\n{'='*60}")
    print("IMPLEMENTATION GUIDANCE")
    print(f"{'='*60}")
    
    if has_contacts:
        print(f"🎉 NOTIFICATION SYSTEM IS FEASIBLE!")
        print(f"\n📋 Implementation Steps:")
        print(f"  1. ✅ Use the working GraphQL query to get account contacts")
        print(f"  2. ✅ Create notification selection UI:")
        print(f"     - List accounts with checkboxes")
        print(f"     - Show contact count per account")
        print(f"     - Allow selection of specific users/contacts")
        print(f"  3. ✅ Build email notification system:")
        print(f"     - Integration with existing notifier/email.py")
        print(f"     - Template for zone status reports")
        print(f"     - Account-specific zone summaries")
        print(f"  4. ✅ Create notification dashboard:")
        print(f"     - Send to account owners button")
        print(f"     - Custom message option")
        print(f"     - Delivery status tracking")
        
        print(f"\n🔧 Technical Implementation:")
        print(f"  - Add contact retrieval function to zone_monitor.py")
        print(f"  - Extend dashboard with notification controls")
        print(f"  - Use account_contacts.json for testing")
        print(f"  - Group zones by account for targeted reports")
        
        print(f"\n📧 Notification Types:")
        print(f"  - Critical: All zones offline for an account")
        print(f"  - Warning: Multiple zones offline")
        print(f"  - Summary: Daily/weekly status reports")
        print(f"  - Custom: Manual notifications with custom messages")
        
    else:
        print(f"❌ NOTIFICATION SYSTEM LIMITATIONS")
        print(f"\n🔧 Alternative Approaches:")
        print(f"  1. Local Contact Database:")
        print(f"     - Create contacts.json file")
        print(f"     - Map business names to email addresses")
        print(f"     - Manual maintenance required")
        print(f"  2. External Contact Integration:")
        print(f"     - CRM system lookup by business name")
        print(f"     - Google Contacts API")
        print(f"     - CSV import of contact mappings")
        print(f"  3. SYB Support Request:")
        print(f"     - Request API access to contact information")
        print(f"     - Ask about user management endpoints")
        print(f"     - Inquire about notification webhooks")
        
        print(f"\n📝 Recommended Next Steps:")
        print(f"  1. Contact SYB support about contact API access")
        print(f"  2. Implement local contact database as backup")
        print(f"  3. Use business names for manual contact lookup")
        print(f"  4. Build notification system with manual contact entry")
    
    print(f"\n🎯 Business Value:")
    print(f"  - Proactive customer communication about issues")
    print(f"  - Reduced support tickets from unaware customers")
    print(f"  - Improved customer satisfaction through transparency")
    print(f"  - Automated reporting reduces manual work")


if __name__ == "__main__":
    print("SYB Final Account Contact Information Test")
    print("Determining if notification system is feasible")
    print("="*80)
    
    # Run the tests
    result = asyncio.run(test_final_contact_query())
    asyncio.run(test_single_account_detailed())
    
    # Print implementation guidance
    print_implementation_guide(result)