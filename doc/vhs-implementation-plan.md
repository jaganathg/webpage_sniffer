# VHS Darmstadt Appointment Monitoring System - Simplified and Scalable Implementation Plan

## Executive Summary

### Project Overview
An automated monitoring system for the VHS Darmstadt citizenship test (Einbürgerungstest) appointment booking platform. The system continuously checks for available appointment slots and instantly notifies registered users when slots become available, solving the challenge of high demand and limited availability.

### Business Problem
- Citizenship test appointments are released irregularly on the VHS Darmstadt website.
- Extremely high demand with limited slots available.
- Manual checking is time-consuming and often unsuccessful.
- Users miss opportunities due to delayed awareness of slot availability.

### Simplified Solution Approach
Start with a local Python script that detects appointment availability, then progressively move to Azure Cloud using either Logic Apps or Container Instances. The system will evolve through stages — from a simple local prototype to a fully automated cloud-based service.

## Implementation Phases (Simplified Roadmap)

### Phase 0: Local Script Proof (Initial Focus)

#### Objective
Develop a minimal Python script that can detect appointment availability and verify correct logic locally.

#### Plan
- Use Python 3.11+.
- Libraries: `requests`, `BeautifulSoup4`, `smtplib` (for email testing).
- Fetch HTML from the target page (https://www.darmstadt-vhs.de/einbuergerungstest).
- Detect if the red-box section (appointment availability) exists.
- Print or log output: "Available" / "Not available".
- Optional: Send an email to yourself when availability is detected.

#### Validation
- Run periodically using Windows Task Scheduler or cron.
- Verify that detection matches manual checks.

**Cost:** Free (local testing only)

---

### Phase 1: Core Detection Script Development (Enhanced Local Version)

#### Objective
Refine the detection logic for all possible scenarios and improve script robustness.

#### Features
- Handle scenarios: section missing, inactive, active, or error states.
- Add retry logic for network issues.
- Capture console logs or screenshots (optional, for debugging).
- Keep the script lightweight (<60s execution).

#### Output
- Local logs for availability history.
- Email notification upon detection (optional).

**Cost:** Free (local testing only)

---

### Phase 2: Minimal Azure Cloud Setup (Simple Automation)

#### Objective
Migrate the working script to Azure using minimal infrastructure.

#### Option A: Azure Logic Apps (Low-Code)
- Create a Logic App with:
  - Timer trigger (every 5–10 minutes).
  - HTTP request step to trigger a Python function or endpoint.
  - Email notification (Outlook or SendGrid connector).
- Logic App runs the Python script in Azure Function backend.

**Cost:** ~€0.50–1.00/month

#### Option B: Azure Container Instance (More Control)
- Package your script in a lightweight Docker container.
- Deploy to Azure Container Instances (ACI).
- Schedule execution using Azure Function or Logic App.

**Recommended Configuration:**
- 1 vCPU, 1.5GB RAM (Linux image preferred).
- Runtime: Python 3.11-slim base image.
- Environment variables for configuration.

**Cost:** ~€1–1.50/month

#### Notifications
- Use SendGrid (Free Tier) for up to 100 emails/day.
- Keep notification message simple and time-stamped.

**Example:**
```
Subject: VHS Appointment Available!
Body: A new appointment has been detected at {timestamp}. Visit the website immediately.
```

---

### Phase 3: Extended Azure Infrastructure (Future Upgrade)

After validating that your basic setup works, progressively add:
- **Azure Table Storage:** Save appointment history and detection logs.
- **Azure Blob Storage:** Store screenshots and debug logs.
- **Application Insights:** Monitor performance and errors.
- **Advanced Scheduling:** Peak/off-peak adjustment using CRON.

**Cost:** ~€1.40–2.00/month

---

### Phase 4: Monitoring & Optimization

- Enable Application Insights once system is stable.
- Create basic dashboards for:
  - Detection success rate.
  - Email delivery success.
  - Execution time trends.
- Use budget alerts to cap monthly cost below €3.

---

## Cost Overview

| Component | Description | Monthly Cost |
|-----------|-------------|--------------|
| Local Testing | Run on your laptop | €0 |
| Azure Container Instance | 1 vCPU / 1.5GB RAM | €0.80 |
| Azure Logic App or Function | Scheduler | €0.50 |
| SendGrid | Free tier (100 emails/day) | €0 |
| **Total** | Fully functional setup | **≈ €1.30/month** |

---

## Future Enhancements

Once the minimal version is reliable, consider these upgrades:
1. **Notifications:** Add SMS or push notifications.
2. **Storage:** Keep appointment history in Azure Table Storage.
3. **Analytics:** Monitor trends and patterns in appointment availability.
4. **Multi-City Support:** Extend monitoring to other VHS locations.
5. **Machine Learning (Optional):** Predict appointment release patterns.

---

## Summary

This simplified plan provides a realistic starting path for developing and learning cloud automation using Azure while solving the VHS appointment problem.

**Short-term Goal:** Local detection script with console or email notification.

**Medium-term Goal:** Automated cloud execution using Azure Logic Apps or Container Instances.

**Long-term Goal:** Scalable cloud monitoring with full automation, notification, and analytics.

---

## Key Takeaways
- Start simple → verify locally → scale to Azure.
- Focus on fast detection and reliability first.
- Keep monthly cost under €2 while learning Azure automation.
- Gradually expand architecture as confidence grows.