#!/usr/bin/env python3
"""
STT worker: connects to Deepgram, streams mic audio and prints *plain transcripts*
to STDOUT (one transcript per line). Logging goes to STDERR so the parent process
can read transcripts cleanly.

Requirements:
    pip install websockets sounddevice python-dotenv
"""

import os
import asyncio
import json
import logging
import sys
from dotenv import load_dotenv

# Optional: microphone capture
try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import websockets
except Exception:
    websockets = None

# Load .env if present
load_dotenv()

# Send logs to STDERR so main process can treat STDOUT as the transcript channel
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(sys.stderr)])

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    logging.error("DEEPGRAM_API_KEY environment variable not set. Exiting.")
    raise SystemExit(1)

DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "").strip()
STT_TEST_MODE = os.getenv("STT_TEST_MODE") in ("1", "true", "True")

# Print a small env snapshot relevant to networking/SSL to STDERR for debugging
for k in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "NODE_EXTRA_CA_CERTS", "REQUESTS_CA_BUNDLE"]:
    logging.info("ENV %s=%s", k, os.getenv(k))


def extract_transcripts_from_msg(msg_json):
    """
    Given a Deepgram JSON message (dict), return a list of transcript strings (possibly empty).
    We prefer finalized alternatives and filter out empty strings.
    """
    transcripts = []

    # Many Deepgram messages use "type": "Results" and provide `channel.alternatives`
    try:
        msg_type = msg_json.get("type", "").lower()
        if msg_type in ("results", "transcript", "final"):
            # There may be top-level 'channel' or 'channels' structure
            if "channel" in msg_json and isinstance(msg_json["channel"], dict):
                alts = msg_json["channel"].get("alternatives", [])
                if alts and isinstance(alts, list):
                    t = alts[0].get("transcript", "").strip()
                    if t:
                        transcripts.append(t)
            # handle other shapes (channels array)
            if "channels" in msg_json and isinstance(msg_json["channels"], list):
                for ch in msg_json["channels"]:
                    alts = ch.get("alternatives", [])
                    if alts:
                        t = alts[0].get("transcript", "").strip()
                        if t:
                            transcripts.append(t)
            # some messages include 'alternatives' at top level
            if "alternatives" in msg_json and isinstance(msg_json["alternatives"], list):
                alts = msg_json["alternatives"]
                if alts:
                    t = alts[0].get("transcript", "").strip()
                    if t:
                        transcripts.append(t)
    except Exception as e:
        logging.debug("Error extracting transcripts: %s", e)

    # Deduplicate and return
    out = []
    for t in transcripts:
        if t and t not in out:
            out.append(t)
    return out


async def run_stt():
    url = "wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000"
    if DEEPGRAM_MODEL:
        url += f"&model={DEEPGRAM_MODEL}"

    if websockets is None:
        logging.error("websockets package not available. Install via `pip install websockets`.")
        return

    async def sender(ws, audio_queue: asyncio.Queue):
        """Sends audio bytes to Deepgram. In test mode or without sounddevice, send a few dummy frames."""
        if STT_TEST_MODE or sd is None:
            logging.info("STT worker running in TEST_MODE or sounddevice unavailable — sending dummy frames")
            for _ in range(8):
                await ws.send(b"\x00\x00\x00\x00")
                await asyncio.sleep(0.2)
            return

        loop = asyncio.get_event_loop()

        def audio_callback(indata, frames, time, status):
            if status:
                logging.warning("SoundDevice status: %s", status)
            try:
                audio_bytes = indata.tobytes()
                loop.call_soon_threadsafe(audio_queue.put_nowait, audio_bytes)
            except Exception as e:
                logging.exception("audio_callback error: %s", e)

        # Use context manager so InputStream is closed cleanly on exit
        try:
            with sd.InputStream(samplerate=16000, channels=1, dtype="int16", callback=audio_callback):
                logging.info("Microphone stream started (hit Ctrl-C to stop).")
                while True:
                    chunk = await audio_queue.get()
                    if chunk is None:
                        break
                    await ws.send(chunk)
        except Exception as e:
            logging.exception("Microphone stream error: %s", e)
            raise

    async def receiver(ws):
        """Receives messages from Deepgram and prints non-empty transcripts to STDOUT."""
        async for message in ws:
            # message may be text (JSON) or bytes; Deepgram sends JSON text
            try:
                # decode if bytes
                if isinstance(message, (bytes, bytearray)):
                    try:
                        message = message.decode("utf-8")
                    except Exception:
                        # Not JSON text; skip
                        continue
                msg_json = json.loads(message)
            except Exception:
                # Not JSON or parse error: log and skip
                logging.debug("Non-JSON message from Deepgram: %s", repr(message)[:200])
                continue

            # Debug-log the raw JSON to STDERR (already separated), but avoid huge spam
            logging.debug("Deepgram JSON: %s", json.dumps(msg_json)[:1000])

            # Extract transcripts
            transcripts = extract_transcripts_from_msg(msg_json)
            for t in transcripts:
                # Print to STDOUT so parent subprocess captures it as transcript lines.
                # Use flush=True to ensure immediate delivery.
                print(t, flush=True)

    # Main loop: connect, spawn sender/receiver, reconnect on errors
    while True:
        try:
            headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
            logging.info("Attempting to connect to Deepgram: %s (key ending %s)", url, DEEPGRAM_API_KEY[-4:])
            async with websockets.connect(url, extra_headers=headers, max_size=None) as ws:
                logging.info("✅ Connected to Deepgram WebSocket")
                audio_queue = asyncio.Queue()
                send_task = asyncio.create_task(sender(ws, audio_queue))
                recv_task = asyncio.create_task(receiver(ws))
                done, pending = await asyncio.wait([send_task, recv_task], return_when=asyncio.FIRST_EXCEPTION)
                for t in pending:
                    t.cancel()
                # If we exit the wait loop, cancel remaining tasks cleanly
                for t in pending:
                    try:
                        await t
                    except Exception:
                        pass
        except Exception as e:
            logging.error("STT Worker Error: %s. Reconnecting in 3s...", e)
            await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        asyncio.run(run_stt())
    except KeyboardInterrupt:
        logging.info("STT worker interrupted by user. Exiting.")
    except Exception as e:
        logging.exception("Unhandled in STT worker: %s", e)
        raise
