# Setting Up BMAsia WhatsApp Business Account

## Prerequisites
- ✅ You have a BMAsia phone number
- ✅ You have a Meta Business account
- ✅ You have a Facebook app created

## Step-by-Step Setup

### 1. Register Your Phone Number with WhatsApp Business
1. Download **WhatsApp Business app** on a phone
2. Register using your BMAsia phone number
3. Set up your business profile:
   - Business name: BMAsia
   - Category: Business Services
   - Description: Music streaming solutions for businesses
   - Email: Your BMAsia support email
   - Website: Your BMAsia website

### 2. Add Phone Number to Your Meta App
1. Go to: https://developers.facebook.com
2. Select your app (SYB Zone Monitor)
3. Navigate to: **WhatsApp > API Setup**
4. Click **"Add phone number"** in the "From" section
5. Select **"Add a phone number you own"**
6. Enter your BMAsia phone number
7. Select verification method (SMS or Voice call)
8. Enter the verification code

### 3. Connect WhatsApp Business Account
1. In the same API Setup page
2. You'll see options to:
   - Create a new WhatsApp Business Account
   - OR connect an existing one
3. Choose **"Create new WhatsApp Business Account"**
4. Name it: "BMAsia Support" or similar

### 4. Get Your New Phone Number ID
1. Once connected, you'll see your phone number listed
2. Click on the phone number
3. Copy the **Phone number ID** (it will be different from the test number ID)
4. This is what you'll use instead of `704214529438627`

### 5. Update Your Configuration
Update your `.env` file:
```bash
# WhatsApp Business Configuration
WHATSAPP_ENABLED=true
WHATSAPP_PHONE_NUMBER_ID=your_new_phone_number_id_here
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_API_VERSION=v17.0
```

### 6. Update Render Environment Variables
1. Go to your Render dashboard
2. Update `WHATSAPP_PHONE_NUMBER_ID` with the new ID
3. Save and let it redeploy

### 7. Revert to Original WhatsApp Service
Since we'll have a real business number, we can send custom messages:
```bash
cd "/Users/benorbe/Documents/SYB Offline Alarm"
cp whatsapp_service_original.py whatsapp_service.py
git add whatsapp_service.py
git commit -m "Revert to custom messages for business number"
git push
```

## Important Notes

### Business Verification (Optional but Recommended)
- In development mode: Can message 250 unique users per day
- After business verification: Unlimited messaging
- To verify: Meta Business Manager > Business Settings > Business Info > Start Verification

### Message Templates vs Direct Messages
With a business number, you can:
- Send **template messages** to anyone (after 24 hours of no conversation)
- Send **regular messages** within 24-hour conversation window
- For your monitoring system, you'll mainly use template messages

### Rate Limits
- Start with 250 initiated conversations per day
- Increases based on quality rating and usage
- Monitor in: WhatsApp Manager > Insights

## Troubleshooting

### If Phone Number Registration Fails
- Make sure the number isn't already registered with WhatsApp
- Try using WhatsApp Business app first
- Contact Meta support if issues persist

### If API Calls Fail
- Verify the new Phone Number ID is correct
- Check that your access token has permissions for the new number
- Ensure the number is verified and active

## Next Steps
1. Complete the phone number setup
2. Get the new Phone Number ID
3. Update your configuration
4. Test with a real zone alert message!