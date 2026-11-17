---
name: salon-voice-ai-agent
displayName: Salon AI Voice Receptionist & Owner OS
description: Autonomous 24/7 AI voice receptionist and omnichannel front-office OS for salons & spas. Answers calls in sub-500ms, books & reschedules appointments, manages Instagram/WhatsApp DMs, pacifies angry clients, automates 6-hr reviews, and generates daily EBITDA reports.
version: 1.0.0
author: Kishor Kumar Paroi
homepage: https://ai-voice-receptionist.kishor.tech
repository: https://github.com/KishorKumarParoi/omnichannel-ai-receptionist
license: Proprietary / Commercial
tags:
  - voice-agent
  - salon
  - appointment-booking
  - omnichannel
  - vapi
  - telephony
  - crm
  - ebitda
allowed-tools:
  - Bash
  - WebFetch
  - ReadFile
  - WriteFile
---

# Salon AI Voice Receptionist & Owner OS

A production-grade, 24/7 autonomous AI voice receptionist, omnichannel messaging concierge, and front-office operating system engineered for luxury salons, spas, barbershops, and aesthetics clinics across the **United States, United Kingdom, Canada, and Europe**.

Replaces $15,000+/month in front-desk shift payroll, missed-call revenue leaks, and manual scheduling friction with a sub-500ms voice agent connected directly to a multi-tenant booking calendar, omnichannel inbox, and automated marketing engine.

---

## 🌟 Core Architectural Capabilities

### 1. 🎙️ 24/7 Sub-500ms Natural Human Voice Concierge
- **Ultra-Low Latency Voice Pipeline**: Powered by Vapi.ai, Deepgram Nova-2 STT, Anthropic Claude 3.5 Sonnet, and ElevenLabs / Cartesia neural voice synthesis.
- **Interruption & Turn-Taking Tolerance**: Allows callers to change their mind mid-sentence, ask questions about stylist specialties, or interrupt naturally without robotic delay.
- **Multi-Accent Support**:
  - `red_american`: Rachel / Sofia (Southern / US Contemporary)
  - `european_british`: Lily (British English RP)
  - `indian_english`: Priya (Indian English)
  - `african_english`: Amina (African English)

### 2. 📅 Autonomous Calendar Booking & Conflict Resolution
- Real-time availability checks across multiple stylists, chairs, and service categories (e.g., Balayage: 180 mins; Haircut & Blowout: 60 mins; Men's Fade: 30 mins).
- Prevents double-bookings with PostgreSQL / SQLite transaction locks.
- Performs conversational rescheduling and cancellations instantly via caller phone number lookup.

### 3. 📱 Unified Omnichannel Inbox (WhatsApp, Instagram, Messenger)
- Automatically ingests and responds to night-time DMs on Instagram, Facebook Messenger, and WhatsApp Business.
- Guides social followers directly to confirmed appointment bookings with calendar links.

### 4. 🤝 Emotionally Calibrated Angry Customer Pacifier
- Calibrated de-escalation protocols: validates frustrated callers with active empathy.
- Executes credit-matching rules or immediate priority re-booking.
- Dispatches instantaneous priority alerts with full audio recordings and transcripts to the owner's private Slack channel (`#manager-escalations`).

### 5. ⭐ Automated 6-Hour Review Harvester
- Exactly 6 hours post-service, triggers an automated SMS and email review check-in.
- Satisfied clients receive a direct 1-click link to leave a 5-star Google Maps review.
- Dissatisfied clients are privately routed to salon management before negative reviews go public.

### 6. 🔁 15-Day Autonomous Voice Retention Calls
- Autonomously calls past clients at the 15-day mark to check in on service longevity (color vibrancy, haircut maintenance) and proactively locks in their next appointment.

### 7. 📊 Executive OwnerOS & Daily EBITDA Reports
- **9:00 PM Daily Digest**: Delivers total appointments booked, stylist utilization, and revenue pipeline directly to the owner's email.
- **1st-of-Month EBITDA Analysis**: Powered by Claude 3 Opus to calculate exact net profit, customer acquisition costs, and channel attribution.

---

## 🛠️ Tool Calling & Webhook Specification

The AI agent executes structured tools during live conversations via HTTP POST webhooks to `/webhook/vapi-tools`:

| Tool Function | Description | Key Parameters |
| :--- | :--- | :--- |
| `check_availability` | Queries open slots for a specific stylist and service date. | `service_name`, `stylist_name`, `date` |
| `book_appointment` | Commits booking to database and triggers SMS/Email confirmation. | `customer_name`, `customer_phone`, `service_name`, `stylist_name`, `date`, `start_time` |
| `reschedule_appointment` | Moves existing reservation to a new validated slot. | `customer_phone`, `old_date`, `new_date`, `new_time` |
| `cancel_appointment` | Frees up chair slot and logs cancellation reason. | `customer_phone`, `date`, `reason` |
| `escalate_to_slack` | Notifies owner immediately of angry client or VIP escalation. | `customer_name`, `customer_phone`, `issue_summary`, `severity` |

---

## ⚙️ Environment Variables Setup

Ensure the following environment keys are configured in your deployment:

```bash
# Telephony & Voice Pipeline (Vapi & Telnyx)
VAPI_PRIVATE_API_KEY=your_vapi_api_key
VAPI_PHONE_NUMBER_ID=your_vapi_phone_id
TELNYX_API_KEY=your_telnyx_api_key
TELNYX_PHONE_NUMBER=+16172718180

# LLM Reasoning & Intelligence
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Database & Multi-Tenant Auth
DATABASE_URL=postgresql://user:pass@ep-dummy.neon.tech/neondb?sslmode=require
CLERK_SECRET_KEY=sk_live_your_clerk_secret

# Communications & Notifications
RESEND_API_KEY=re_your_resend_api_key
SLACK_BOT_TOKEN=xoxb-your_slack_bot_token
SLACK_ESCALATION_CHANNEL=#manager-escalations
```

---

## 📖 Companion References

- **Telephony & Vapi Setup**: See `references/telephony_vapi.md`
- **System Prompts**: See `prompts/sofia_system_prompt.md`
- **Unit Economics & P&L Blueprint**: See `references/cost_and_unit_economics.md`
