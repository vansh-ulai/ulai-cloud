#!/usr/bin/env python3
"""
Test Deepgram API Key and Connection
"""
import os
import asyncio
import websockets
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY")

print("="*70)
print("DEEPGRAM API TEST".center(70))
print("="*70)

# Test 1: Check API key format
print("\n✓ Test 1: API Key Check")
if not API_KEY:
    print("  ❌ No API key found!")
    exit(1)

print(f"  ✅ Found API key: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"  Length: {len(API_KEY)} characters")

# Check if it looks valid (Deepgram keys are typically 40 chars)
if len(API_KEY) < 30:
    print("  ⚠️  Warning: API key seems too short")

# Test 2: Try connecting to Deepgram WebSocket
print("\n✓ Test 2: WebSocket Connection Test")
print("  Attempting to connect to Deepgram...")

async def test_connection():
    # Simplified URL - just the essentials
    url = (
        "wss://api.deepgram.com/v1/listen"
        "?encoding=linear16"
        "&sample_rate=16000"
        "&channels=1"
    )
    
    headers = {
        "Authorization": f"Token {API_KEY}"
    }
    
    try:
        print(f"  Connecting to: {url[:50]}...")
        print(f"  Using auth header: Token {API_KEY[:10]}...")
        
        async with websockets.connect(
            url,
            extra_headers=headers,
            ping_interval=20,
            ping_timeout=10
        ) as ws:
            print("  ✅ Connected successfully!")
            
            # Send dummy audio to get a response
            print("  📤 Sending test audio...")
            dummy_audio = b'\x00' * 3200  # 0.1 seconds of silence
            await ws.send(dummy_audio)
            
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                print(f"  ✅ Received response: {msg[:100]}")
            except asyncio.TimeoutError:
                print("  ✅ No response yet (this is NORMAL - Deepgram waits for speech)")
            
            print("\n  🎉 CONNECTION TEST PASSED!")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"  ❌ Connection rejected: {e}")
        print(f"  Status code: {e.status_code}")
        
        if e.status_code == 400:
            print("\n  🔍 HTTP 400 means BAD REQUEST. Possible causes:")
            print("     1. Invalid API key format")
            print("     2. API key doesn't have permission for live transcription")
            print("     3. Wrong URL parameters")
        elif e.status_code == 401:
            print("\n  🔍 HTTP 401 means UNAUTHORIZED. Your API key is invalid.")
        
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test_connection())

print("\n" + "="*70)

if result:
    print("SUCCESS! Your Deepgram API is working correctly.".center(70))
    print("="*70)
    print("\n✅ You can now run the STT test with confidence!")
else:
    print("FAILED! Connection test unsuccessful.".center(70))
    print("="*70)
    print("\n❌ ACTION REQUIRED:")
    print("   1. Verify your API key at: https://console.deepgram.com/")
    print("   2. Make sure it's a valid API key (not a project ID)")
    print("   3. Check that your account has live transcription enabled")
    print("   4. Copy the EXACT key from Deepgram console to your .env file")