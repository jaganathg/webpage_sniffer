# VHS Appointment Checker - Complete Deployment Guide

## Overview

This system automatically monitors the VHS Darmstadt website for available Einbürgerungstest appointments and sends email notifications when appointments are found.

**Schedule**: Runs every 10 minutes, but only checks on:
- **Days**: Monday, Tuesday, Thursday
- **Time**: 7:00 AM - 4:00 PM (German time - Europe/Berlin)

**Email**: Sends notification to `any valid email` via Outlook.com connector

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Function App                       │
│                  (vhs-appointment-checker)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Timer Trigger (vhs_appointment_timer)              │   │
│  │  - Runs every 10 minutes                             │   │
│  │  - Checks day/time restrictions                      │   │
│  │  - Scrapes VHS website                               │   │
│  │  - Sends notification if appointments found          │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           │ (if appointments found)          │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HTTP Trigger (vhs_monitor)                         │   │
│  │  - Manual testing endpoint                           │   │
│  │  - URL: /api/vhs-monitor                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP POST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Logic App (logic-vhs-email-notifier)         │
│  - Receives HTTP request                                     │
│  - Sends email via Outlook.com connector                    │
│  - To: requester email account                                   │
│  - Subject: "VHS Appointment Available!"                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Azure Resources

### Resource Group: `rg-vhs-appointment-checker`
Location: West Europe

**Resources:**
1. **Function App**: `vhs-appointment-checker`
   - Runtime: Python 3.12
   - Plan: Consumption (Linux)
   - Cost: ~$0.50-1.50/month

2. **Storage Account**: `stvhschecker1761229501`
   - Used by Function App
   - Cost: ~$0.30/month

3. **Application Insights**: `vhs-appointment-checker`
   - For monitoring and logs
   - Cost: Free tier (minimal)

4. **Logic App**: `logic-vhs-email-notifier`
   - Type: Consumption
   - Cost: ~$0.10-0.50/month

**Total Monthly Cost**: ~$1-2 USD

---

## Configuration

### Environment Variables (Function App)

| Name | Value | Purpose |
|------|-------|---------|
| `LOGIC_APP_URL` | `https://prod-202.westeurope.logic.azure.com:443/workflows/...` | Logic App HTTP endpoint |
| `FUNCTIONS_WORKER_RUNTIME` | `python` | Runtime environment |
| `FUNCTIONS_EXTENSION_VERSION` | `~4` | Functions runtime version |

### Schedule Configuration

**Timer Expression**: `0 */10 * * * *` (NCRONTAB format)
- Runs every 10 minutes

**Day/Time Restrictions** (in code):
```python
# Days: Monday=0, Tuesday=1, Thursday=3
allowed_days = [0, 1, 3]

# Time: 07:00 - 16:00 German time
is_allowed_time = 7 <= current_hour < 16
```

---

## How to Monitor the System

### 1. Check Function Execution Logs

**Via Azure Portal:**
1. Go to Azure Portal → `vhs-appointment-checker`
2. Click **Functions** → `vhs_appointment_timer`
3. Click **Monitor** or **Invocations**
4. View recent executions with timestamps and status

**Via Application Insights:**
1. Go to `vhs-appointment-checker` → **Application Insights**
2. Click **Logs** (under Monitoring)
3. Run query:
```kusto
traces
| where timestamp > ago(24h)
| where message contains "VHS"
| project timestamp, message, severityLevel
| order by timestamp desc
```

### 2. Check Logic App Runs

1. Go to Azure Portal → `logic-vhs-email-notifier`
2. Click **Overview**
3. Scroll down to **Runs history**
4. Click on any run to see detailed execution flow
5. Check if email action succeeded

### 3. Test Manually

**Test HTTP Endpoint:**
```bash
curl https://vhs-appointment-checker.azurewebsites.net/api/vhs-monitor
```

**Expected Response:**
```json
{
  "appointments_available": false,
  "timestamp": "2025-10-23T17:00:00+02:00",
  "url": "https://www.darmstadt-vhs.de/einbuergerungstest",
  "status": "success"
}
```

**Test Logic App (send test email):**
```bash
curl -X POST "https://prod-202.westeurope.logic.azure.com:443/workflows/7c81c97d8ed7417ca754e17097e86657/triggers/When_an_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_an_HTTP_request_is_received%2Frun&sv=1.0&sig=mF4u0CjRvleLJG2odG61PFM_e03BaxpNxr08hJMmxVg" \
-H "Content-Type: application/json" \
-d '{"appointments_available": true, "timestamp": "2025-10-23T17:15:00+02:00", "url": "https://www.darmstadt-vhs.de/einbuergerungstest", "status": "success"}'
```

### 4. Set Up Alerts (Optional)

**Create an alert for failed executions:**
1. Go to Function App → **Alerts**
2. Click **+ New alert rule**
3. Configure:
   - Signal: Function execution failed
   - Threshold: Greater than 0
   - Action: Send email to your address

---

## How to Pause/Stop the Automation

### Option 1: Disable the Timer Trigger (Recommended)

**Via Azure Portal:**
1. Go to `vhs-appointment-checker` → **Functions**
2. Click on `vhs_appointment_timer`
3. Click **Overview** → **Disable** button at the top
4. Confirm

**To Re-enable:**
- Same steps, but click **Enable** button

**Via Azure CLI:**
```bash
# Disable
az functionapp config appsettings set \
  --name vhs-appointment-checker \
  --resource-group rg-vhs-appointment-checker \
  --settings "AzureWebJobs.vhs_appointment_timer.Disabled=true"

# Enable
az functionapp config appsettings set \
  --name vhs-appointment-checker \
  --resource-group rg-vhs-appointment-checker \
  --settings "AzureWebJobs.vhs_appointment_timer.Disabled=false"
```

### Option 2: Stop the Entire Function App

**Via Azure Portal:**
1. Go to `vhs-appointment-checker` → **Overview**
2. Click **Stop** button at the top
3. Confirm

**Note**: This stops ALL functions, including the HTTP endpoint for testing.

**To Restart:**
- Click **Start** button

**Via Azure CLI:**
```bash
# Stop
az functionapp stop \
  --name vhs-appointment-checker \
  --resource-group rg-vhs-appointment-checker

# Start
az functionapp start \
  --name vhs-appointment-checker \
  --resource-group rg-vhs-appointment-checker
```

### Option 3: Delete Resources (Permanent)

**To completely remove everything:**

```bash
# Delete entire resource group (removes all resources)
az group delete \
  --name rg-vhs-appointment-checker \
  --yes
```

**Warning**: This is permanent and removes:
- Function App
- Storage Account
- Logic App
- Application Insights
- All data and logs

---

## Troubleshooting

### Email Not Received

**Check 1: Spam Folder**
- Emails from Logic App may go to spam initially
- Mark sender as "Not Spam" to receive future emails in inbox

**Check 2: Logic App Execution**
1. Go to Logic App → **Run history**
2. Click on the run
3. Check if "Send an email" action succeeded
4. If failed, check error message

**Check 3: Email Address**
- Verify email is set to: `any valid email`
- Check Logic App workflow → "Send an email" action → "To" field

### Function Not Running

**Check 1: Function Status**
- Go to Function App → **Functions**
- Verify `vhs_appointment_timer` shows "Enabled"

**Check 2: Schedule Restrictions**
- Remember: Only runs Mon/Tue/Thu, 7 AM - 4 PM German time
- Check current time in German timezone

**Check 3: Application Logs**
```bash
# View live logs
az webapp log tail \
  --name vhs-appointment-checker \
  --resource-group rg-vhs-appointment-checker
```

### Authentication Errors (HTTP 401)

If you get 401 errors when testing HTTP endpoint:
- The function should have `auth_level=func.AuthLevel.ANONYMOUS`
- Check [function_app.py](function_app.py) line 151

### Deployment Issues

**If deployment fails:**

1. **Check Azure CLI login:**
```bash
az account show
```

2. **Redeploy:**
```bash
cd /Users/{users}/Documents/J_Study/Python/webpage_sniffer
func azure functionapp publish vhs-appointment-checker --build remote
```

3. **View deployment logs:**
- In VS Code, check Output panel (Azure Functions extension)

---

## How to Update the Code

### 1. Modify Local Code

Edit [function_app.py](function_app.py) with your changes.

### 2. Test Locally

```bash
cd /Users/{users}/J_Study/Python/webpage_sniffer
func start
```

Test at: `http://localhost:7071/api/vhs-monitor`

### 3. Deploy to Azure

```bash
func azure functionapp publish vhs-appointment-checker --build remote
```

### 4. Verify Deployment

```bash
# Test live endpoint
curl https://vhs-appointment-checker.azurewebsites.net/api/vhs-monitor
```

---

## Common Modifications

### Change Schedule

**Edit timer expression in [function_app.py](function_app.py:114):**

```python
# Current: Every 10 minutes
@app.timer_trigger(schedule="0 */10 * * * *", ...)

# Every 5 minutes
@app.timer_trigger(schedule="0 */5 * * * *", ...)

# Every 30 minutes
@app.timer_trigger(schedule="0 */30 * * * *", ...)

# Every hour
@app.timer_trigger(schedule="0 0 * * * *", ...)
```

**NCRONTAB Format**: `{second} {minute} {hour} {day} {month} {day-of-week}`

### Change Days/Time

**Edit in [function_app.py](function_app.py:74-78):**

```python
# Days (0=Monday, 1=Tuesday, ..., 6=Sunday)
allowed_days = [0, 1, 3]  # Mon, Tue, Thu

# Change to Mon-Fri
allowed_days = [0, 1, 2, 3, 4]

# Time (24-hour format)
is_allowed_time = 7 <= current_hour < 16  # 7 AM - 4 PM

# Change to 8 AM - 6 PM
is_allowed_time = 8 <= current_hour < 18
```

### Change Email Recipient

**Via Azure Portal:**
1. Go to `logic-vhs-email-notifier`
2. Click **Logic app designer**
3. Click on "Send an email (V2)" action
4. Update "To" field
5. Click **Save**

### Change Email Content

**Via Azure Portal:**
1. Go to `logic-vhs-email-notifier`
2. Click **Logic app designer**
3. Click on "Send an email (V2)" action
4. Update "Subject" and "Body" fields
5. Click **Save**

---

## Cost Management

### Monitor Costs

1. Go to Azure Portal → **Cost Management + Billing**
2. Click **Cost analysis**
3. Filter by Resource Group: `rg-vhs-appointment-checker`

### Expected Costs

| Resource | Usage | Cost/Month |
|----------|-------|------------|
| Function App | ~4,320 executions/month (10 min × 9 hours × 3 days × 4 weeks) | $0.50-1.50 |
| Storage | Minimal | $0.30 |
| Logic App | ~50-100 runs/month (when appointments found) | $0.10-0.50 |
| Application Insights | Free tier | $0.00 |
| **Total** | | **~$1-2** |

### Reduce Costs

1. **Reduce execution frequency**
   - Change from every 10 minutes to every 30 minutes
   - Saves ~66% on execution costs

2. **Narrow time window**
   - Only run 9 AM - 3 PM instead of 7 AM - 4 PM
   - Saves ~33% on execution costs

3. **Disable when not needed**
   - Pause during vacation periods
   - Resume when needed

---

## Security Best Practices

### Current Security

✅ **Function App**:
- HTTP endpoint: Anonymous (for testing)
- Timer trigger: No external access needed

✅ **Logic App**:
- HTTP endpoint: Includes SAS token in URL
- Only accessible with correct URL

✅ **Secrets**:
- Logic App URL stored in Function App environment variables
- Not exposed in code

### Recommendations

1. **Email Security**:
   - Mark Logic App sender as trusted in Gmail
   - Use a dedicated email if needed

2. **Monitor Access**:
   - Review Function App logs regularly
   - Check Logic App run history

3. **Update Dependencies**:
   - Keep Python packages updated
   - Monitor security advisories

---

## Maintenance Checklist

### Weekly
- [ ] Check email delivery (verify emails received when appointments found)
- [ ] Review Function App logs for errors

### Monthly
- [ ] Review Azure costs
- [ ] Check Application Insights for performance issues
- [ ] Test HTTP endpoint manually

### Quarterly
- [ ] Update Python dependencies in [requirements.txt](requirements.txt)
- [ ] Review and optimize schedule if needed
- [ ] Verify Logic App OAuth connection is still valid

---

## Support and Resources

### Azure Resources
- [Azure Functions Documentation](https://docs.microsoft.com/en-us/azure/azure-functions/)
- [Logic Apps Documentation](https://docs.microsoft.com/en-us/azure/logic-apps/)
- [Application Insights Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)

### Local Project Files
- **Main Code**: [function_app.py](function_app.py)
- **Dependencies**: [requirements.txt](requirements.txt)
- **Configuration**: [host.json](host.json), [local.settings.json](local.settings.json)
- **This Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Contact
For issues or questions about the VHS website or appointments, contact:
- VHS Darmstadt: https://www.darmstadt-vhs.de/kontakt

---

## Quick Reference Commands

### Check Status
```bash
# Function App status
az functionapp show --name vhs-appointment-checker --resource-group rg-vhs-appointment-checker --query "state" -o tsv

# Test HTTP endpoint
curl https://vhs-appointment-checker.azurewebsites.net/api/vhs-monitor
```

### Start/Stop
```bash
# Stop Function App
az functionapp stop --name vhs-appointment-checker --resource-group rg-vhs-appointment-checker

# Start Function App
az functionapp start --name vhs-appointment-checker --resource-group rg-vhs-appointment-checker
```

### Deploy
```bash
# Deploy updates
cd /Users/{users}/Documents/J_Study/Python/webpage_sniffer
func azure functionapp publish vhs-appointment-checker --build remote
```

### Logs
```bash
# View Application Insights logs (via Azure Portal)
# Go to: vhs-appointment-checker → Monitoring → Logs

# Sample query:
traces
| where timestamp > ago(1h)
| where message contains "VHS" or message contains "appointment"
| project timestamp, message, severityLevel
| order by timestamp desc
```

---

## Appendix: Logic App Workflow JSON

The Logic App workflow is configured with:

**Trigger**: When a HTTP request is received
- Method: POST
- URL: (auto-generated with SAS token)

**Action**: Send an email (V2)
- Connection: Outlook.com
- To: valid email
- Subject: VHS Appointment Available!
- Body: The VHS appointment is available, book your slots now!

To view/edit the JSON:
1. Go to Logic App → **Logic app code view**
2. View or edit the workflow definition

---

**Document Version**: 1.0
**Last Updated**: October 23, 2025
**System Status**: ✅ Live and Running
