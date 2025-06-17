#!/usr/bin/env python3
"""Explore billing and access fields for account contact information."""

import asyncio
import json
from datetime import datetime

import httpx
from config import Config


async def explore_billing_and_access():
    """Investigate billing and access fields for contact information."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Exploring Billing and Access Fields for Contact Info")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # Test billing and access fields
    field_tests = [
        {
            "name": "Billing Field Exploration",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    billing {
                                        contact
                                        contactEmail
                                        email
                                        billingEmail
                                        invoiceEmail
                                        name
                                        address
                                        company
                                        phone
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
            "name": "Access Field Exploration",
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
                                            id
                                            name
                                            email
                                            role
                                            isOwner
                                            isPrimary
                                        }
                                        members {
                                            id
                                            name
                                            email
                                            role
                                        }
                                        owners {
                                            id
                                            name
                                            email
                                        }
                                        admins {
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
            """
        },
        {
            "name": "Settings Field Exploration",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    settings {
                                        contactEmail
                                        notificationEmail
                                        alertEmail
                                        adminEmail
                                        ownerEmail
                                        billingEmail
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
            "name": "Basic Billing Structure",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 2) {
                            edges {
                                node {
                                    id
                                    businessName
                                    billing {
                                        __typename
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
            "name": "Basic Access Structure", 
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 2) {
                            edges {
                                node {
                                    id
                                    businessName
                                    access {
                                        __typename
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
        working_fields = []
        contact_data = {}
        
        for i, test in enumerate(field_tests):
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
                                
                                # Analyze billing data
                                billing = account.get("billing")
                                if billing:
                                    print(f"    ✅ Billing data found:")
                                    print(json.dumps(billing, indent=6))
                                    
                                    # Store any contact info found
                                    if account_id not in contact_data:
                                        contact_data[account_id] = {
                                            "businessName": business_name,
                                            "billing": billing,
                                            "access": None
                                        }
                                    else:
                                        contact_data[account_id]["billing"] = billing
                                
                                # Analyze access data
                                access = account.get("access")
                                if access:
                                    print(f"    ✅ Access data found:")
                                    print(json.dumps(access, indent=6))
                                    
                                    # Store access info
                                    if account_id not in contact_data:
                                        contact_data[account_id] = {
                                            "businessName": business_name,
                                            "billing": None,
                                            "access": access
                                        }
                                    else:
                                        contact_data[account_id]["access"] = access
                                
                                # Analyze settings data
                                settings = account.get("settings")
                                if settings:
                                    print(f"    ✅ Settings data found:")
                                    print(json.dumps(settings, indent=6))
                                    
                                    # Store settings info
                                    if account_id not in contact_data:
                                        contact_data[account_id] = {
                                            "businessName": business_name,
                                            "billing": None,
                                            "access": None,
                                            "settings": settings
                                        }
                                    else:
                                        contact_data[account_id]["settings"] = settings
                        else:
                            print("❌ No account data returned")
                else:
                    print(f"❌ HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            print("-" * 60)
        
        # Test introspection on Billing and Access types
        await introspect_billing_access_types(client, config, headers)
        
        # Summary
        print_billing_access_summary(contact_data)


async def introspect_billing_access_types(client, config, headers):
    """Use GraphQL introspection to discover Billing and Access type fields."""
    
    print(f"\n{'='*60}")
    print("GRAPHQL INTROSPECTION - BILLING & ACCESS TYPES")
    print(f"{'='*60}")
    
    types_to_introspect = ["Billing", "Access", "AccountSettings"]
    
    for type_name in types_to_introspect:
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
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ Introspection Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', str(error))}")
                
                if "data" in data and data["data"]:
                    type_info = data["data"].get("__type")
                    if type_info:
                        fields = type_info.get("fields", [])
                        print(f"✅ {type_name} type has {len(fields)} fields:")
                        
                        contact_related_fields = []
                        for field in fields:
                            field_name = field.get("name", "")
                            field_type = field.get("type", {})
                            type_name_str = field_type.get("name") or field_type.get("ofType", {}).get("name", "")
                            description = field.get("description", "")
                            
                            print(f"  - {field_name}: {type_name_str}")
                            if description:
                                print(f"    Description: {description}")
                            
                            # Check if field might be contact-related
                            contact_keywords = ["email", "contact", "owner", "user", "member", "admin", "billing", "notification", "name", "address", "phone"]
                            if any(keyword in field_name.lower() for keyword in contact_keywords):
                                contact_related_fields.append(field_name)
                        
                        if contact_related_fields:
                            print(f"\n🎯 Potential contact-related fields in {type_name}:")
                            for field in contact_related_fields:
                                print(f"  - {field}")
                    else:
                        print(f"❌ No {type_name} type found in introspection")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Introspection failed: {e}")


def print_billing_access_summary(contact_data):
    """Print summary of billing and access findings."""
    
    print(f"\n{'='*60}")
    print("BILLING & ACCESS CONTACT SUMMARY")
    print(f"{'='*60}")
    
    print(f"📊 Analysis Results:")
    print(f"  Total accounts analyzed: {len(contact_data)}")
    
    email_contacts_found = 0
    user_contacts_found = 0
    billing_contacts_found = 0
    
    if contact_data:
        print(f"\n🏨 Detailed Account Analysis:")
        
        for account_id, data in contact_data.items():
            business_name = data["businessName"]
            billing = data.get("billing")
            access = data.get("access")
            settings = data.get("settings")
            
            print(f"\n  Account: {business_name}")
            print(f"  ID: {account_id}")
            
            # Check for contact information
            contact_info = []
            
            if billing:
                print(f"    Billing Data Available: Yes")
                billing_contacts_found += 1
                
                # Look for email fields in billing
                email_fields = [k for k, v in billing.items() if "email" in k.lower() and v]
                if email_fields:
                    email_contacts_found += 1
                    for field in email_fields:
                        contact_info.append(f"billing.{field}: {billing[field]}")
                        
                # Look for name/contact fields in billing
                name_fields = [k for k, v in billing.items() if k.lower() in ["name", "contact", "company"] and v]
                for field in name_fields:
                    contact_info.append(f"billing.{field}: {billing[field]}")
            else:
                print(f"    Billing Data Available: No")
            
            if access:
                print(f"    Access Data Available: Yes")
                
                # Look for users with emails
                users = access.get("users", [])
                if users:
                    user_contacts_found += 1
                    for user in users:
                        if user.get("email"):
                            role = user.get("role", "unknown")
                            is_owner = user.get("isOwner", False)
                            contact_info.append(f"user {user['name']} ({role}{'Owner' if is_owner else ''}): {user['email']}")
            else:
                print(f"    Access Data Available: No")
            
            if settings:
                print(f"    Settings Data Available: Yes")
                
                # Look for email fields in settings
                email_fields = [k for k, v in settings.items() if "email" in k.lower() and v]
                for field in email_fields:
                    contact_info.append(f"settings.{field}: {settings[field]}")
            else:
                print(f"    Settings Data Available: No")
            
            if contact_info:
                print(f"    Contact Information Found:")
                for info in contact_info:
                    print(f"      ✅ {info}")
            else:
                print(f"    Contact Information Found: None")
    
    print(f"\n💡 NOTIFICATION SYSTEM ASSESSMENT:")
    
    if email_contacts_found > 0 or user_contacts_found > 0:
        print(f"✅ GOOD NEWS! Contact information IS available through the API!")
        print(f"  📊 Summary:")
        print(f"    - Accounts with billing data: {billing_contacts_found}")
        print(f"    - Accounts with email contacts: {email_contacts_found}")
        print(f"    - Accounts with user contacts: {user_contacts_found}")
        
        print(f"\n  🎯 You CAN build the notification system!")
        print(f"  📧 Email notifications are possible using:")
        
        if billing_contacts_found > 0:
            print(f"    - Billing contact information")
        if user_contacts_found > 0:
            print(f"    - User/access contact information")
        
        print(f"\n  📝 Recommended implementation approach:")
        print(f"    1. ✅ Query accounts with billing and access fields")
        print(f"    2. ✅ Extract contact emails from available data")
        print(f"    3. ✅ Build notification selection UI with account checkboxes")
        print(f"    4. ✅ Send targeted status reports to account contacts")
        
        # Generate recommended query
        recommended_query = """
        query GetAccountContacts {
            me {
                ... on PublicAPIClient {
                    accounts(first: 50) {
                        edges {
                            node {
                                id
                                businessName
                                billing {
                                    # Add billing contact fields that work
                                }
                                access {
                                    users {
                                        id
                                        name
                                        email
                                        role
                                        isOwner
                                    }
                                }
                                settings {
                                    # Add settings email fields that work
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        print(f"\n  📋 Template GraphQL query:")
        print(recommended_query)
        
    else:
        print(f"❌ Contact information is still not accessible")
        print(f"  Alternative approaches needed:")
        print(f"    1. Store contact info in local database")
        print(f"    2. Use business names for manual contact lookup")
        print(f"    3. Contact SYB support about API permissions")


async def test_working_billing_access_query():
    """Test a specific query with only the fields that actually work."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print("TESTING WORKING BILLING/ACCESS QUERY")
    print(f"{'='*60}")
    
    # Start simple and build up
    working_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 5) {
                    edges {
                        node {
                            id
                            businessName
                            billing
                            access
                        }
                    }
                }
            }
        }
    }
    """
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                config.syb_api_url,
                json={"query": working_query},
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ GraphQL Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', str(error))}")
                
                if "data" in data and data["data"]:
                    me_data = data["data"].get("me", {})
                    accounts_data = me_data.get("accounts", {})
                    account_edges = accounts_data.get("edges", [])
                    
                    print(f"✅ Successfully retrieved {len(account_edges)} accounts")
                    
                    for i, edge in enumerate(account_edges):
                        account = edge.get("node", {})
                        business_name = account.get("businessName", "Unknown")
                        billing = account.get("billing")
                        access = account.get("access")
                        
                        print(f"\n  Account {i+1}: {business_name}")
                        print(f"    Billing: {'Available' if billing else 'None'}")
                        print(f"    Access: {'Available' if access else 'None'}")
                        
                        if billing:
                            print(f"    Billing data: {type(billing)} = {billing}")
                        if access:
                            print(f"    Access data: {type(access)} = {access}")
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    print("SYB Billing & Access Contact Information Explorer")
    print("Investigating billing and access fields for contact information")
    print("="*80)
    
    asyncio.run(explore_billing_and_access())
    asyncio.run(test_working_billing_access_query())