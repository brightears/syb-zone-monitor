#!/usr/bin/env python3
"""Find the account creator/owner by exploring all possible relationships."""

import asyncio
import json
from datetime import datetime
import httpx
from config import Config


async def find_account_creator():
    """Explore all possible ways to find who created/owns each account."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Finding Account Creator/Owner Information")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # First, let's check what queries are available at root level
        await check_root_queries(client, config, headers)
        
        # Check if we can query users and their accounts
        await check_user_account_relationship(client, config, headers)
        
        # Check access field in more detail
        await deep_dive_access_field(client, config, headers)
        
        # Check if subscription has owner info
        await check_subscription_info(client, config, headers)
        
        # Check plan field for owner info
        await check_plan_info(client, config, headers)


async def check_root_queries(client, config, headers):
    """Check what root queries are available."""
    
    print("\n1. CHECKING ROOT QUERY CAPABILITIES")
    print("-"*60)
    
    root_introspection = """
    query {
        __schema {
            queryType {
                fields {
                    name
                    description
                    type {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    try:
        response = await client.post(
            config.syb_api_url,
            json={"query": root_introspection},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "data" in data and data["data"]:
                query_fields = data["data"]["__schema"]["queryType"]["fields"]
                
                print(f"✅ Found {len(query_fields)} root queries:")
                
                # Look for user-related queries
                user_queries = []
                for field in query_fields:
                    name = field["name"]
                    if any(term in name.lower() for term in ["user", "viewer", "me", "account", "creator"]):
                        user_queries.append(field)
                        print(f"  - {name}: {field.get('description', '')}")
                
                print(f"\n🎯 Found {len(user_queries)} potentially relevant queries")
                
    except Exception as e:
        print(f"❌ Root introspection failed: {e}")


async def check_user_account_relationship(client, config, headers):
    """Check if we can query users and see their accounts."""
    
    print("\n\n2. CHECKING USER->ACCOUNT RELATIONSHIP")
    print("-"*60)
    
    # First try to get current user info
    me_queries = [
        {
            "name": "Me with accounts",
            "query": """
            {
                me {
                    __typename
                    ... on User {
                        id
                        name
                        email
                        accounts {
                            edges {
                                node {
                                    id
                                    businessName
                                }
                            }
                        }
                    }
                    ... on PublicAPIClient {
                        id
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
        },
        {
            "name": "Viewer query",
            "query": """
            {
                viewer {
                    __typename
                    ... on User {
                        id
                        name
                        email
                        accounts {
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
        }
    ]
    
    for query_info in me_queries:
        print(f"\nTesting: {query_info['name']}")
        
        try:
            response = await client.post(
                config.syb_api_url,
                json={"query": query_info["query"]},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    for error in data["errors"]:
                        print(f"  ❌ {error.get('message')}")
                
                if "data" in data and data["data"]:
                    result = data["data"]
                    print(f"  ✅ Result: {json.dumps(result, indent=2)}")
                    
        except Exception as e:
            print(f"  ❌ Failed: {e}")


async def deep_dive_access_field(client, config, headers):
    """Deep dive into the access field to understand user relationships."""
    
    print("\n\n3. DEEP DIVE INTO ACCESS FIELD")
    print("-"*60)
    
    # First introspect the Access type
    access_introspection = """
    query {
        __type(name: "Access") {
            name
            description
            fields {
                name
                description
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    try:
        response = await client.post(
            config.syb_api_url,
            json={"query": access_introspection},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "data" in data and data["data"]:
                access_type = data["data"].get("__type")
                if access_type:
                    fields = access_type.get("fields", [])
                    print(f"✅ Access type has {len(fields)} fields:")
                    
                    for field in fields:
                        name = field["name"]
                        desc = field.get("description", "")
                        print(f"  - {name}: {desc}")
                        
                        # Check for owner/creator related fields
                        if any(term in name.lower() for term in ["owner", "creator", "admin", "primary"]):
                            print(f"    🎯 This might indicate ownership!")
                    
                    # Now test access field with all sub-fields
                    await test_access_details(client, config, headers)
                    
    except Exception as e:
        print(f"❌ Access introspection failed: {e}")


async def test_access_details(client, config, headers):
    """Test access field in detail to find ownership info."""
    
    print("\n  Testing detailed access query...")
    
    detailed_access_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 10) {
                    edges {
                        node {
                            id
                            businessName
                            createdAt
                            access {
                                # Try to get owner/creator info
                                owner {
                                    id
                                    name
                                    email
                                }
                                creator {
                                    id
                                    name
                                    email
                                }
                                primaryUser {
                                    id
                                    name
                                    email
                                }
                                administrator {
                                    id
                                    name
                                    email
                                }
                                
                                # Get all users with details
                                users(first: 20) {
                                    edges {
                                        node {
                                            id
                                            name
                                            email
                                            companyRole
                                            createdAt
                                            updatedAt
                                            # Try additional fields
                                            isOwner
                                            isCreator
                                            isAdmin
                                            isPrimary
                                            role
                                            permissions
                                        }
                                    }
                                }
                                
                                # Check if there's a separate owners list
                                owners {
                                    edges {
                                        node {
                                            id
                                            name
                                            email
                                        }
                                    }
                                }
                                
                                # Try user count
                                userCount
                                totalUsers
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    try:
        response = await client.post(
            config.syb_api_url,
            json={"query": detailed_access_query},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Log which fields don't exist
            if "errors" in data:
                print("\n  Fields that don't exist in access:")
                for error in data["errors"]:
                    message = error.get('message', '')
                    if "Cannot query field" in message:
                        field = message.split('"')[1] if '"' in message else "unknown"
                        print(f"    - {field}")
            
            # Process data
            if "data" in data and data["data"]:
                accounts = data["data"]["me"]["accounts"]["edges"]
                
                print(f"\n  ✅ Analyzing {len(accounts)} accounts for ownership patterns...")
                
                # Analyze user patterns
                ownership_patterns = []
                
                for edge in accounts:
                    account = edge["node"]
                    business_name = account["businessName"]
                    created_at = account.get("createdAt")
                    access = account.get("access", {})
                    
                    if access:
                        users = access.get("users", {}).get("edges", [])
                        
                        if users:
                            print(f"\n  📍 {business_name}")
                            print(f"     Created: {created_at}")
                            
                            # Find the earliest user (likely the creator)
                            earliest_user = None
                            for user_edge in users:
                                user = user_edge["node"]
                                user_created = user.get("createdAt")
                                
                                if user_created:
                                    if not earliest_user or user_created < earliest_user.get("createdAt", ""):
                                        earliest_user = user
                            
                            if earliest_user:
                                print(f"     Earliest user: {earliest_user.get('name')} ({earliest_user.get('email')})")
                                print(f"     User created: {earliest_user.get('createdAt')}")
                                
                                ownership_patterns.append({
                                    "account": business_name,
                                    "account_created": created_at,
                                    "likely_creator": {
                                        "name": earliest_user.get("name"),
                                        "email": earliest_user.get("email"),
                                        "created": earliest_user.get("createdAt")
                                    },
                                    "total_users": len(users)
                                })
                
                # Save findings
                if ownership_patterns:
                    with open("account_ownership_patterns.json", "w") as f:
                        json.dump({
                            "timestamp": datetime.now().isoformat(),
                            "patterns": ownership_patterns
                        }, f, indent=2)
                    print(f"\n  💾 Ownership patterns saved to account_ownership_patterns.json")
                    
    except Exception as e:
        print(f"  ❌ Detailed access query failed: {e}")


async def check_subscription_info(client, config, headers):
    """Check if subscription contains owner information."""
    
    print("\n\n4. CHECKING SUBSCRIPTION FOR OWNER INFO")
    print("-"*60)
    
    subscription_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 5) {
                    edges {
                        node {
                            id
                            businessName
                            plan {
                                name
                                description
                            }
                            billing {
                                subscription {
                                    status
                                    currentPeriodStart
                                    currentPeriodEnd
                                    # Try owner fields
                                    owner {
                                        id
                                        name
                                        email
                                    }
                                    createdBy {
                                        id
                                        name
                                        email
                                    }
                                    customer {
                                        id
                                        name
                                        email
                                    }
                                    contact {
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
    """
    
    try:
        response = await client.post(
            config.syb_api_url,
            json={"query": subscription_query},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print("  Fields that don't exist in subscription:")
                for error in data["errors"]:
                    message = error.get('message', '')
                    if "Cannot query field" in message:
                        field = message.split('"')[1] if '"' in message else "unknown"
                        print(f"    - {field}")
            
            if "data" in data and data["data"]:
                accounts = data["data"]["me"]["accounts"]["edges"]
                
                for edge in accounts:
                    account = edge["node"]
                    business_name = account["businessName"]
                    plan = account.get("plan")
                    billing = account.get("billing", {})
                    subscription = billing.get("subscription") if billing else None
                    
                    print(f"\n  {business_name}:")
                    if plan:
                        print(f"    Plan: {plan.get('name')}")
                    if subscription:
                        print(f"    Subscription: {json.dumps(subscription, indent=6)}")
                        
    except Exception as e:
        print(f"❌ Subscription query failed: {e}")


async def check_plan_info(client, config, headers):
    """Check if plan contains owner information."""
    
    print("\n\n5. ANALYZING ACCOUNT CREATION PATTERNS")
    print("-"*60)
    
    # Get accounts with all available data to find patterns
    pattern_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 50) {
                    edges {
                        node {
                            id
                            businessName
                            createdAt
                            country
                            businessType
                            access {
                                users(first: 20) {
                                    edges {
                                        node {
                                            id
                                            name
                                            email
                                            companyRole
                                            createdAt
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
    
    try:
        response = await client.post(
            config.syb_api_url,
            json={"query": pattern_query},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "data" in data and data["data"]:
                accounts = data["data"]["me"]["accounts"]["edges"]
                
                print(f"✅ Analyzing {len(accounts)} accounts...")
                
                # Statistics
                total_accounts = len(accounts)
                accounts_with_users = 0
                accounts_with_pending = 0
                accounts_with_no_contacts = 0
                
                all_contacts = []
                
                for edge in accounts:
                    account = edge["node"]
                    business_name = account["businessName"]
                    access = account.get("access", {})
                    
                    users = access.get("users", {}).get("edges", []) if access else []
                    pending_users = access.get("pendingUsers", {}).get("edges", []) if access else []
                    
                    if users:
                        accounts_with_users += 1
                    if pending_users:
                        accounts_with_pending += 1
                    if not users and not pending_users:
                        accounts_with_no_contacts += 1
                        print(f"\n  ⚠️ No contacts found for: {business_name}")
                    
                    # Collect all contacts
                    for user_edge in users:
                        user = user_edge["node"]
                        all_contacts.append({
                            "account": business_name,
                            "type": "active",
                            "name": user.get("name"),
                            "email": user.get("email"),
                            "role": user.get("companyRole"),
                            "created": user.get("createdAt")
                        })
                    
                    for pending_edge in pending_users:
                        pending = pending_edge["node"]
                        all_contacts.append({
                            "account": business_name,
                            "type": "pending",
                            "email": pending.get("email")
                        })
                
                # Summary
                print(f"\n📊 FINAL ANALYSIS:")
                print(f"  Total accounts: {total_accounts}")
                print(f"  Accounts with active users: {accounts_with_users} ({accounts_with_users/total_accounts*100:.1f}%)")
                print(f"  Accounts with pending users: {accounts_with_pending} ({accounts_with_pending/total_accounts*100:.1f}%)")
                print(f"  Accounts with NO contacts: {accounts_with_no_contacts} ({accounts_with_no_contacts/total_accounts*100:.1f}%)")
                print(f"  Total contacts found: {len(all_contacts)}")
                
                # Save comprehensive results
                results = {
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "total_accounts": total_accounts,
                        "accounts_with_active_users": accounts_with_users,
                        "accounts_with_pending_users": accounts_with_pending,
                        "accounts_with_no_contacts": accounts_with_no_contacts,
                        "total_contacts": len(all_contacts)
                    },
                    "contacts": all_contacts
                }
                
                with open("comprehensive_contact_analysis.json", "w") as f:
                    json.dump(results, f, indent=2)
                print(f"\n💾 Comprehensive analysis saved to comprehensive_contact_analysis.json")
                
    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")


if __name__ == "__main__":
    print("SYB Account Creator/Owner Discovery")
    print("Finding the primary account owner for all accounts")
    print("="*80)
    
    asyncio.run(find_account_creator())