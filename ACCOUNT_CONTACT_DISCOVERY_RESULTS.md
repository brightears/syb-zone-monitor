# SYB GraphQL API - Account Contact Discovery Results

## Summary

**Great news!** The SYB GraphQL API **DOES** provide access to account contact information through the `access.users` and `access.pendingUsers` fields. You can successfully build a targeted notification system to send status reports to account owners.

## Key Findings

### Available Contact Information

1. **Active Users**: Each account can have multiple active users with:
   - User ID
   - Name
   - Email address
   - Company role (optional)
   - Created/Updated timestamps

2. **Pending Users**: Invited users who haven't accepted yet:
   - Email address only

### Statistics from Test Run
- Total accounts queried: 10
- Accounts with contacts: 4 (40%)
- Total contact emails available: 7
- Average contacts per account (when present): 1.75

## Working GraphQL Query

```graphql
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
```

## Sample Contact Data Structure

```json
{
  "account_id": "QWNjb3VudCwsMW1sbTJ0ZW52OWMv",
  "business_name": "Anantara Desaru Coast Resort & Villas",
  "contacts": [
    {
      "id": "VXNlciwsMWtnbTgycWs2aW8v",
      "name": "Norbert Platzer",
      "email": "norbert@bmasiamusic.com",
      "role": "Music Curator",
      "type": "active"
    },
    {
      "id": "VXNlcixzb3VuZHRyYWNrOnVzZXI6a0Y2RDdyd0x0SDZMR2RjZWp0bzhpajlWaUxKOWV3U2F4Q3pnZGc0M2kxSDJ3MjFBMywwLw..",
      "name": "Peter Wagner",
      "email": "pwagner@anantara.com",
      "role": null,
      "type": "active"
    },
    {
      "name": "Pending User",
      "email": "pvisvalingam@anantara.com",
      "role": "pending",
      "type": "pending"
    }
  ]
}
```

## Implementation Recommendations

### 1. Notification Selection UI
Build a dashboard interface with:
- List of accounts with checkboxes for selection
- Display contact count per account
- Option to select individual contacts within an account
- Bulk selection options (all accounts, accounts with issues, etc.)

### 2. Contact Retrieval Function
```python
async def get_account_contacts():
    """Fetch all accounts with their contact information."""
    # Use the working GraphQL query above
    # Return structured data with account ID, name, and contacts
```

### 3. Notification Types
- **Critical Alerts**: All zones offline for an account
- **Warning Notifications**: Multiple zones offline
- **Status Summaries**: Daily/weekly reports
- **Custom Messages**: Manual notifications with custom content

### 4. Email Template Structure
```
Subject: [SYB Alert] Zone Status for {business_name}

Dear {contact_name},

This is an automated status report for your SoundZones at {business_name}.

Current Status:
- Total Zones: {total_zones}
- Online: {online_zones}
- Offline: {offline_zones}

Offline Zones:
{for each offline zone}
- {zone_name}: Offline since {offline_timestamp}
{/for}

Please check your zones or contact support if assistance is needed.

Best regards,
SYB Monitoring System
```

### 5. Integration with Existing System
- Extend `zone_monitor.py` to include contact retrieval
- Add notification controls to the web dashboard
- Use existing `notifier/email.py` for sending emails
- Store notification history for tracking

## Important Considerations

1. **Not all accounts have contacts**: Only 40% of tested accounts had contact information
2. **Email permissions**: Some users may not have email addresses visible
3. **Pending users**: Include option to notify pending users as well
4. **Rate limiting**: Be mindful of API rate limits when fetching contact data

## Next Steps

1. Implement the contact retrieval function using the working query
2. Create a notification selection interface in the dashboard
3. Build email templates for different notification scenarios
4. Add notification scheduling (immediate, daily digest, weekly summary)
5. Test with real account data and monitor delivery rates

## Contact Fields Not Available

The following fields were tested but are NOT available in the API:
- Direct email fields on Account (email, contactEmail, ownerEmail, etc.)
- Owner/contact objects on Account
- User role flags (isOwner, isPrimary, isAdmin)
- Total count of users in a connection

## Conclusion

The SYB GraphQL API provides sufficient contact information to build a targeted notification system. While not every account has configured users, those that do can receive automated status reports about their zones. This will enable proactive communication with account owners when issues arise.