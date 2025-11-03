# core/meet_creator.py
from __future__ import print_function
import datetime
import os.path
import uuid
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "token.json"  # token you generated with calendar_oauth.py


def create_google_meet_link(email=None, password=None):
    """Creates a new Google Meet link using Calendar API (OAuth-based) and makes it open to everyone."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            TOKEN_PATH, ['https://www.googleapis.com/auth/calendar']
        )
    else:
        print("❌ token.json not found. Run calendar_oauth.py first.")
        return None

    service = build("calendar", "v3", credentials=creds)

    # Define event details
    start_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
    end_time = start_time + datetime.timedelta(hours=1)

    event = {
        "summary": "Ulai AI Client Meeting",
        "description": "Auto-generated meeting for client session.",
        "start": {
            "dateTime": start_time.isoformat() + "Z",
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat() + "Z",
            "timeZone": "UTC",
        },
        "conferenceData": {
            "createRequest": {
                "requestId": f"ulai-{uuid.uuid4()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            },
            # --- THIS IS THE CRITICAL ADDITION ---
            # Set the access type to "OPEN" to allow anyone with the link
            # to join directly without needing approval (no "Ask to join" lobby).
            "settings": {
                "accessType": "OPEN"
            }
            # --- END OF ADDITION ---
        },
        "visibility": "public",
        "guestsCanInviteOthers": True,
        "guestsCanModify": True,
        "guestsCanSeeOtherGuests": True,
        "anyoneCanAddSelf": True,
        "attendees": [
            {
                "email": "everyone@ulaitest.dev",  # fake open-domain guest
                "responseStatus": "accepted"
            }
        ]
    }

    # Create the Meet event
    try:
        event = service.events().insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1
        ).execute()

        meet_link = event.get("hangoutLink")
        print(f"✅ New Meet link created (Lobby Disabled): {meet_link}")
        
        # You can also print the access type to confirm
        access_type = event.get("conferenceData", {}).get("settings", {}).get("accessType")
        print(f"✅ Meet Access Type: {access_type}")

        return meet_link

    except Exception as e:
        print(f"❌ Failed to create Meet link: {e}")
        # Note: If this fails, your Google Workspace domain might be
        # blocking "OPEN" meetings. If so, use Solution 2.
        return None
