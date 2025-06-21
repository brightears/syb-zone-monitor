# WhatsApp Setup Checklist

## Required Steps in Meta Developer Dashboard

1. **Add Test Phone Number**
   - Go to your Meta app dashboard
   - Navigate to WhatsApp > API Setup
   - Under "To" section, click "Add phone number"
   - Add your phone number: +66856644142
   - Enter the verification code sent to your WhatsApp

2. **Verify Permissions**
   - Go to App Dashboard > Permissions
   - Ensure these permissions are enabled:
     - whatsapp_business_messaging
     - whatsapp_business_management

3. **Check App Mode**
   - Your app might be in Development mode
   - In Development mode, you can only send messages to verified test numbers
   - To send to any number, you need to complete Business Verification

## Current Issue
The error "(#10) Application does not have permission for this action" typically means:
- Your phone number isn't added as a test recipient
- OR the access token doesn't have the right permissions

## Quick Fix
1. Log into https://developers.facebook.com
2. Go to your app
3. Navigate to WhatsApp > API Setup
4. In the "To" section, add +66856644142 as a test number
5. Verify it with the code sent to your WhatsApp
6. Try sending the message again