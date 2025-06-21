# WhatsApp Access Token Guide

## Current Issue
You're getting "(#10) Application does not have permission for this action" which typically means:
1. The access token doesn't have the right permissions
2. The phone number isn't properly set up as a test recipient
3. The app configuration is incomplete

## Solution Steps

### Option 1: Generate a New Temporary Token (Quick Test)
1. Go to: https://developers.facebook.com/tools/explorer/
2. Select your app: "SYB Zone Monitor" (or whatever you named it)
3. Add these permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
4. Click "Generate Access Token"
5. Copy the token and update your .env file

### Option 2: Check WhatsApp Configuration
1. Go to your app dashboard
2. Navigate to: WhatsApp > Configuration
3. Make sure you see:
   - Your WhatsApp Business Account
   - Your phone number (15551884340)
   - Status should be "Active"

### Option 3: Verify Test Phone Numbers
1. Go to: WhatsApp > API Setup
2. In the "From" section, you should see your business phone number
3. In the "To" section, verify that +66856644142 is listed and verified
4. If not, add it again and complete verification

### Option 4: Try the Built-in Tester
1. In WhatsApp > API Setup
2. Find the "Send and receive messages" section
3. There should be a built-in message tester
4. Try sending a test message there first

## Important Notes
- In Development mode, you can only send to 5 verified test numbers
- The token from the Graph API Explorer expires after 1 hour
- For production, you'll need a System User token (longer process)

## If Still Not Working
The issue might be that your WhatsApp Business Account isn't properly connected to your app. Try:
1. Remove the WhatsApp product from your app
2. Re-add WhatsApp product
3. Go through the setup again
4. Make sure to select your WhatsApp Business Account during setup