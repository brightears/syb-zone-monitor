#!/usr/bin/env python3
"""Explore access.users field for account contact information."""

import asyncio
import json
from datetime import datetime

import httpx
from config import Config


async def explore_access_users():
    """Investigate access.users for contact information."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Exploring Access Users for Contact Info")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # Test access users with various field combinations
    user_tests = [
        {
            "name": "Basic Users Structure",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    access {
                                        users {
                                            edges {
                                                node {
                                                    id
                                                    name
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
        },
        {
            "name": "Extended User Fields",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    access {
                                        users {
                                            edges {
                                                node {
                                                    id
                                                    name
                                                    email
                                                    role
                                                    isOwner
                                                    isPrimary
                                                    isAdmin
                                                    contactEmail
                                                    phone
                                                    title
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
        },
        {
            "name": "Pending Users",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    access {
                                        pendingUsers {
                                            edges {
                                                node {
                                                    id
                                                    name
                                                    email
                                                    role
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
        },
        {
            "name": "Users with Pagination Info",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
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
                                                }
                                            }
                                            totalCount
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
        }
    ]
    
    async with httpx.AsyncClient(timeout=30) as client:
        contact_data = {}
        
        for i, test in enumerate(user_tests):
            print(f"\n--- Test {i+1}: {test['name']} ---")
            
            try:
                response = await client.post(
                    config.syb_api_url,
                    json={"query": test["query"]},
                    headers=headers
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" in data:
                        print("❌ GraphQL Errors:")
                        for error in data["errors"]:
                            message = error.get('message', str(error))
                            print(f"  - {message}")
                            
                            # Track which fields don't exist
                            if "Cannot query field" in message:
                                field_name = message.split('"')[1] if '"' in message else "unknown"
                                print(f"    ❌ Field '{field_name}' does not exist")
                    
                    if "data" in data and data["data"]:
                        me_data = data["data"].get("me", {})
                        accounts_data = me_data.get("accounts", {})
                        account_edges = accounts_data.get("edges", [])
                        
                        if account_edges:
                            print(f"✅ Success! Found {len(account_edges)} accounts with data:")
                            
                            for edge in account_edges:
                                account = edge.get("node", {})
                                account_id = account.get("id")
                                business_name = account.get("businessName", "Unknown")
                                
                                print(f"\n  Account: {business_name}")
                                print(f"  ID: {account_id}")
                                
                                # Initialize contact data storage
                                if account_id not in contact_data:
                                    contact_data[account_id] = {
                                        "businessName": business_name,
                                        "users": [],
                                        "pendingUsers": []
                                    }
                                
                                # Analyze access data
                                access = account.get("access", {})
                                
                                # Get users
                                users_connection = access.get("users", {})
                                if users_connection:
                                    users_edges = users_connection.get("edges", [])
                                    total_count = users_connection.get("totalCount")
                                    
                                    print(f"    Users found: {len(users_edges)}")
                                    if total_count is not None:
                                        print(f"    Total users: {total_count}")
                                    
                                    for user_edge in users_edges:
                                        user = user_edge.get("node", {})
                                        if user:
                                            user_id = user.get("id")
                                            name = user.get("name", "Unknown")
                                            email = user.get("email")
                                            role = user.get("role")
                                            is_owner = user.get("isOwner")
                                            is_primary = user.get("isPrimary")
                                            is_admin = user.get("isAdmin")
                                            
                                            print(f"      User: {name}")
                                            print(f"        ID: {user_id}")
                                            if email:
                                                print(f"        ✅ Email: {email}")
                                            else:
                                                print(f"        ❌ Email: None")
                                            
                                            if role:
                                                print(f"        Role: {role}")
                                            if is_owner is not None:
                                                print(f"        Is Owner: {is_owner}")
                                            if is_primary is not None:
                                                print(f"        Is Primary: {is_primary}")
                                            if is_admin is not None:
                                                print(f"        Is Admin: {is_admin}")
                                            
                                            # Store user data
                                            user_data = {
                                                "id": user_id,
                                                "name": name,
                                                "email": email,
                                                "role": role,
                                                "isOwner": is_owner,
                                                "isPrimary": is_primary,
                                                "isAdmin": is_admin
                                            }
                                            
                                            # Avoid duplicates
                                            if user_data not in contact_data[account_id]["users"]:
                                                contact_data[account_id]["users"].append(user_data)
                                
                                # Get pending users
                                pending_users_connection = access.get("pendingUsers", {})
                                if pending_users_connection:
                                    pending_edges = pending_users_connection.get("edges", [])
                                    
                                    print(f"    Pending users found: {len(pending_edges)}")
                                    
                                    for pending_edge in pending_edges:
                                        pending_user = pending_edge.get("node", {})
                                        if pending_user:
                                            name = pending_user.get("name", "Unknown")
                                            email = pending_user.get("email")
                                            role = pending_user.get("role")
                                            
                                            print(f"      Pending User: {name}")
                                            if email:
                                                print(f"        ✅ Email: {email}")
                                            if role:
                                                print(f"        Role: {role}")
                                            
                                            # Store pending user data
                                            pending_data = {
                                                "name": name,
                                                "email": email,
                                                "role": role
                                            }
                                            
                                            # Avoid duplicates
                                            if pending_data not in contact_data[account_id]["pendingUsers"]:
                                                contact_data[account_id]["pendingUsers"].append(pending_data)
                        else:
                            print("❌ No account data returned")
                else:
                    print(f"❌ HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            print("-" * 60)
        
        # Test introspection on User types
        await introspect_user_types(client, config, headers)
        
        # Summary and recommendations
        print_user_contact_summary(contact_data)


async def introspect_user_types(client, config, headers):
    """Use GraphQL introspection to discover User type fields."""
    
    print(f"\n{'='*60}")
    print("GRAPHQL INTROSPECTION - USER TYPES")
    print(f"{'='*60}")
    
    # Try different possible user type names
    user_types = ["User", "AccountUser", "AccountAccessUser", "PendingUser"]
    
    for type_name in user_types:
        print(f"\n--- {type_name} Type ---")
        
        introspection_query = f"""
        query {{
            __type(name: "{type_name}") {{
                name
                fields {{
                    name
                    type {{
                        name
                        kind
                        ofType {{
                            name
                            kind
                        }}
                    }}
                    description
                }}
            }}
        }}
        """
        
        try:
            response = await client.post(
                config.syb_api_url,
                json={"query": introspection_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    type_info = data["data"].get("__type")
                    if type_info:
                        fields = type_info.get("fields", [])
                        print(f"✅ {type_name} type has {len(fields)} fields:")
                        
                        contact_fields = []
                        for field in fields:
                            field_name = field.get("name", "")
                            field_type = field.get("type", {})
                            type_name_str = field_type.get("name") or field_type.get("ofType", {}).get("name", "")
                            description = field.get("description", "")
                            
                            print(f"  - {field_name}: {type_name_str}")
                            if description:
                                print(f"    Description: {description}")
                            
                            # Track contact-related fields
                            contact_keywords = ["email", "contact", "owner", "admin", "primary", "role", "name", "phone"]
                            if any(keyword in field_name.lower() for keyword in contact_keywords):
                                contact_fields.append(field_name)
                        
                        if contact_fields:
                            print(f"\n🎯 Contact-related fields in {type_name}:")
                            for field in contact_fields:
                                print(f"  - {field}")
                    else:
                        print(f"❌ {type_name} type not found")
                
        except Exception as e:
            print(f"❌ Introspection of {type_name} failed: {e}")


def print_user_contact_summary(contact_data):
    """Print summary of user contact findings."""
    
    print(f"\n{'='*60}")
    print("USER CONTACT INFORMATION SUMMARY")
    print(f"{'='*60}")
    
    total_accounts = len(contact_data)
    accounts_with_users = 0
    total_users = 0
    users_with_email = 0
    owner_users = 0
    admin_users = 0
    
    print(f"📊 Contact Analysis Results:")
    print(f"  Total accounts analyzed: {total_accounts}")
    
    if contact_data:
        print(f"\n🏨 Detailed User Analysis:")
        
        for account_id, data in contact_data.items():
            business_name = data["businessName"]
            users = data.get("users", [])
            pending_users = data.get("pendingUsers", [])
            
            print(f"\n  Account: {business_name}")
            print(f"  ID: {account_id}")
            
            if users:
                accounts_with_users += 1
                total_users += len(users)
                
                print(f"    Active Users: {len(users)}")
                
                contact_emails = []
                for user in users:
                    name = user.get("name", "Unknown")
                    email = user.get("email")
                    role = user.get("role", "unknown")
                    is_owner = user.get("isOwner", False)
                    is_admin = user.get("isAdmin", False)
                    
                    if email:
                        users_with_email += 1
                        contact_emails.append(email)
                        
                        role_desc = []
                        if is_owner:
                            role_desc.append("Owner")
                            owner_users += 1
                        if is_admin:
                            role_desc.append("Admin")
                            admin_users += 1
                        if role:
                            role_desc.append(role)
                        
                        role_str = " & ".join(role_desc) if role_desc else "User"
                        print(f"      ✅ {name} ({role_str}): {email}")
                    else:
                        print(f"      ❌ {name} ({role}): No email")
                
                if contact_emails:
                    print(f"    📧 Contact emails available: {len(contact_emails)}")
                else:
                    print(f"    ❌ No contact emails found")
                    
            else:
                print(f"    Active Users: 0")
            
            if pending_users:
                print(f"    Pending Users: {len(pending_users)}")
                for pending in pending_users:
                    name = pending.get("name", "Unknown")
                    email = pending.get("email")
                    role = pending.get("role", "unknown")
                    if email:
                        print(f"      📧 {name} ({role}): {email}")
            else:
                print(f"    Pending Users: 0")
    
    print(f"\n📊 Summary Statistics:")
    print(f"  Accounts with users: {accounts_with_users}/{total_accounts}")
    print(f"  Total users found: {total_users}")
    print(f"  Users with email: {users_with_email}/{total_users}")
    print(f"  Owner users: {owner_users}")
    print(f"  Admin users: {admin_users}")
    
    print(f"\n💡 NOTIFICATION SYSTEM ASSESSMENT:")
    
    if users_with_email > 0:
        print(f"🎉 EXCELLENT NEWS! Contact information IS available!")
        print(f"✅ The SYB API provides access to account users with email addresses")
        print(f"✅ You CAN build the targeted notification system!")
        
        print(f"\n🎯 Implementation Recommendations:")
        print(f"  1. ✅ Use access.users to get account contacts")
        print(f"  2. ✅ Filter users by role (owners, admins) for priority notifications")
        print(f"  3. ✅ Build notification selection UI with account/user checkboxes")
        print(f"  4. ✅ Send targeted status reports to selected contacts")
        
        print(f"\n📧 Email Notification Strategy:")
        print(f"  - Send to account owners for critical issues")
        print(f"  - Send to admins for operational updates")
        print(f"  - Allow manual selection of specific users")
        print(f"  - Group by account for targeted reports")
        
        # Generate working query
        working_query = """
query GetAccountContacts {
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
                                        role
                                        isOwner
                                        isPrimary
                                    }
                                }
                                totalCount
                            }
                        }
                        soundZones(first: 1) {
                            totalCount
                        }
                    }
                }
            }
        }
    }
}
"""
        
        print(f"\n📋 Working GraphQL Query:")
        print(working_query)
        
        print(f"\n🚀 Next Steps:")
        print(f"  1. Implement contact retrieval using the working query above")
        print(f"  2. Create notification UI with account/user selection")
        print(f"  3. Integrate with existing zone monitoring")
        print(f"  4. Build email templates for different notification types")
        print(f"  5. Test with real account data")
        
    else:
        print(f"❌ No user email addresses found")
        print(f"  The users exist but don't have email addresses in the API")
        print(f"  Alternative approaches:")
        print(f"    1. Contact SYB support about email access permissions")
        print(f"    2. Store contact info in local database")
        print(f"    3. Use business names for manual contact lookup")


async def create_working_contact_query_test():
    """Create and test a working query for getting account contacts."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print("TESTING FINAL WORKING CONTACT QUERY")
    print(f"{'='*60}")
    
    # The query that should work based on our exploration
    final_query = """
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
                                        }
                                    }
                                    totalCount
                                }
                            }
                            soundZones(first: 1) {
                                totalCount
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
            print("Executing final working query...")
            
            response = await client.post(
                config.syb_api_url,
                json={"query": final_query},
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ Errors in final query:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', str(error))}")
                    return False
                
                if "data" in data and data["data"]:
                    me_data = data["data"].get("me", {})
                    accounts_data = me_data.get("accounts", {})
                    account_edges = accounts_data.get("edges", [])
                    
                    print(f"✅ SUCCESS! Retrieved {len(account_edges)} accounts with contact data")
                    
                    notification_targets = []
                    
                    for edge in account_edges:
                        account = edge.get("node", {})
                        account_id = account.get("id")
                        business_name = account.get("businessName", "Unknown")
                        zone_count = account.get("soundZones", {}).get("totalCount", 0)
                        
                        access = account.get("access", {})
                        users_connection = access.get("users", {})
                        users_edges = users_connection.get("edges", [])
                        total_users = users_connection.get("totalCount", 0)
                        
                        print(f"\n📊 {business_name}")
                        print(f"  Zones: {zone_count}")
                        print(f"  Users: {total_users}")
                        
                        account_contacts = []
                        for user_edge in users_edges:
                            user = user_edge.get("node", {})
                            name = user.get("name")
                            email = user.get("email")
                            
                            if email:
                                print(f"    📧 {name}: {email}")
                                account_contacts.append({
                                    "name": name,
                                    "email": email
                                })
                        
                        if account_contacts:
                            notification_targets.append({
                                "account_id": account_id,
                                "business_name": business_name,
                                "zone_count": zone_count,
                                "contacts": account_contacts
                            })
                    
                    print(f"\n🎯 NOTIFICATION SYSTEM SUMMARY:")
                    print(f"  Total accounts: {len(account_edges)}")
                    print(f"  Accounts with contacts: {len(notification_targets)}")
                    
                    total_contacts = sum(len(target["contacts"]) for target in notification_targets)
                    print(f"  Total contact emails: {total_contacts}")
                    
                    if notification_targets:
                        print(f"\n✅ READY TO IMPLEMENT NOTIFICATION SYSTEM!")
                        print(f"  You can now:")
                        print(f"    - Get account contact information")
                        print(f"    - Send targeted notifications by account")
                        print(f"    - Build selection UI for specific accounts/contacts")
                        
                        # Save the working data structure for implementation
                        output_file = "account_contacts.json"
                        with open(output_file, "w") as f:
                            json.dump(notification_targets, f, indent=2)
                        print(f"  📁 Sample contact data saved to: {output_file}")
                    
                    return True
                else:
                    print("❌ No data returned")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False


if __name__ == "__main__":
    print("SYB Access Users Contact Information Explorer")
    print("Deep dive into user contact information for notification system")
    print("="*80)
    
    asyncio.run(explore_access_users())
    asyncio.run(create_working_contact_query_test())