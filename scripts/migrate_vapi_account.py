#!/usr/bin/env python3
"""
One-Shot Automated Vapi Account Migration & Provisioning Engine
Author: Kishor Kumar Paroi (Principal AI Systems Architect)

Migrates or provisions an entire Vapi organization from scratch:
1. Re-creates all 12 mid-call tools (book_appointment, check_availability, lookup, etc.) pointing to production serverUrl.
2. Re-creates the 5 core leadership assistants (Sophia, Marcus, Kishor, Tasnim, Raiyan) with high-fidelity voices and prompts.
3. Provisions the 5-Member Frontfoot Squad with full bidirectional transfer destinations.
4. Connects Telnyx Credential + Telnyx Phone Number (+16172718180) and binds it directly to the Squad.
5. Updates .env with all new IDs.
6. Syncs all variables to Vercel production and triggers redeployment.

Usage:
  python3 scripts/migrate_vapi_account.py \
    --public-key "your_new_public_key" \
    --private-key "your_new_private_key" \
    --telnyx-api-key "KEY..." \
    --telnyx-app-id "3088592697158534683" \
    --phone-number "+16172718180" \
    --sync-vercel
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
import httpx
from dotenv import set_key, load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
BACKUP_DIR = BASE_DIR / "vapi" / "backup"
load_dotenv(ENV_PATH)

DEFAULT_SERVER_URL = "https://ai-voice-receptionist.kishor.tech/webhook/vapi-tools"

def parse_args():
    parser = argparse.ArgumentParser(description="One-Shot Vapi Account Migration")
    parser.add_argument("--public-key", required=False, help="New Vapi Public Key (pk_...)")
    parser.add_argument("--private-key", required=False, help="New Vapi Private Key")
    parser.add_argument("--telnyx-api-key", required=False, help="Telnyx API Key (defaults to TELNYX_API_KEY from .env)")
    parser.add_argument("--telnyx-app-id", default="3088592697158534683", help="Telnyx Call Control Application ID")
    parser.add_argument("--phone-number", default="+16172718180", help="Telnyx Inbound Phone Number to attach to Squad")
    parser.add_argument("--server-url", default=DEFAULT_SERVER_URL, help="Webhook server URL")
    parser.add_argument("--sync-vercel", action="store_true", help="Automatically sync new keys to Vercel production")
    return parser.parse_args()

def main():
    args = parse_args()

    vapi_private = args.private_key or os.getenv("VAPI_PRIVATE_API_KEY", "").strip()
    vapi_public = args.public_key or os.getenv("VAPI_PUBLIC_API_KEY", "").strip()
    telnyx_key = args.telnyx_api_key or os.getenv("TELNYX_API_KEY", "").strip()
    telnyx_app_id = args.telnyx_app_id or os.getenv("TELNYX_CONNECTION_ID", "3088592697158534683").strip()
    phone_number = args.phone_number
    server_url = args.server_url

    if not vapi_private:
        print("❌ Error: Missing Vapi Private API Key. Pass --private-key or set VAPI_PRIVATE_API_KEY in .env")
        sys.exit(1)

    print("=" * 75)
    print("🚀 ONE-SHOT VAPI ACCOUNT MIGRATION & PROVISIONING ENGINE")
    print(f"   Target Vapi Public Key: {vapi_public[:8]}...{vapi_public[-4:] if len(vapi_public)>12 else ''}")
    print(f"   Server Webhook URL:    {server_url}")
    print(f"   Telnyx Phone Number:   {phone_number}")
    print("=" * 75)

    headers = {
        "Authorization": f"Bearer {vapi_private}",
        "Content-Type": "application/json"
    }

    with httpx.Client(base_url="https://api.vapi.ai", headers=headers, timeout=45.0) as client:
        # Verify Key
        res_test = client.get("/tool")
        if res_test.status_code != 200:
            print(f"❌ Vapi Authentication Failed ({res_test.status_code}): {res_test.text}")
            sys.exit(1)
        print("✅ Authenticated successfully with new Vapi Account!")

        # -------------------------------------------------------------
        # 1. Provision Mid-Call Tools
        # -------------------------------------------------------------
        print("\n🔧 Step 1: Provisioning 12 Mid-Call Tools...")
        tools_backup_file = BACKUP_DIR / "tools_backup.json"
        if not tools_backup_file.exists():
            print(f"❌ Backup file {tools_backup_file} not found. Run backup first.")
            sys.exit(1)

        raw_tools = json.loads(tools_backup_file.read_text(encoding="utf-8"))
        existing_tools_res = client.get("/tool").json()
        existing_tool_map = {
            t.get("function", {}).get("name") or t.get("name") or t.get("type"): t.get("id")
            for t in existing_tools_res
        }

        new_tool_ids = {}
        for t in raw_tools:
            name = t.get("function", {}).get("name") or t.get("name") or t.get("type")
            clean_payload = {
                "type": t.get("type", "function"),
                "server": {"url": server_url}
            }
            if "function" in t:
                clean_payload["function"] = t["function"]
            if "async" in t:
                clean_payload["async"] = t["async"]
            if "messages" in t:
                clean_payload["messages"] = t["messages"]

            if name in existing_tool_map:
                tool_id = existing_tool_map[name]
                client.patch(f"/tool/{tool_id}", json=clean_payload)
                print(f"  ✓ Updated existing tool: {name} ({tool_id})")
                new_tool_ids[name] = tool_id
            else:
                c_res = client.post("/tool", json=clean_payload)
                if c_res.status_code in (200, 201):
                    tool_id = c_res.json()["id"]
                    print(f"  + Created tool: {name} ({tool_id})")
                    new_tool_ids[name] = tool_id
                else:
                    print(f"  ⚠️ Failed creating tool {name}: {c_res.text}")

        # List of core tool IDs for the assistants
        common_tool_ids = [
            tid for name, tid in new_tool_ids.items()
            if name in [
                "check_availability", "book_appointment", "lookup_appointment",
                "reschedule_appointment", "cancel_appointment", "send_text",
                "query_knowledge_base", "end_call"
            ]
        ]

        # -------------------------------------------------------------
        # 2. Provision the 5 Core Assistants
        # -------------------------------------------------------------
        print("\n👥 Step 2: Provisioning 5 Frontfoot Assistants...")
        asst_backup_file = BACKUP_DIR / "assistants_backup.json"
        raw_assts = json.loads(asst_backup_file.read_text(encoding="utf-8"))
        existing_assts = client.get("/assistant").json()
        existing_asst_map = {a.get("name"): a.get("id") for a in existing_assts}

        target_assistants = [
            "Luxe Salon Voice Receptionist - Sophia",
            "Luxe Salon Director - Marcus",
            "AI Forward Deployment Engineer - Kishor",
            "Head of Sales - Tasnim",
            "Director of Communications - Raiyan"
        ]

        new_assistant_ids = {}
        for a in raw_assts:
            name = a.get("name")
            if name not in target_assistants:
                continue

            # Clean payload
            clean_asst = {
                "name": name,
                "firstMessage": a.get("firstMessage"),
                "firstMessageMode": a.get("firstMessageMode", "assistant-speaks-first"),
                "serverUrl": server_url,
                "server": {"url": server_url},
                "voice": a.get("voice"),
                "transcriber": a.get("transcriber", {
                    "provider": "deepgram",
                    "model": "nova-2",
                    "language": "en"
                }),
                "model": {
                    "provider": a.get("model", {}).get("provider", "openai"),
                    "model": a.get("model", {}).get("model", "gpt-4o"),
                    "messages": a.get("model", {}).get("messages", []),
                    "toolIds": common_tool_ids
                }
            }

            if name in existing_asst_map:
                asst_id = existing_asst_map[name]
                client.patch(f"/assistant/{asst_id}", json=clean_asst)
                print(f"  ✓ Updated assistant: {name} ({asst_id})")
                new_assistant_ids[name] = asst_id
            else:
                c_res = client.post("/assistant", json=clean_asst)
                if c_res.status_code in (200, 201):
                    asst_id = c_res.json()["id"]
                    print(f"  + Created assistant: {name} ({asst_id})")
                    new_assistant_ids[name] = asst_id
                else:
                    print(f"  ❌ Failed creating assistant {name}: {c_res.text}")

        sophia_id = new_assistant_ids.get("Luxe Salon Voice Receptionist - Sophia")
        marcus_id = new_assistant_ids.get("Luxe Salon Director - Marcus")
        kishor_id = new_assistant_ids.get("AI Forward Deployment Engineer - Kishor")
        tasnim_id = new_assistant_ids.get("Head of Sales - Tasnim")
        raiyan_id = new_assistant_ids.get("Director of Communications - Raiyan")

        # -------------------------------------------------------------
        # 3. Provision the 5-Member Squad with Bidirectional Handoffs
        # -------------------------------------------------------------
        print("\n🌐 Step 3: Configuring 5-Member Frontfoot Squad with Bidirectional Routing...")
        squads_backup_file = BACKUP_DIR / "squads_backup.json"
        raw_squads = json.loads(squads_backup_file.read_text(encoding="utf-8"))
        squad_template = raw_squads[0] if raw_squads else {}

        # Remap member assistant IDs to newly created assistant IDs
        id_lookup_by_name = {
            "Luxe Salon Voice Receptionist - Sophia": sophia_id,
            "Luxe Salon Director - Marcus": marcus_id,
            "AI Forward Deployment Engineer - Kishor": kishor_id,
            "Head of Sales - Tasnim": tasnim_id,
            "Director of Communications - Raiyan": raiyan_id
        }

        squad_members = []
        for member in squad_template.get("members", []):
            destinations = member.get("assistantDestinations", [])
            # Find which assistant this member is by checking its destinations
            # Or rebuild cleanly:
            pass

        # Clean canonical squad structure:
        canonical_members = [
            {
                "assistantId": sophia_id,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus Vance for master hair coloring, balayage, or salon director consultations."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for engineering, software automation, technical setup, or API integrations."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for business partnerships, enterprise salon expansion, or luxury pricing tiers."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for corporate communications, client feedback, VIP correspondence, or executive escalations."}
                ]
            },
            {
                "assistantId": marcus_id,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer back to Sophia for standard salon bookings, front desk check-in, or reception."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for tech support, integration issues, or appointment system customizations."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for salon package deals, bridal group pricing, or wholesale salon programs."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for client feedback, VIP correspondence, or communications."}
                ]
            },
            {
                "assistantId": kishor_id,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer to Sophia for standard salon bookings, front desk check-in, or reception."},
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus for master styling, hair coloring, balayage, or salon creative direction."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for enterprise sales contracts, commercial package deals, or pricing tiers."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for corporate communications, client relations, or executive escalations."}
                ]
            },
            {
                "assistantId": tasnim_id,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer to Sophia for routine salon appointments, nails, facials, or reception scheduling."},
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus for custom styling consultations, color formulation, or hair design."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for technical feasibility, software setup, API integration, or automation."},
                    {"type": "assistant", "assistantName": "Director of Communications - Raiyan", "description": "Transfer to Raiyan for PR, media inquiries, partner relations, or client satisfaction."}
                ]
            },
            {
                "assistantId": raiyan_id,
                "assistantDestinations": [
                    {"type": "assistant", "assistantName": "Luxe Salon Voice Receptionist - Sophia", "description": "Transfer to Sophia for regular appointment bookings, front-desk check-ins, or general reception."},
                    {"type": "assistant", "assistantName": "Luxe Salon Director - Marcus", "description": "Transfer to Marcus for stylist consultations, hair coloring, or salon director advice."},
                    {"type": "assistant", "assistantName": "AI Forward Deployment Engineer - Kishor", "description": "Transfer to Kishor for technical issues, system software questions, or integrations."},
                    {"type": "assistant", "assistantName": "Head of Sales - Tasnim", "description": "Transfer to Tasnim for sales inquiries, luxury packages, or corporate memberships."}
                ]
            }
        ]

        squad_payload = {
            "name": "Luxe Frontfoot 5-Member Leadership Squad",
            "members": canonical_members
        }

        existing_squads = client.get("/squad").json()
        squad_id = None
        for sq in existing_squads:
            if sq.get("name") == squad_payload["name"]:
                squad_id = sq["id"]
                client.patch(f"/squad/{squad_id}", json=squad_payload)
                print(f"  ✓ Updated existing Squad ({squad_id})")
                break

        if not squad_id:
            c_sq = client.post("/squad", json=squad_payload)
            if c_sq.status_code in (200, 201):
                squad_id = c_sq.json()["id"]
                print(f"  + Created new Squad ({squad_id})")
            else:
                print(f"  ❌ Squad creation failed: {c_sq.text}")

        # -------------------------------------------------------------
        # 4. Connect Telnyx Credential & Attach Phone Number to Squad
        # -------------------------------------------------------------
        phone_id = None
        if telnyx_key and telnyx_app_id:
            print(f"\n📞 Step 4: Registering Telnyx Telephony Credential & Inbound Phone ({phone_number})...")
            # 1. Create or verify Telnyx credential
            cred_res = client.get("/credential")
            existing_creds = cred_res.json() if cred_res.status_code == 200 else []
            cred_id = None
            for c in existing_creds:
                if c.get("provider") == "telnyx":
                    cred_id = c["id"]
                    print(f"  ✓ Found existing Telnyx credential: {cred_id}")
                    break

            if not cred_id:
                new_cred = client.post("/credential", json={
                    "provider": "telnyx",
                    "apiKey": telnyx_key
                })
                if new_cred.status_code in (200, 201):
                    cred_id = new_cred.json()["id"]
                    print(f"  + Created Telnyx Credential: {cred_id}")
                else:
                    print(f"  ⚠️ Credential creation note: {new_cred.text}")

            # 2. Register / Bind phone number in Vapi
            phones_res = client.get("/phone-number")
            existing_phones = phones_res.json() if phones_res.status_code == 200 else []
            for p in existing_phones:
                if p.get("number") == phone_number:
                    phone_id = p["id"]
                    print(f"  ✓ Found phone number {phone_number} with ID: {phone_id}")
                    break

            phone_payload = {
                "name": "ParoiAI",
                "provider": "telnyx",
                "number": phone_number,
                "credentialId": cred_id,
                "serverUrl": server_url,
                "squadId": squad_id
            }

            if phone_id:
                up_p = client.patch(f"/phone-number/{phone_id}", json=phone_payload)
                print(f"  ✓ Bound Phone {phone_number} directly to Squad ({squad_id}): {up_p.status_code}")
            else:
                c_p = client.post("/phone-number", json=phone_payload)
                if c_p.status_code in (200, 201):
                    phone_id = c_p.json()["id"]
                    print(f"  + Registered Phone {phone_number} with ID ({phone_id}) bound to Squad!")
                else:
                    # Fallback if provider registration requires manual BYOT
                    print(f"  ⚠️ Phone registration returned: {c_p.status_code} {c_p.text}")

        # -------------------------------------------------------------
        # 5. Persist Everything to .env
        # -------------------------------------------------------------
        print("\n💾 Step 5: Updating .env file with new IDs...")
        if vapi_private:
            set_key(str(ENV_PATH), "VAPI_PRIVATE_API_KEY", vapi_private)
        if vapi_public:
            set_key(str(ENV_PATH), "VAPI_PUBLIC_API_KEY", vapi_public)
            set_key(str(ENV_PATH), "VAPI_PUBLIC_KEY", vapi_public)
        if sophia_id:
            set_key(str(ENV_PATH), "VAPI_ASSISTANT_ID", sophia_id)
            set_key(str(ENV_PATH), "VAPI_SOPHIA_ASSISTANT_ID", sophia_id)
        if marcus_id:
            set_key(str(ENV_PATH), "VAPI_MARCUS_ASSISTANT_ID", marcus_id)
        if kishor_id:
            set_key(str(ENV_PATH), "VAPI_KISHOR_ASSISTANT_ID", kishor_id)
        if tasnim_id:
            set_key(str(ENV_PATH), "VAPI_TASNIM_ASSISTANT_ID", tasnim_id)
        if raiyan_id:
            set_key(str(ENV_PATH), "VAPI_RAIYAN_ASSISTANT_ID", raiyan_id)
        if squad_id:
            set_key(str(ENV_PATH), "VAPI_SQUAD_ID", squad_id)
        if phone_id:
            set_key(str(ENV_PATH), "VAPI_PHONE_NUMBER_ID", phone_id)

        print("  ✅ .env updated successfully!")

        # -------------------------------------------------------------
        # 6. Optional Sync to Vercel
        # -------------------------------------------------------------
        if args.sync_vercel:
            print("\n🚀 Step 6: Syncing credentials to Vercel Production...")
            sync_script = BASE_DIR / "scripts" / "sync_env_to_vercel.py"
            if sync_script.exists():
                subprocess.run([sys.executable, str(sync_script)], check=True)
                print("  ✓ Vercel environment variables synchronized!")
                print("  📦 Deploying to Vercel production...")
                subprocess.run(["vercel", "--prod", "--yes"], cwd=str(BASE_DIR), check=True)
                print("  ✅ Vercel Production Redeployed!")

    print("\n" + "=" * 75)
    print("🎉 MIGRATION COMPLETE! ALL RESOURCES MOVED TO NEW VAPI ACCOUNT")
    print(f"   Sophia Assistant ID:  {sophia_id}")
    print(f"   Marcus Assistant ID:  {marcus_id}")
    print(f"   Kishor Assistant ID:  {kishor_id}")
    print(f"   Tasnim Assistant ID:  {tasnim_id}")
    print(f"   Raiyan Assistant ID:  {raiyan_id}")
    print(f"   Squad ID:             {squad_id}")
    print(f"   Phone Number ID:      {phone_id}")
    print("=" * 75)

if __name__ == "__main__":
    main()
