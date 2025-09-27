# External API Integration Setup Guide

This guide walks you through setting up Gmail, Google Calendar, and HubSpot integrations.

## 🔐 Security First

**CRITICAL:** Never commit API keys or secrets to GitHub. All sensitive data must be in `.env` files that are gitignored.

---

## 1. Gmail API Setup

### Step 1: Enable Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Navigate to **APIs & Services** → **Library**
4. Search for "Gmail API" and click **Enable**

### Step 2: Configure OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (for testing) or **Internal** (for organization)
3. Fill in app information:
   - App name: "Financial Advisor AI Agent"
   - User support email: your email
   - Developer contact: your email
4. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
5. Add test users (REQUIRED):
   - `webshookeng@gmail.com` (for the challenge)
   - Your email

### Step 3: Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Add authorized redirect URIs:
   - `http://localhost:8000/auth/google/callback` (development)
   - `https://your-app.onrender.com/auth/google/callback` (production)
5. Copy **Client ID** and **Client Secret** to `.env`

### Step 4: Set Up Push Notifications (Optional for Webhooks)
```bash
# Create Cloud Pub/Sub topic
gcloud pubsub topics create gmail-notifications

# Grant Gmail permission
gcloud pubsub topics add-iam-policy-binding gmail-notifications \
  --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
  --role=roles/pubsub.publisher

# Create push subscription
gcloud pubsub subscriptions create gmail-push-subscription \
  --topic=gmail-notifications \
  --push-endpoint=https://your-app.onrender.com/webhooks/gmail/watch
```

---

## 2. Google Calendar API Setup

### Step 1: Enable Calendar API
1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Google Calendar API" and click **Enable**

### Step 2: Add Calendar Scopes to OAuth
The OAuth credentials from Gmail setup will work, just ensure these scopes are added:
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/calendar.events`

### Step 3: Set Up Calendar Webhooks (Optional)
```python
# In your app, call this to start watching calendar changes:
from googleapiclient.discovery import build

service = build('calendar', 'v3', credentials=creds)

body = {
    'id': 'unique-channel-id',
    'type': 'web_hook',
    'address': 'https://your-app.onrender.com/webhooks/calendar'
}

watch = service.events().watch(calendarId='primary', body=body).execute()
```

---

## 3. HubSpot API Setup

### Step 1: Create HubSpot Developer Account
1. Go to [HubSpot Developer](https://developers.hubspot.com)
2. Sign up or log in
3. Create a developer test account (free)

### Step 2: Create App
1. Go to **Apps** → **Create app**
2. Basic Info:
   - App name: "Financial Advisor AI Agent"
   - Description: "AI agent for financial advisors"

### Step 3: Configure OAuth
1. In app settings, go to **Auth** tab
2. Set redirect URL:
   - `http://localhost:8000/auth/hubspot/callback` (development)
   - `https://your-app.onrender.com/auth/hubspot/callback` (production)
3. Required scopes:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.schemas.contacts.read`
   - `oauth`
4. Copy **Client ID** and **Client Secret** to `.env`

### Step 4: Set Up Webhooks
1. In app settings, go to **Webhooks** tab
2. Set target URL: `https://your-app.onrender.com/webhooks/hubspot`
3. Subscribe to events:
   - `contact.creation`
   - `contact.propertyChange`
   - `contact.deletion`
4. Copy webhook signature secret to `.env` (for verification)

---

## 4. Environment Variables

Add to your `.env` file:

```env
# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# HubSpot OAuth (from HubSpot Developer Portal)
HUBSPOT_CLIENT_ID=your-hubspot-client-id
HUBSPOT_CLIENT_SECRET=your-hubspot-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/auth/hubspot/callback

# Optional: Webhook secrets
HUBSPOT_APP_SECRET=your-webhook-secret
```

---

## 5. Testing Integrations

### Run Integration Tests
```bash
# Make sure you have a test user in the database
python create_test_user.py

# Run integration tests
python test_integrations.py
```

### Manual Testing via API

1. **Authenticate with Google:**
```bash
curl http://localhost:8000/auth/google/login
# Visit the URL in browser, authenticate, get redirected
```

2. **Authenticate with HubSpot:**
```bash
curl http://localhost:8000/auth/hubspot/login
# Visit the URL in browser, authenticate, get redirected
```

3. **Test Batch Sync:**
```bash
curl -X POST http://localhost:8000/sync/full \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7, "include_gmail": true, "include_hubspot": true}'
```

4. **Check Sync Status:**
```bash
curl http://localhost:8000/sync/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 6. Rate Limits & Best Practices

### Gmail API
- **Quota:** 250 quota units/user/second
- **Daily limit:** 1 billion quota units/day
- **Best practice:** Use batch requests, implement exponential backoff

### Google Calendar API
- **Quota:** 1,000,000 queries/day
- **Best practice:** Cache frequently accessed data, use sync tokens for incremental updates

### HubSpot API
- **Rate limit:** 100 requests per 10 seconds (burst)
- **Daily limit:** 250,000 for Professional/Enterprise
- **Best practice:** Use batch endpoints when possible, implement retry logic

### Our Implementation
We use `tenacity` library for automatic retry with exponential backoff:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def api_call():
    # Your API call here
    pass
```

---

## 7. Troubleshooting

### Gmail API Errors

**Error: `invalid_grant`**
- Token expired, trigger refresh in `get_google_credentials()`

**Error: `insufficient permissions`**
- Check OAuth scopes in Google Cloud Console
- Re-authenticate user

### Calendar API Errors

**Error: `Daily Limit Exceeded`**
- Implement caching for frequently accessed events
- Use incremental sync instead of full sync

### HubSpot API Errors

**Error: `RATE_LIMIT_EXCEEDED`**
- Implement exponential backoff (already done with `tenacity`)
- Reduce batch size

**Error: `CONTACT_EXISTS`**
- Check for existing contact before creating (use `get_contact_by_email`)

---

## 8. Production Deployment Checklist

- [ ] Switch OAuth redirect URIs to production URLs
- [ ] Update webhook URLs to production domain
- [ ] Set up SSL/HTTPS (required for OAuth and webhooks)
- [ ] Configure webhook signature verification
- [ ] Set up monitoring for API errors
- [ ] Implement rate limit tracking
- [ ] Add logging for all API calls
- [ ] Set up alerts for quota limits
- [ ] Test OAuth flow end-to-end
- [ ] Verify webhook delivery

---

## 9. Security Best Practices

1. **Never log tokens or secrets**
2. **Encrypt tokens at rest** (we use Fernet encryption)
3. **Use HTTPS only** in production
4. **Verify webhook signatures** before processing
5. **Implement CSRF protection** on OAuth callbacks
6. **Rotate secrets regularly**
7. **Monitor for suspicious activity**
8. **Use least privilege** (minimal OAuth scopes)

---

## 10. Next Steps

After integrations are set up:

1. **Test each integration individually** using `test_integrations.py`
2. **Run a full batch sync** to import initial data
3. **Set up webhooks** for real-time updates
4. **Monitor API usage** in respective dashboards
5. **Move to Chat 5** for AI Agent Core implementation

---

## Support Resources

- [Gmail API Docs](https://developers.google.com/gmail/api)
- [Calendar API Docs](https://developers.google.com/calendar/api)
- [HubSpot API Docs](https://developers.hubspot.com/docs/api/overview)
- [OAuth 2.0 Guide](https://oauth.net/2/)

---
