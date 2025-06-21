# How to Get a Fresh WhatsApp Access Token

## Method 1: Use the WhatsApp Getting Started Page
1. Go to: https://developers.facebook.com/apps/
2. Select your app
3. Click on **WhatsApp** in the left sidebar
4. Click on **API Setup**
5. Look for the **Temporary access token** section
6. There should be a button to generate a new token there

## Method 2: Force Token Refresh in Graph API Explorer
1. Go to: https://developers.facebook.com/tools/explorer/
2. Click on the "User or Page" dropdown
3. Click "Get User Access Token"
4. Make sure these permissions are checked:
   - whatsapp_business_messaging
   - whatsapp_business_management
5. Click "Generate Access Token"
6. You might need to re-authenticate

## Method 3: Get Token from WhatsApp Business Manager
1. Go to your app dashboard
2. Navigate to WhatsApp > API Setup
3. In the "Temporary access token" section
4. Click the "Generate" or "Refresh" button

## Method 4: Clear Browser Cache
Sometimes the Graph API Explorer caches the token:
1. Clear your browser cache/cookies for developers.facebook.com
2. Log out and log back in
3. Try generating the token again

## Alternative: Use System User Token (Longer Lasting)
If you want a token that doesn't expire in 1-2 hours:
1. Go to Business Settings: https://business.facebook.com/settings
2. Create a System User
3. Generate token for the System User
4. This token lasts 60+ days

## Quick Test
Once you have a new token, test it immediately:
```bash
curl -X GET "https://graph.facebook.com/v17.0/me?access_token=YOUR_NEW_TOKEN"
```

If it returns your user info, the token is valid!