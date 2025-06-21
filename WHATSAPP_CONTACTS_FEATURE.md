# WhatsApp Contact Management Feature

## Overview
You can now store and manage WhatsApp contacts for each account, making it easy to send notifications without typing numbers manually each time.

## How to Use

### 1. Adding WhatsApp Contacts
When you open the notification modal for any account:
1. Click the **"Manage WhatsApp Contacts"** button
2. In the modal that appears:
   - Enter contact name (e.g., "John - Manager")
   - Enter WhatsApp number with country code (e.g., +60123456789)
   - Click "Add Contact"
3. The contact is now saved for that account

### 2. Sending Notifications
In the notification modal:
- **Stored Contacts**: Check the boxes next to WhatsApp contacts you want to notify
- **Quick Send**: Still type a number in the field for one-time sends
- **Both**: You can select stored contacts AND add a quick number

### 3. Managing Contacts
- **View**: Open "Manage WhatsApp Contacts" to see all contacts for an account
- **Delete**: Click the × button next to any contact to remove it
- **Update**: Delete and re-add to update a contact

## Features

✅ **Persistent Storage**: Contacts are saved and remembered between sessions
✅ **Account Isolation**: Each account has its own separate contact list
✅ **Multiple Recipients**: Send to multiple WhatsApp numbers at once
✅ **Validation**: Phone numbers must include country code (start with +)
✅ **Similar to Email**: Works just like the email contact selection

## Data Storage

- Contacts are stored locally in `whatsapp_contacts.json`
- This file is git-ignored for privacy
- Format: Account ID → List of contacts

## Example Workflow

1. **First Time**: 
   - Open notification for "Hyatt Regency Phuket"
   - Click "Manage WhatsApp Contacts"
   - Add "+66856644142" as "Hotel Manager"
   
2. **Next Time**:
   - Open notification for same account
   - "Hotel Manager" appears as a checkbox
   - Just check the box and send!

## Important Notes

- Always include country code (+60 for Malaysia, +66 for Thailand, etc.)
- Contacts are stored per account, not globally
- The quick WhatsApp field still works for one-time sends
- When business WhatsApp number is added (Monday), contacts will receive actual zone alerts