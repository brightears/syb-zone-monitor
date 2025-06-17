#!/usr/bin/env python3
"""Deep introspection of the SYB GraphQL API to find ALL account fields including owner/creator info."""

import asyncio
import json
from datetime import datetime
import httpx
from config import Config


async def deep_introspect_account_type():
    """Perform deep introspection to find all Account type fields."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Deep Account Type Introspection")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # 1. Full introspection of Account type
        print("\n1. COMPLETE ACCOUNT TYPE SCHEMA")
        print("-"*60)
        
        account_introspection = """
        query {
            __type(name: "Account") {
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
                            ofType {
                                name
                                kind
                            }
                        }
                    }
                    args {
                        name
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
                json={"query": account_introspection},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    account_type = data["data"].get("__type")
                    if account_type:
                        fields = account_type.get("fields", [])
                        print(f"✅ Account type has {len(fields)} fields:\n")
                        
                        # Categorize fields
                        contact_fields = []
                        owner_fields = []
                        user_fields = []
                        billing_fields = []
                        metadata_fields = []
                        other_fields = []
                        
                        for field in fields:
                            field_name = field.get("name", "")
                            field_type = field.get("type", {})
                            type_name = field_type.get("name") or field_type.get("ofType", {}).get("name", "")
                            description = field.get("description", "")
                            
                            # Categorize by name
                            lower_name = field_name.lower()
                            if any(term in lower_name for term in ["email", "contact", "phone", "address"]):
                                contact_fields.append((field_name, type_name, description))
                            elif any(term in lower_name for term in ["owner", "creator", "admin", "primary"]):
                                owner_fields.append((field_name, type_name, description))
                            elif any(term in lower_name for term in ["user", "member", "team", "staff", "access"]):
                                user_fields.append((field_name, type_name, description))
                            elif any(term in lower_name for term in ["billing", "payment", "invoice", "subscription"]):
                                billing_fields.append((field_name, type_name, description))
                            elif any(term in lower_name for term in ["created", "updated", "meta", "modified"]):
                                metadata_fields.append((field_name, type_name, description))
                            else:
                                other_fields.append((field_name, type_name, description))
                        
                        # Print categorized fields
                        print("📧 CONTACT FIELDS:")
                        if contact_fields:
                            for name, type_name, desc in contact_fields:
                                print(f"  - {name}: {type_name}")
                                if desc:
                                    print(f"    Description: {desc}")
                        else:
                            print("  None found")
                        
                        print("\n👤 OWNER/CREATOR FIELDS:")
                        if owner_fields:
                            for name, type_name, desc in owner_fields:
                                print(f"  - {name}: {type_name}")
                                if desc:
                                    print(f"    Description: {desc}")
                        else:
                            print("  None found")
                        
                        print("\n👥 USER/MEMBER FIELDS:")
                        if user_fields:
                            for name, type_name, desc in user_fields:
                                print(f"  - {name}: {type_name}")
                                if desc:
                                    print(f"    Description: {desc}")
                        else:
                            print("  None found")
                        
                        print("\n💳 BILLING FIELDS:")
                        if billing_fields:
                            for name, type_name, desc in billing_fields:
                                print(f"  - {name}: {type_name}")
                                if desc:
                                    print(f"    Description: {desc}")
                        else:
                            print("  None found")
                        
                        print("\n📅 METADATA FIELDS:")
                        if metadata_fields:
                            for name, type_name, desc in metadata_fields:
                                print(f"  - {name}: {type_name}")
                                if desc:
                                    print(f"    Description: {desc}")
                        else:
                            print("  None found")
                        
                        print("\n📦 OTHER FIELDS:")
                        if other_fields:
                            for name, type_name, desc in other_fields[:10]:  # Show first 10
                                print(f"  - {name}: {type_name}")
                                if desc:
                                    print(f"    Description: {desc}")
                            if len(other_fields) > 10:
                                print(f"  ... and {len(other_fields) - 10} more fields")
                        else:
                            print("  None found")
                        
                        # Save all fields for reference
                        all_fields = {
                            "timestamp": datetime.now().isoformat(),
                            "total_fields": len(fields),
                            "contact_fields": contact_fields,
                            "owner_fields": owner_fields,
                            "user_fields": user_fields,
                            "billing_fields": billing_fields,
                            "metadata_fields": metadata_fields,
                            "all_fields": [
                                {
                                    "name": f.get("name"),
                                    "type": f.get("type", {}).get("name") or f.get("type", {}).get("ofType", {}).get("name"),
                                    "description": f.get("description")
                                }
                                for f in fields
                            ]
                        }
                        
                        with open("account_schema_full.json", "w") as f:
                            json.dump(all_fields, f, indent=2)
                        print("\n💾 Full schema saved to account_schema_full.json")
                        
                        # Test promising fields
                        await test_promising_fields(client, config, headers, owner_fields, user_fields, billing_fields)
                        
                else:
                    print("❌ No errors in response:")
                    for error in data.get("errors", []):
                        print(f"  - {error.get('message')}")
                        
        except Exception as e:
            print(f"❌ Introspection failed: {e}")


async def test_promising_fields(client, config, headers, owner_fields, user_fields, billing_fields):
    """Test the most promising fields for finding account owner info."""
    
    print("\n\n2. TESTING PROMISING FIELDS")
    print("-"*60)
    
    # Combine all promising field names
    promising_fields = []
    for fields_list in [owner_fields, user_fields, billing_fields]:
        promising_fields.extend([f[0] for f in fields_list])
    
    # Also add some common field names that might exist
    common_fields = [
        "owner", "creator", "createdBy", "accountOwner", "primaryUser",
        "admin", "administrator", "primaryContact", "mainContact",
        "billing", "billingContact", "accountContact", "registeredBy",
        "access", "users", "members", "team", "staff"
    ]
    
    # Combine and deduplicate
    all_test_fields = list(set(promising_fields + common_fields))
    
    # Test each field individually
    print(f"\nTesting {len(all_test_fields)} potential fields individually...")
    
    working_fields = []
    
    for field_name in all_test_fields:
        query = f"""
        {{
            me {{
                ... on PublicAPIClient {{
                    accounts(first: 1) {{
                        edges {{
                            node {{
                                id
                                businessName
                                {field_name}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        
        try:
            response = await client.post(
                config.syb_api_url,
                json={"query": query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" not in data and "data" in data:
                    # Field exists!
                    accounts = data["data"]["me"]["accounts"]["edges"]
                    if accounts and accounts[0]["node"].get(field_name) is not None:
                        print(f"✅ {field_name} - WORKS and has data!")
                        working_fields.append(field_name)
                    else:
                        print(f"⚠️  {field_name} - exists but is null/empty")
                else:
                    # Field doesn't exist
                    pass
                    
        except Exception as e:
            pass
    
    print(f"\n🎯 Working fields with data: {working_fields}")
    
    # Now test these working fields together on multiple accounts
    if working_fields:
        await test_working_fields_on_accounts(client, config, headers, working_fields)


async def test_working_fields_on_accounts(client, config, headers, working_fields):
    """Test working fields on multiple accounts to find contact info."""
    
    print("\n\n3. TESTING WORKING FIELDS ON MULTIPLE ACCOUNTS")
    print("-"*60)
    
    # Build query with all working fields
    fields_query = "\n".join([f"                        {field}" for field in working_fields])
    
    query = f"""
    {{
        me {{
            ... on PublicAPIClient {{
                accounts(first: 20) {{
                    edges {{
                        node {{
                            id
                            businessName
{fields_query}
                        }}
                    }}
                }}
            }}
        }}
    }}
    """
    
    print(f"Testing {len(working_fields)} working fields on 20 accounts...")
    
    try:
        response = await client.post(
            config.syb_api_url,
            json={"query": query},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "data" in data and data["data"]:
                accounts = data["data"]["me"]["accounts"]["edges"]
                
                print(f"\n✅ Retrieved {len(accounts)} accounts")
                
                # Analyze results
                accounts_with_owner_info = 0
                owner_info_summary = []
                
                for edge in accounts:
                    account = edge["node"]
                    business_name = account.get("businessName", "Unknown")
                    account_id = account.get("id")
                    
                    # Check each working field for owner/contact info
                    owner_info = {}
                    for field in working_fields:
                        value = account.get(field)
                        if value:
                            owner_info[field] = value
                    
                    if owner_info:
                        accounts_with_owner_info += 1
                        owner_info_summary.append({
                            "account_id": account_id,
                            "business_name": business_name,
                            "owner_fields": owner_info
                        })
                        
                        print(f"\n📍 {business_name}")
                        for field, value in owner_info.items():
                            print(f"  {field}: {json.dumps(value, indent=4)}")
                
                # Summary
                print(f"\n📊 OWNER INFO SUMMARY:")
                print(f"  Total accounts checked: {len(accounts)}")
                print(f"  Accounts with owner info: {accounts_with_owner_info}")
                print(f"  Percentage with owner info: {(accounts_with_owner_info/len(accounts)*100):.1f}%")
                
                # Save detailed results
                results = {
                    "timestamp": datetime.now().isoformat(),
                    "total_accounts": len(accounts),
                    "accounts_with_owner_info": accounts_with_owner_info,
                    "working_fields": working_fields,
                    "accounts": owner_info_summary
                }
                
                with open("account_owner_discovery.json", "w") as f:
                    json.dump(results, f, indent=2)
                print(f"\n💾 Detailed results saved to account_owner_discovery.json")
                
            else:
                print("❌ No data in response")
                
    except Exception as e:
        print(f"❌ Failed to test working fields: {e}")


async def test_nested_fields():
    """Test nested fields that might contain owner information."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("\n\n4. TESTING NESTED OWNER FIELDS")
    print("-"*60)
    
    # Test various nested structures
    nested_tests = [
        {
            "name": "Nested owner object",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    owner {
                                        id
                                        name
                                        email
                                        phone
                                        role
                                        createdAt
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
            "name": "Creator field",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    creator {
                                        id
                                        name
                                        email
                                    }
                                    createdBy {
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
            """
        },
        {
            "name": "Admin/Administrator fields",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    admin {
                                        id
                                        name
                                        email
                                    }
                                    administrator {
                                        id
                                        name
                                        email
                                    }
                                    administrators {
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
            """
        },
        {
            "name": "Primary contact/user",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    primaryContact {
                                        id
                                        name
                                        email
                                    }
                                    primaryUser {
                                        id
                                        name
                                        email
                                    }
                                    mainContact {
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
            """
        }
    ]
    
    async with httpx.AsyncClient(timeout=30) as client:
        for test in nested_tests:
            print(f"\nTesting: {test['name']}")
            
            try:
                response = await client.post(
                    config.syb_api_url,
                    json={"query": test["query"]},
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" in data:
                        # Extract which fields don't exist
                        for error in data["errors"]:
                            message = error.get('message', '')
                            if "Cannot query field" in message:
                                field = message.split('"')[1] if '"' in message else "unknown"
                                print(f"  ❌ Field '{field}' does not exist")
                    
                    if "data" in data and data["data"]:
                        accounts = data["data"]["me"]["accounts"]["edges"]
                        if accounts:
                            print(f"  ✅ Query succeeded! Checking for data...")
                            for edge in accounts:
                                account = edge["node"]
                                for key, value in account.items():
                                    if key not in ["id", "businessName"] and value:
                                        print(f"  ✅ Found {key}: {json.dumps(value, indent=4)}")
                            
            except Exception as e:
                print(f"  ❌ Request failed: {e}")


async def check_user_query():
    """Check if we can query users directly to find account owners."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("\n\n5. CHECKING USER QUERY FOR ACCOUNT OWNERSHIP")
    print("-"*60)
    
    # First, introspect the User type
    user_introspection = """
    query {
        __type(name: "User") {
            name
            fields {
                name
                type {
                    name
                    kind
                }
                description
            }
        }
    }
    """
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                config.syb_api_url,
                json={"query": user_introspection},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    user_type = data["data"].get("__type")
                    if user_type:
                        fields = user_type.get("fields", [])
                        print(f"✅ User type has {len(fields)} fields:")
                        
                        account_related = []
                        for field in fields:
                            field_name = field.get("name", "")
                            if any(term in field_name.lower() for term in ["account", "owner", "admin", "role"]):
                                account_related.append(field_name)
                                print(f"  - {field_name}: {field.get('type', {}).get('name')}")
                        
                        if account_related:
                            print(f"\n🎯 Found {len(account_related)} account-related fields on User type")
                        
        except Exception as e:
            print(f"❌ User introspection failed: {e}")


if __name__ == "__main__":
    print("SYB GraphQL API - Deep Account Introspection")
    print("Finding ALL available fields for account owner/creator information")
    print("="*80)
    
    asyncio.run(deep_introspect_account_type())
    asyncio.run(test_nested_fields())
    asyncio.run(check_user_query())