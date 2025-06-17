#!/usr/bin/env python3
"""Explore the billing field on accounts to find primary contact information."""

import asyncio
import json
from datetime import datetime
import httpx
from config import Config


async def explore_billing_field():
    """Deep dive into the billing field to find contact information."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("💳 Exploring Account Billing Field for Contact Information")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # First, introspect the Billing type
        print("\n1. INTROSPECTING BILLING TYPE")
        print("-"*60)
        
        billing_introspection = """
        query {
            __type(name: "Billing") {
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
                json={"query": billing_introspection},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    billing_type = data["data"].get("__type")
                    if billing_type:
                        fields = billing_type.get("fields", [])
                        print(f"✅ Billing type has {len(fields)} fields:")
                        
                        contact_fields = []
                        for field in fields:
                            field_name = field.get("name", "")
                            field_type = field.get("type", {})
                            type_name = field_type.get("name") or field_type.get("ofType", {}).get("name", "")
                            description = field.get("description", "")
                            
                            print(f"  - {field_name}: {type_name}")
                            if description:
                                print(f"    Description: {description}")
                            
                            # Check for contact-related fields
                            if any(term in field_name.lower() for term in ["email", "contact", "owner", "admin", "name", "customer"]):
                                contact_fields.append(field_name)
                        
                        if contact_fields:
                            print(f"\n🎯 Potential contact fields in Billing: {contact_fields}")
                        
                        # Now test billing data on actual accounts
                        await test_billing_on_accounts(client, config, headers, contact_fields)
                        
                else:
                    print("❌ No Billing type found")
                    
        except Exception as e:
            print(f"❌ Billing introspection failed: {e}")


async def test_billing_on_accounts(client, config, headers, potential_fields):
    """Test billing field on actual accounts."""
    
    print("\n\n2. TESTING BILLING FIELD ON ACCOUNTS")
    print("-"*60)
    
    # Build a comprehensive billing query
    billing_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 20) {
                    edges {
                        node {
                            id
                            businessName
                            billing {
                                # Try all common billing fields
                                id
                                email
                                contactEmail
                                billingEmail
                                customerEmail
                                ownerEmail
                                adminEmail
                                primaryEmail
                                accountEmail
                                
                                # Name fields
                                name
                                contactName
                                customerName
                                billingName
                                
                                # Contact object
                                contact {
                                    name
                                    email
                                    phone
                                }
                                
                                # Customer info
                                customer {
                                    id
                                    name
                                    email
                                }
                                
                                # Subscription info that might have contact
                                subscription {
                                    id
                                    contactEmail
                                    customerEmail
                                }
                                
                                # Payment method might have contact
                                paymentMethod {
                                    email
                                    name
                                }
                                
                                # Any other nested objects
                                billingContact {
                                    name
                                    email
                                    phone
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    print("Testing comprehensive billing query...")
    
    try:
        response = await client.post(
            config.syb_api_url,
            json={"query": billing_query},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for errors to see which fields don't exist
            if "errors" in data:
                print("\n❌ Fields that don't exist:")
                for error in data["errors"]:
                    message = error.get('message', '')
                    if "Cannot query field" in message:
                        field = message.split('"')[1] if '"' in message else "unknown"
                        print(f"  - {field}")
            
            # Process any data we got
            if "data" in data and data["data"]:
                accounts = data["data"]["me"]["accounts"]["edges"]
                
                if accounts:
                    print(f"\n✅ Retrieved {len(accounts)} accounts")
                    
                    accounts_with_billing_contact = 0
                    billing_contacts = []
                    
                    for edge in accounts:
                        account = edge["node"]
                        business_name = account.get("businessName", "Unknown")
                        billing = account.get("billing")
                        
                        if billing:
                            print(f"\n📍 {business_name}")
                            print(f"  Billing data: {json.dumps(billing, indent=4)}")
                            
                            # Extract any contact info from billing
                            contact_info = extract_contact_from_billing(billing)
                            if contact_info:
                                accounts_with_billing_contact += 1
                                billing_contacts.append({
                                    "business_name": business_name,
                                    "contacts": contact_info
                                })
                    
                    # Summary
                    print(f"\n📊 BILLING CONTACT SUMMARY:")
                    print(f"  Total accounts: {len(accounts)}")
                    print(f"  Accounts with billing contact: {accounts_with_billing_contact}")
                    print(f"  Percentage: {(accounts_with_billing_contact/len(accounts)*100):.1f}%")
                    
                    if billing_contacts:
                        print(f"\n💾 Saving billing contacts to billing_contacts.json")
                        with open("billing_contacts.json", "w") as f:
                            json.dump({
                                "timestamp": datetime.now().isoformat(),
                                "total_accounts": len(accounts),
                                "accounts_with_contacts": accounts_with_billing_contact,
                                "contacts": billing_contacts
                            }, f, indent=2)
                        
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Billing query failed: {e}")


async def test_minimal_billing():
    """Test minimal billing field access."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("\n\n3. TESTING MINIMAL BILLING QUERY")
    print("-"*60)
    
    # Start with just the billing field itself
    minimal_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 5) {
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
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                config.syb_api_url,
                json={"query": minimal_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    accounts = data["data"]["me"]["accounts"]["edges"]
                    
                    print(f"✅ Retrieved {len(accounts)} accounts with billing field")
                    
                    for edge in accounts:
                        account = edge["node"]
                        business_name = account.get("businessName")
                        billing = account.get("billing")
                        
                        print(f"\n{business_name}:")
                        if billing:
                            print(f"  Billing type: {billing.get('__typename')}")
                            print(f"  Billing data: {billing}")
                        else:
                            print(f"  No billing data")
                            
        except Exception as e:
            print(f"❌ Minimal billing query failed: {e}")


async def check_account_settings():
    """Check if AccountSettings contains contact information."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("\n\n4. CHECKING ACCOUNT SETTINGS FOR CONTACT INFO")
    print("-"*60)
    
    # First introspect AccountSettings
    settings_introspection = """
    query {
        __type(name: "AccountSettings") {
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
                json={"query": settings_introspection},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    settings_type = data["data"].get("__type")
                    if settings_type:
                        fields = settings_type.get("fields", [])
                        print(f"✅ AccountSettings type has {len(fields)} fields:")
                        
                        for field in fields:
                            field_name = field.get("name", "")
                            print(f"  - {field_name}: {field.get('type', {}).get('name')}")
                            
                            # If we find email/contact fields, test them
                            if any(term in field_name.lower() for term in ["email", "contact", "notification"]):
                                await test_settings_field(client, config, headers, field_name)
                                
        except Exception as e:
            print(f"❌ Settings introspection failed: {e}")


async def test_settings_field(client, config, headers, field_name):
    """Test a specific settings field."""
    
    print(f"\n  Testing settings.{field_name}...")
    
    query = f"""
    {{
        me {{
            ... on PublicAPIClient {{
                accounts(first: 5) {{
                    edges {{
                        node {{
                            id
                            businessName
                            settings {{
                                {field_name}
                            }}
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
            
            if "data" in data and data["data"]:
                accounts = data["data"]["me"]["accounts"]["edges"]
                
                for edge in accounts:
                    account = edge["node"]
                    settings = account.get("settings", {})
                    value = settings.get(field_name)
                    
                    if value:
                        print(f"    ✅ {account.get('businessName')}: {field_name} = {value}")
                        
    except Exception as e:
        print(f"    ❌ Failed: {e}")


def extract_contact_from_billing(billing_data):
    """Extract any contact information from billing data."""
    
    if not billing_data:
        return None
    
    contacts = []
    
    # Check for direct email fields
    for field in ["email", "contactEmail", "billingEmail", "customerEmail"]:
        if field in billing_data and billing_data[field]:
            contacts.append({
                "type": field,
                "email": billing_data[field]
            })
    
    # Check nested objects
    if "contact" in billing_data and billing_data["contact"]:
        contact = billing_data["contact"]
        if contact.get("email"):
            contacts.append({
                "type": "billing.contact",
                "name": contact.get("name"),
                "email": contact["email"]
            })
    
    if "customer" in billing_data and billing_data["customer"]:
        customer = billing_data["customer"]
        if customer.get("email"):
            contacts.append({
                "type": "billing.customer",
                "name": customer.get("name"),
                "email": customer["email"]
            })
    
    return contacts if contacts else None


if __name__ == "__main__":
    print("SYB Account Billing Contact Explorer")
    print("Investigating billing field for primary account contact information")
    print("="*80)
    
    asyncio.run(explore_billing_field())
    asyncio.run(test_minimal_billing())
    asyncio.run(check_account_settings())