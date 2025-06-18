# SMS Notification Setup Guide

This guide will help you set up SMS notifications for the SYB Zone Monitor using Twilio.

## Prerequisites

- A Twilio account (sign up at https://www.twilio.com)
- A Twilio phone number capable of sending SMS
- Phone numbers for your contacts in E.164 format (e.g., +1234567890)

## Step 1: Create a Twilio Account

1. Go to https://www.twilio.com and sign up for a free account
2. Verify your email and phone number
3. You'll receive $15 in free trial credits (enough for ~1000 SMS messages)

## Step 2: Get Your Twilio Credentials

1. Log in to your Twilio Console
2. From the dashboard, copy:
   - **Account SID**: Found on the main dashboard
   - **Auth Token**: Click to reveal and copy
3. Save these credentials securely

## Step 3: Get a Twilio Phone Number

1. In the Twilio Console, go to **Phone Numbers** > **Manage** > **Buy a number**
2. Choose a number with SMS capabilities
3. Purchase the number (costs ~$1/month)
4. Copy the phone number in E.164 format (e.g., +1234567890)

## Step 4: Configure Environment Variables

Add the following to your `.env` file:

```env
# Enable SMS notifications
SMS_ENABLED=true

# Twilio credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890

# SMS settings
SMS_CRITICAL_THRESHOLD=1800  # Send automatic SMS if zone offline for 30+ minutes
SMS_QUIET_HOURS_START=22     # Don't send automatic SMS after 10 PM
SMS_QUIET_HOURS_END=7        # Resume automatic SMS after 7 AM
```

## Step 5: Add Phone Numbers to Contacts

Currently, phone numbers need to be added manually to your contact data. Update your `FINAL_CONTACT_ANALYSIS.json` file:

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "phone_verified": true,
  "sms_enabled": true
}
```

## Step 6: Test SMS Notifications

1. Deploy the updated application
2. Open the dashboard and click "Notify" on any account
3. Check the "SMS" checkbox in the notification modal
4. Select contacts with phone numbers
5. Send a test notification

## SMS Features

### Manual SMS Notifications
- Send SMS alerts manually through the dashboard
- Choose between Email, SMS, or both
- Custom message templates for different alert types
- See which contacts have phone numbers

### Automatic SMS Alerts (Coming Soon)
- Automatically send SMS when zones are offline for 30+ minutes
- Respects quiet hours (no SMS between 10 PM - 7 AM by default)
- One SMS per account per incident to prevent spam

### SMS Message Format
SMS messages are automatically shortened to fit within SMS limits:
- Zone offline alerts list up to 3 zones with duration
- Clear, concise format optimized for mobile viewing
- Includes account name and action required

## Cost Considerations

- **Twilio Trial**: $15 free credits (~1000 SMS to US numbers)
- **Pay-as-you-go**: ~$0.0079 per SMS to US numbers
- **Monthly phone number**: ~$1.15/month
- **International rates**: Vary by country (check Twilio pricing)

## Troubleshooting

### SMS not sending?
1. Check that `SMS_ENABLED=true` in your `.env` file
2. Verify Twilio credentials are correct
3. Ensure phone numbers are in E.164 format (+country code)
4. Check Twilio console for error logs

### Rate limiting?
- Twilio has default sending limits
- New accounts: 1 SMS/second
- Can be increased by contacting Twilio support

### International SMS issues?
- Some countries require sender ID registration
- Check Twilio's country-specific requirements
- May need to upgrade from trial account

## Security Best Practices

1. **Never commit credentials**: Keep `.env` file in `.gitignore`
2. **Use environment variables**: Don't hardcode credentials
3. **Verify phone numbers**: Implement verification before enabling SMS
4. **Rate limiting**: Implement limits to prevent abuse
5. **Opt-in/out**: Provide ways for users to manage SMS preferences

## Future Enhancements

- [ ] Phone number verification flow
- [ ] SMS preference management UI
- [ ] Automatic critical alerts
- [ ] SMS delivery status tracking
- [ ] Multiple SMS providers support
- [ ] WhatsApp Business API integration