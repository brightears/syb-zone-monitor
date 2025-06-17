#!/usr/bin/env python3
"""Explore account contact/owner information in the SYB GraphQL API."""

import asyncio
import json
from datetime import datetime

import httpx
from config import Config


async def explore_account_contact_fields():
    """Investigate what contact/owner information is available for accounts."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Exploring Account Contact Information")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # Test various potential contact fields
    contact_field_tests = [
        {
            "name": "Basic Account Info",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 5) {
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
            "name": "Extended Account Fields",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    email
                                    contactEmail
                                    ownerEmail
                                    primaryContact
                                    administratorEmail
                                    billingEmail
                                    owner
                                    contact
                                    administrator
                                    billing
                                }
                            }
                        }
                    }
                }
            }
            """
        },
        {
            "name": "Account Users/Members",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
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
                                        isOwner
                                        isPrimary
                                    }
                                    team {
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
            """
        },
        {
            "name": "Account with Subscription Contact",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    subscription {
                                        contact
                                        contactEmail
                                        ownerEmail
                                        billingContact
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
            "name": "Account Contact Object",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    contact {
                                        name
                                        email
                                        phone
                                        title
                                        role
                                    }
                                    owner {
                                        name
                                        email
                                        phone
                                        title
                                    }
                                    primaryContact {
                                        name
                                        email
                                        phone
                                        title
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
            "name": "Account Settings/Profile",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts(first: 3) {
                            edges {
                                node {
                                    id
                                    businessName
                                    profile {
                                        contactEmail
                                        ownerEmail
                                        primaryEmail
                                        notificationEmail
                                    }
                                    settings {
                                        contactEmail
                                        notificationEmail
                                        alertEmail
                                        adminEmail
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
        account_data = {}
        
        for i, test in enumerate(contact_field_tests):
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
                            
                            # Analyze error to understand which fields don't exist
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
                                
                                # Store successful account data
                                if account_id not in account_data:
                                    account_data[account_id] = {
                                        "businessName": business_name,
                                        "contactFields": {}
                                    }
                                
                                # Analyze all non-standard fields in this account
                                for field_name, field_value in account.items():
                                    if field_name not in ["id", "businessName"]:
                                        if field_value is not None:
                                            print(f"    ✅ {field_name}: {field_value}")
                                            working_fields.append(field_name)
                                            account_data[account_id]["contactFields"][field_name] = field_value
                                        else:
                                            print(f"    ➖ {field_name}: null")
                        else:
                            print("❌ No account data returned")
                else:
                    print(f"❌ HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            print("-" * 60)
        
        # Test individual account query for more detailed contact info
        await test_individual_account_contact(client, config, headers, account_data)
        
        # Test introspection on Account type
        await introspect_account_type(client, config, headers)
        
        # Summary
        print_contact_summary(working_fields, account_data)


async def test_individual_account_contact(client, config, headers, account_data):
    """Test querying individual accounts for contact information."""
    
    print(f"\n{'='*60}")
    print("TESTING INDIVIDUAL ACCOUNT CONTACT QUERIES")
    print(f"{'='*60}")
    
    if not account_data:
        print("❌ No account data available for individual testing")
        return
    
    # Get first account ID for detailed testing
    first_account_id = list(account_data.keys())[0]
    business_name = account_data[first_account_id]["businessName"]
    
    print(f"Testing detailed contact fields for: {business_name}")
    print(f"Account ID: {first_account_id}")
    
    # Test comprehensive individual account query
    individual_tests = [
        {
            "name": "Individual Account - All Contact Fields",
            "query": f"""
            query {{
                account(id: "{first_account_id}") {{
                    id
                    businessName
                    email
                    contactEmail
                    ownerEmail
                    primaryContact
                    administratorEmail
                    billingEmail
                    notificationEmail
                    alertEmail
                    contact {{
                        name
                        email
                        phone
                        title
                    }}
                    owner {{
                        name
                        email
                        phone
                        title
                    }}
                    users {{
                        id
                        name
                        email
                        role
                        isOwner
                        isPrimary
                    }}
                    members {{
                        id
                        name
                        email
                        role
                        isOwner
                        isPrimary
                    }}
                }}
            }}
            """
        },
        {
            "name": "Individual Account - Basic Fields Only",
            "query": f"""
            query {{
                account(id: "{first_account_id}") {{
                    id
                    businessName
                }}
            }}
            """
        }
    ]
    
    for test in individual_tests:
        print(f"\n--- {test['name']} ---")
        
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
                
                if "data" in data and data["data"]:
                    account = data["data"].get("account")
                    if account:
                        print("✅ Individual account data:")
                        print(json.dumps(account, indent=2))
                    else:
                        print("❌ No account data in response")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


async def introspect_account_type(client, config, headers):
    """Use GraphQL introspection to discover Account type fields."""
    
    print(f"\n{'='*60}")
    print("GRAPHQL INTROSPECTION - ACCOUNT TYPE")
    print(f"{'='*60}")
    
    introspection_query = """
    query {
        __type(name: "Account") {
            name
            fields {
                name
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
                description
            }
        }
    }
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
                account_type = data["data"].get("__type")
                if account_type:
                    fields = account_type.get("fields", [])
                    print(f"✅ Account type has {len(fields)} fields:")
                    
                    contact_related_fields = []
                    for field in fields:
                        field_name = field.get("name", "")
                        field_type = field.get("type", {})
                        type_name = field_type.get("name") or field_type.get("ofType", {}).get("name", "")
                        description = field.get("description", "")
                        
                        print(f"  - {field_name}: {type_name}")
                        if description:
                            print(f"    Description: {description}")
                        
                        # Check if field might be contact-related
                        contact_keywords = ["email", "contact", "owner", "user", "member", "admin", "billing", "notification"]
                        if any(keyword in field_name.lower() for keyword in contact_keywords):
                            contact_related_fields.append(field_name)
                    
                    if contact_related_fields:
                        print(f"\n🎯 Potential contact-related fields:")
                        for field in contact_related_fields:
                            print(f"  - {field}")
                    else:
                        print(f"\n❌ No obvious contact-related fields found")
                else:
                    print("❌ No Account type found in introspection")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Introspection failed: {e}")


def print_contact_summary(working_fields, account_data):
    """Print summary of findings."""
    
    print(f"\n{'='*60}")
    print("ACCOUNT CONTACT INFORMATION SUMMARY")
    print(f"{'='*60}")
    
    unique_fields = list(set(working_fields))
    
    print(f"✅ Successfully discovered fields:")
    if unique_fields:
        for field in sorted(unique_fields):
            print(f"  - {field}")
    else:
        print("  ❌ No additional contact fields found beyond 'businessName'")
    
    print(f"\n📊 Account Analysis:")
    print(f"  Total accounts analyzed: {len(account_data)}")
    
    if account_data:
        print(f"\n🏨 Sample Account Data:")
        for account_id, data in list(account_data.items())[:3]:  # Show first 3
            business_name = data["businessName"]
            contact_fields = data["contactFields"]
            
            print(f"\n  Account: {business_name}")
            print(f"  ID: {account_id}")
            
            if contact_fields:
                print(f"  Contact fields found:")
                for field_name, field_value in contact_fields.items():
                    print(f"    - {field_name}: {field_value}")
            else:
                print(f"  Contact fields: None found")
    
    print(f"\n💡 NOTIFICATION SYSTEM RECOMMENDATIONS:")
    
    if unique_fields:
        print(f"✅ Contact information is available! You can build the notification system using:")
        
        email_fields = [f for f in unique_fields if "email" in f.lower()]
        if email_fields:
            print(f"  📧 Email fields: {', '.join(email_fields)}")
            print(f"  ✅ Can send email notifications to account owners")
        
        user_fields = [f for f in unique_fields if f.lower() in ["users", "members", "team"]]
        if user_fields:
            print(f"  👥 User/member fields: {', '.join(user_fields)}")
            print(f"  ✅ Can get multiple contacts per account")
        
        print(f"\n  📝 Recommended GraphQL query for notification system:")
        
        # Build recommended query based on what works
        recommended_fields = ["id", "businessName"]
        recommended_fields.extend([f for f in unique_fields if "email" in f.lower()])
        
        if "users" in unique_fields:
            recommended_fields.append("users { id name email role isOwner }")
        elif "members" in unique_fields:
            recommended_fields.append("members { id name email role isOwner }")
        
        query_fields = "\n                    ".join(recommended_fields)
        recommended_query = f"""
        query GetAccountContacts {{
            me {{
                ... on PublicAPIClient {{
                    accounts(first: 50) {{
                        edges {{
                            node {{
                                {query_fields}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        
        print(recommended_query)
        
    else:
        print(f"❌ No contact information fields found in the API")
        print(f"  The API appears to only provide 'businessName' for accounts")
        print(f"  Alternative approaches:")
        print(f"    1. Store contact info in your local database")
        print(f"    2. Use business name to lookup contacts externally")
        print(f"    3. Ask SYB support about accessing contact information")
        print(f"    4. Use a separate contact management system")
    
    print(f"\n🎯 NEXT STEPS:")
    if unique_fields and any("email" in f.lower() for f in unique_fields):
        print(f"  1. ✅ Implement account contact retrieval using discovered fields")
        print(f"  2. ✅ Build notification selection UI with account checkboxes")
        print(f"  3. ✅ Create targeted email notification system")
        print(f"  4. ✅ Test with real account data")
    else:
        print(f"  1. ❌ Contact SYB support about API access to contact information")
        print(f"  2. ❌ Implement alternative contact management approach")
        print(f"  3. ❌ Consider using business names for manual contact lookup")


async def test_specific_account_by_name():
    """Test getting contact info for a specific known account."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    # Load known accounts from our mapping
    try:
        with open("account_mapping.json", "r") as f:
            account_mapping = json.load(f)
            
        accounts = account_mapping.get("accounts", {})
        if not accounts:
            print("❌ No accounts found in mapping file")
            return
        
        # Test with the first few known accounts
        print(f"\n{'='*60}")
        print("TESTING KNOWN ACCOUNTS FOR CONTACT INFO")
        print(f"{'='*60}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            
            for account_id, business_name in list(accounts.items())[:3]:
                print(f"\nTesting: {business_name}")
                print(f"ID: {account_id}")
                
                # Try comprehensive individual account query
                query = f"""
                query {{
                    soundZones(accountId: "{account_id}", first: 1) {{
                        edges {{
                            node {{
                                id
                                account {{
                                    id
                                    businessName
                                    email
                                    contactEmail
                                    ownerEmail
                                    contact
                                    owner
                                    users
                                    members
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
                        
                        if "errors" in data:
                            print("  ❌ Errors:", [e.get('message') for e in data['errors']])
                        
                        if "data" in data and data["data"]:
                            zones = data["data"].get("soundZones", {}).get("edges", [])
                            if zones:
                                account_data = zones[0]["node"]["account"]
                                print("  ✅ Account data via zone:")
                                print(json.dumps(account_data, indent=4))
                            else:
                                print("  ❌ No zones found for account")
                    else:
                        print(f"  ❌ HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ Request failed: {e}")
                    
    except FileNotFoundError:
        print("❌ account_mapping.json not found")
    except Exception as e:
        print(f"❌ Error loading account mapping: {e}")


if __name__ == "__main__":
    print("SYB Account Contact Information Explorer")
    print("Investigating contact/owner fields for notification system")
    print("="*80)
    
    asyncio.run(explore_account_contact_fields())
    asyncio.run(test_specific_account_by_name())