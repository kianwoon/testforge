# Microsoft Teams Integration Setup Guide

This guide walks you through setting up TestForge integration with Microsoft Teams, allowing team members to submit test cases directly from Teams channels.

## Prerequisites

Before starting, ensure you have:

- **Azure Account**: An active Azure subscription with permissions to register applications
- **Microsoft Teams Access**: Ability to add apps to Teams channels
- **TestForge Deployment**: A running instance of TestForge (local or cloud)
- **Public Endpoint**: For production, a publicly accessible HTTPS endpoint (port 3978)
  - For local development, use [ngrok](https://ngrok.com/) to create a tunnel

---

## Step 1: Register Bot in Azure Portal

1. Navigate to the [Azure Portal](https://portal.azure.com/)
2. Search for **Azure Bot** in the search bar and select it
3. Click **Create** to register a new bot
4. Fill in the required information:
   - **Bot Handle**: A unique identifier for your bot (e.g., `testforge-bot`)
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or select existing
   - **Pricing Tier**: Standard or Free (F0) for development
   - **Type of App**: Multi-tenant (recommended for most cases)
5. Click **Review + Create**, then **Create**

Once created, note down the **Microsoft App ID** - you'll need this for configuration.

---

## Step 2: Generate App Password

1. In your bot's Azure resource page, go to **Configuration**
2. Find the **Microsoft App ID** section
3. Click **Manage Password (Secret)** or navigate to **Certificates & secrets**
4. Click **New client secret**
5. Enter a description (e.g., "TestForge Integration") and select an expiration
6. Click **Add**
7. **IMPORTANT**: Copy the **Value** (not the Secret ID) immediately - you won't be able to see it again

---

## Step 3: Configure TestForge

Update your TestForge `.env` file with the Teams configuration:

```env
# Microsoft Teams Bot Configuration
TEAMS_APP_ID=<your-microsoft-app-id>
TEAMS_APP_PASSWORD=<your-app-password-value>
TEAMS_BOT_PORT=3978

# Existing TestForge configuration
CLAUDE_API_KEY=<your-claude-api-key>
# ... other settings
```

### Configuration Options

| Variable | Description | Required |
|----------|-------------|----------|
| `TEAMS_APP_ID` | Microsoft App ID from Azure | Yes |
| `TEAMS_APP_PASSWORD` | Client secret value from Azure | Yes |
| `TEAMS_BOT_PORT` | Port for Teams bot service (default: 3978) | No |

---

## Step 4: Configure Webhook

### Production Setup

1. Deploy TestForge with the Teams bot service accessible at a public HTTPS endpoint
2. Ensure port 3978 (or your configured port) is accessible
3. Your webhook URL will be: `https://your-domain.com/api/messages`

### Local Development with ngrok

For local testing, use ngrok to create a tunnel:

```bash
# Start ngrok (in a separate terminal)
ngrok http 3978
```

Note the HTTPS URL provided by ngrok (e.g., `https://abc123.ngrok.io`).

Your webhook URL will be: `https://abc123.ngrok.io/api/messages`

### Register Webhook in Azure

1. Go to your bot in Azure Portal
2. Navigate to **Configuration**
3. In **Messaging endpoint**, enter your webhook URL:
   - Production: `https://your-domain.com/api/messages`
   - ngrok: `https://<ngrok-id>.ngrok.io/api/messages`
4. Click **Apply** or **Save**

---

## Step 5: Enable Teams Channel

1. In your bot's Azure resource page, go to **Channels**
2. Click **Microsoft Teams** icon
3. Accept the Terms of Service
4. Configure channel settings:
   - **Messaging**: Enable messaging
   - **Calling**: Not required for TestForge
5. Click **Apply** or **Save**

### Add Bot to Teams

1. In the Teams channel configuration, click on the link to open in Teams
2. Or manually add the bot:
   - Open Microsoft Teams
   - Go to the channel where you want to use TestForge
   - Click the three dots (...) next to the channel name
   - Select **Manage channel** > **Connectors** or use **Apps**
   - Search for your bot by name
   - Click **Add** to add it to the team

---

## Step 6: Test the Bot

### Basic Health Check

```bash
# Check if Teams bot service is running
curl http://localhost:3978/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "teams-bot"
}
```

### Test in Teams

1. Open the Teams channel where you added the bot
2. Type a message to the bot (mention it if configured):
   ```
   @TestForge generate test for login flow
   ```
3. The bot should respond with acknowledgment

### Submit a Test Case

Send a structured message to the bot:

```
Test Case: User Login
Scope: Authentication Module
Steps:
1. Navigate to /login
2. Enter valid credentials
3. Click submit
Expected: User redirected to dashboard
```

---

## Troubleshooting

### Bot Not Responding

1. **Check service status**:
   ```bash
   curl http://localhost:3978/health
   ```

2. **Verify environment variables**:
   ```bash
   # Check if variables are set
   docker exec <container> env | grep TEAMS
   ```

3. **Check logs**:
   ```bash
   docker-compose logs teams-bot
   ```

### Authentication Errors

- Verify `TEAMS_APP_ID` matches the App ID in Azure Portal
- Verify `TEAMS_APP_PASSWORD` is the **Value** (not Secret ID) of the client secret
- Ensure the secret hasn't expired

### Webhook Not Receiving Messages

1. **Verify endpoint URL** in Azure matches your actual endpoint
2. **Check ngrok status** if using local development:
   ```bash
   # Ensure ngrok is running
   ngrok http 3978
   ```
3. **Check firewall** allows incoming connections on port 3978

### Bot Added but No Messages Received

- Ensure Teams channel is properly enabled in Azure
- Check that the bot has necessary permissions in the Teams channel
- Try removing and re-adding the bot to the channel

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid App ID or Password | Verify credentials in `.env` |
| `403 Forbidden` | Bot not enabled for Teams | Enable Teams channel in Azure |
| `502 Bad Gateway` | Service not running or wrong port | Start Teams bot service |
| `503 Service Unavailable` | Webhook endpoint not reachable | Check ngrok or public endpoint |

---

## Security Considerations

### App Password Security

- **Never commit** the App Password to version control
- Store in `.env` file (included in `.gitignore`)
- Rotate secrets periodically via Azure Portal
- Use Azure Key Vault for production deployments

### Endpoint Security

- Always use HTTPS in production
- Validate incoming requests using Microsoft's authentication
- Rate limit requests to prevent abuse

### Data Handling

- Test case data may contain sensitive information
- Ensure proper data handling in your TestForge deployment
- Follow your organization's data governance policies

### Permissions

- Grant minimum required permissions to the bot
- Review and audit bot permissions regularly
- Consider using app-only permissions for specific scenarios

---

## Additional Resources

- [Microsoft Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Bot Framework SDK](https://github.com/microsoft/botframework-sdk)
- [ngrok Documentation](https://ngrok.com/docs)
- [TestForge API Documentation](./api.md)

---

## Support

For issues with:
- **TestForge**: Contact the QA automation team
- **Azure/Teams**: Consult your Azure administrator or Microsoft support
