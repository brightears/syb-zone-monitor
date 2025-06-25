# Deployment Notes - Email Contact Management Update

## Changes Deployed
- **Date**: 2025-06-25
- **Commit**: e9cd977
- **Feature**: Manual email contact management with enhanced email service

## What's New
1. **Manual Email Contacts**: Users can now add email contacts manually for each account
2. **Enhanced Email Service**: Professional email formatting with zone status details
3. **Dual Contact Sources**: Supports both API contacts (from SYB) and manual contacts
4. **Custom WhatsApp Messages**: Switched from template-only to custom message support

## Database Migration Required
The new email_contacts table will be created automatically when the app starts, but you can also run manually:

```sql
-- This is in create_email_contacts_table.sql
CREATE TABLE IF NOT EXISTS email_contacts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(100) DEFAULT 'Manager',
    is_active BOOLEAN DEFAULT TRUE,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, email)
);
```

## Environment Variables to Check on Render
Make sure these are set for email functionality:
- `SMTP_HOST` (default: smtp.gmail.com)
- `SMTP_PORT` (default: 587)
- `SMTP_USERNAME` (your email)
- `SMTP_PASSWORD` (app password)
- `EMAIL_FROM` (sender address)

## Testing After Deployment
1. Check the dashboard loads: https://your-app.onrender.com
2. Try adding a manual email contact for an account
3. Send a test notification to verify email delivery
4. Check logs for any errors

## Rollback if Needed
```bash
git revert e9cd977
git push origin main
```

## Next Steps
- Wait for WhatsApp number to be released (24-hour period)
- Update WHATSAPP_PHONE_NUMBER_ID when ready
- Test WhatsApp integration with business number