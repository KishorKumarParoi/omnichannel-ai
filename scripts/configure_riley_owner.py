#!/usr/bin/env python3
"""
Configures Riley as Owner & Managing Partner of Luxe Salon & Spa
and seamlessly integrates Riley into the 6-Member Executive Squad.
"""

import os
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

API_KEY = os.getenv("VAPI_PRIVATE_API_KEY", "4ea8ab8e-44c0-4903-a867-3d36ac3e185a").strip()
SQUAD_ID = os.getenv("VAPI_SQUAD_ID", "2af8a077-0d73-4893-ad7a-0a981f70e646").strip()

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

RILEY_ID = "681e654e-e071-43b8-a419-22be6886233a"
SOPHIA_ID = os.getenv("VAPI_SOPHIA_ASSISTANT_ID", "960a1e4a-69ee-41c6-a811-38986bea5312").strip()
MARCUS_ID = os.getenv("VAPI_MARCUS_ASSISTANT_ID", "fa6948ca-b3a8-46be-bc5b-6d251c8536ae").strip()
KISHOR_ID = os.getenv("VAPI_KISHOR_ASSISTANT_ID", "e7dfddf5-3618-4d2f-8e1f-0babb3b232ae").strip()
TASNIM_ID = os.getenv("VAPI_TASNIM_ASSISTANT_ID", "b7dc9948-8bf7-4eef-b1e3-bffaa2d9ac0d").strip()
RAIYAN_ID = os.getenv("VAPI_RAIYAN_ASSISTANT_ID", "2733cdb5-6cfa-4c4e-bd85-bf2b6ccdfbab").strip()

SERVER_URL = "https://ai-voice-receptionist.kishor.tech/webhook/vapi-tools"

RILEY_PROMPT = """# Identity & Executive Leadership Persona
You are Riley, Owner & Managing Partner of Luxe Salon & Spa on Newbury Street in Boston's historic Back Bay.
You are charismatic, deeply hospitable, visionary, and authoritative. You treat every caller as an esteemed VIP guest of your salon.

# Responsibilities & Domain
1. Executive Concierge: You have full authority to book VIP reservations, approve custom package rates, reserve private suites, and guarantee exceptional 5-star experiences.
2. Collaboration with Leadership:
   - Marcus Vance: Your Creative Director & Master Colorist (consultations, color corrections, luxury balayage).
   - Sophia: Your Lead Concierge & Front Desk Manager (routine bookings, availability, front desk).
   - Kishor Paroi: AI Forward Deployment Engineer (tech systems, digital passes, booking portal).
   - Tasnim: Head of Sales (bridal groups, corporate packages, commercial contracts).
   - Raiyan: Director of Communications (PR, media, high-profile clientele relations).

# Conversational Protocol
- Greet with executive warmth: "Hello, this is Riley, owner of Luxe Salon on Newbury Street. I'm delighted to personally assist you—how may I elevate your salon experience today?"
- Listen attentively, answer questions about salon philosophy, services, and master stylists.
- When guests want to reserve appointments, seamlessly invoke `check_availability` and `book_appointment`.
- If the guest needs routine front-desk reception or standard check-ins, you can warmly transfer them to Sophia.
- If the guest needs deep master color or haircut consultation, transfer to Marcus Vance.

# ⏱️ MANDATORY CALL DURATION & COST-SAVING PACING RULES:
1. Target Resolution within 3-5 Minutes:
   - Proactively guide the guest toward a confirmed booking or clear resolution.
   - By 5 minutes: "To ensure we secure your preferred time with our team today, shall we go ahead and finalize your reservation?"
2. Approaching 10 Minutes:
   - If undecided: "I want to be completely respectful of your time—shall we lock this in now, or may I text you our VIP reservation pass directly?"
3. Hard Cutoff by 15 Minutes:
   - Conclude warmly and invoke the `end_call` tool. The telephony line hard-disconnects at 15 minutes (900s).
"""

def main():
    print("=" * 75)
    print("👑 PROVISIONING RILEY AS SALON OWNER & UPGRADING SQUAD")
    print("=" * 75)

    with httpx.Client(base_url="https://api.vapi.ai", headers=HEADERS, timeout=45.0) as client:
        # 1. Fetch Tools to bind to Riley
        tools_res = client.get("/tool").json()
        tools_list = tools_res if isinstance(tools_res, list) else tools_res.get("results", [])
        common_tool_ids = [
            t["id"] for t in tools_list
            if (t.get("function", {}).get("name") or t.get("name") or t.get("type")) in [
                "check_availability", "book_appointment", "lookup_appointment",
                "reschedule_appointment", "cancel_appointment", "send_text",
                "query_knowledge_base", "update_customer_details", "end_call"
            ]
        ]
        print(f"✓ Found {len(common_tool_ids)} tools to attach to Riley.")

        # 2. Update Riley
        print("\n✨ Upgrading Riley's Assistant Profile...")
        riley_payload = {
            "name": "Luxe Salon Owner - Riley",
            "firstMessage": "Hello, this is Riley, owner and managing partner of Luxe Salon on Newbury Street. It's an absolute pleasure to speak with you—how can I personally elevate your salon experience today?",
            "firstMessageMode": "assistant-speaks-first",
            "serverUrl": SERVER_URL,
            "server": {"url": SERVER_URL},
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM" # Rachel - polished, warm luxury tone
            },
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2",
                "language": "en"
            },
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": RILEY_PROMPT}
                ],
                "toolIds": common_tool_ids
            },
            "maxDurationSeconds": 900,
            "silenceTimeoutSeconds": 20,
            "backgroundDenoisingEnabled": True
        }

        r_up = client.patch(f"/assistant/{RILEY_ID}", json=riley_payload)
        if r_up.status_code == 200:
            print(f"✅ Riley upgraded successfully as Owner ({RILEY_ID})!")
        else:
            print(f"⚠️ Error updating Riley: {r_up.text}")

        # 3. Configure 6-Member Squad with Bidirectional Handoffs
        print("\n🌐 Upgrading Squad to 6-Member Leadership Squad...")
        canonical_members = [
            {
                "assistantId": SOPHIA_ID,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Owner - Riley", "description": "Transfer to Riley, Salon Owner & Managing Partner, for VIP guest accommodations, owner-level decisions, private salon buyouts, or executive escalations."},
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus Vance for master hair coloring, balayage, or creative director consultations."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for engineering, software automation, technical setup, or digital pass integrations."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for bridal group packages, commercial contracts, or wholesale salon programs."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for corporate communications, press inquiries, or VIP correspondence."}
                ]
            },
            {
                "assistantId": MARCUS_ID,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Owner - Riley", "description": "Transfer to Riley, Salon Owner, for executive approvals, VIP suite reservations, or owner consultations."},
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer to Sophia for standard salon bookings, front desk check-in, or reception scheduling."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for tech support, integration issues, or appointment system customizations."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for bridal group pricing, commercial packages, or salon partnerships."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for client feedback, VIP correspondence, or communications."}
                ]
            },
            {
                "assistantId": RILEY_ID,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer to Sophia for routine front-desk appointments, check-ins, or reception bookings."},
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus Vance for master stylist coloring, balayage formulation, or creative hair consultations."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for technical feasibility, software setup, API integration, or automation."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for sales inquiries, luxury bridal packages, or corporate memberships."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for PR, media inquiries, partner relations, or client satisfaction."}
                ]
            },
            {
                "assistantId": KISHOR_ID,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Owner - Riley", "description": "Transfer to Riley, Salon Owner, for executive approvals or owner inquiries."},
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer to Sophia for standard salon bookings, front desk check-in, or reception."},
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus for master styling, hair coloring, balayage, or salon creative direction."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for enterprise sales contracts, commercial package deals, or pricing tiers."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for corporate communications, client relations, or executive escalations."}
                ]
            },
            {
                "assistantId": TASNIM_ID,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Owner - Riley", "description": "Transfer to Riley, Salon Owner, for high-value contract approvals or VIP partner onboarding."},
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer to Sophia for routine salon appointments, nails, facials, or reception scheduling."},
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus for custom styling consultations, color formulation, or hair design."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for technical feasibility, software setup, API integration, or automation."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for PR, media inquiries, partner relations, or client satisfaction."}
                ]
            },
            {
                "assistantId": RAIYAN_ID,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Owner - Riley", "description": "Transfer to Riley, Salon Owner, for executive statements, VIP owner escalations, or strategic partnerships."},
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer to Sophia for regular appointment bookings, front-desk check-ins, or general reception."},
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus for stylist consultations, hair coloring, or salon director advice."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for technical issues, system software questions, or integrations."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for sales inquiries, luxury packages, or corporate memberships."}
                ]
            }
        ]

        squad_payload = {
            "name": "Luxe Frontfoot 6-Member Leadership Squad",
            "members": canonical_members
        }

        s_patch = client.patch(f"/squad/{SQUAD_ID}", json=squad_payload)
        if s_patch.status_code == 200:
            print(f"✅ Squad upgraded to 6-Member Leadership Squad with Riley ({SQUAD_ID})!")
        else:
            print(f"⚠️ Error updating Squad: {s_patch.text}")

    # 4. Save to .env
    set_key(str(ENV_PATH), "VAPI_RILEY_ASSISTANT_ID", RILEY_ID)
    print("✓ Persisted VAPI_RILEY_ASSISTANT_ID to .env")

    print("\n" + "=" * 75)
    print("🎉 RILEY SUCCESSFULLY CONFIGURED AS SALON OWNER & ADDED TO SQUAD!")
    print(f"   Riley Assistant ID:  {RILEY_ID}")
    print(f"   Squad ID:            {SQUAD_ID}")
    print("=" * 75)

if __name__ == "__main__":
    main()
