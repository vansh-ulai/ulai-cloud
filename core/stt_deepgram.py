import os
import json
import asyncio
import sounddevice as sd
import websockets
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("stt_deepgram")

# Load API key from environment
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    raise EnvironmentError("API Key not found. Please add DEEPGRAM_API_KEY to your .env file.")

async def start_stt_listener(
    out_queue: asyncio.Queue,
    speaking_event: asyncio.Event,
    device_name_hint=None,

):
    """
    Connects to Deepgram and pushes transcripts to a queue within the same process.
    """
    LOG.info("🎤 Initializing Deepgram STT listener...")
    
    device_index = None
    
    LOG.info("🔍 Querying all available audio devices...")
    all_devices = []
    try:
        all_devices = list(sd.query_devices())
        for i, d in enumerate(all_devices):
            device_name = d.get("name") or ""
            max_input = d.get('max_input_channels', 0)
            if max_input > 0:
                LOG.info(f"   [Input] Device {i}: {device_name} (input channels: {max_input})")
            else:
                LOG.info(f"   [Output] Device {i}: {device_name}")
    except Exception as e:
        LOG.error(f"❌ Failed to query audio devices: {e}.")
        raise
    
    # --- THIS IS THE FIX ---
    # We now have a prioritized list of hints.
    # We will try the specific names first, then fall back to generic names.
    LOG.info(f"🔍 Looking for best audio device (and hint: '{device_name_hint}')...")
    
    device_hints = [
       "bot-input",
        "bot_input",
        "bot-input.monitor",
        "bot-output",
        "bot-output.monitor",

        # 2. Legacy names from previous start script
        "meet_output.monitor",
        "meet_output",
        "meet-output",
        "bot_mic",
        "bot-mic",
        "bot_mic.monitor",
        "bot_mic",

        # 3. User-provided hint
        device_name_hint,

        # 4. Generic PulseAudio names (crucial fallback)
        "pulse",
        "default",

        # 5. Other common loopback names
        "stereo mix",
        "wave out",
        "what u hear",
        "loopback",
        "mix"
    ]
    
    # Try to find a matching device
    for hint in device_hints:
        if not hint:
            continue
        for i, d in enumerate(all_devices):
            device_name = (d.get("name") or "").lower()
            # Use '==' for 'pulse' and 'default' to avoid matching 'pulseaudio' etc.
            # Use 'in' for other hints.
            is_match = False
            if hint in ["pulse", "default"]:
                if hint == device_name:
                    is_match = True
            elif hint.lower() in device_name:
                is_match = True

            if is_match and d.get('max_input_channels', 0) > 0:
                device_index = i
                LOG.info(f"✅ Selected audio device '{d['name']}' at index {i} (matched hint: '{hint}')")
                break
        if device_index is not None:
            break
    # --- END FIX ---
    
    if device_index is None:
        LOG.error(f"❌ CRITICAL: No usable input audio device found after checking all hints.")
        LOG.error("   STT cannot start. This will cause the bot to fail.")
        raise RuntimeError("Failed to find a valid input audio device for STT.")

    audio_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    
    chunks_sent = [0]
    last_transcript_time = [asyncio.get_event_loop().time()]

    def audio_callback(indata, frames, time, status):
        if speaking_event.is_set():
            return
        if status:
            LOG.warning(f"⚠️ SoundDevice status: {status}")
        try:
            loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))
            chunks_sent[0] += 1
            if chunks_sent[0] % 100 == 0:
                LOG.info(f"📊 Audio chunks sent to Deepgram: {chunks_sent[0]}")
        except Exception as e:
            LOG.error(f"❌ Audio callback error: {e}")

    async def stream_worker():
        url = "wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000&channels=1&model=nova-2&punctuate=true&smart_format=true"
        
        try:
            mic_stream = sd.InputStream(
                samplerate=16000, 
                channels=1, 
                dtype="int16",
                device=device_index, 
                callback=audio_callback,
                blocksize=8192
            )
            mic_stream.start()
            LOG.info(f"🎙️ Microphone stream started successfully on device {device_index} ('{sd.query_devices(device_index)['name']}')")
        except Exception as e:
            LOG.error(f"❌ Failed to start microphone on device {device_index}: {e}")
            raise

        connection_attempts = 0
        
        while True:
            connection_attempts += 1
            try:
                LOG.info(f"🔌 Connecting to Deepgram (attempt {connection_attempts})...")
                
                async with websockets.connect(
                    url, 
                    extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
                    ping_interval=20,
                    ping_timeout=10
                ) as ws:
                    LOG.info("✅ Connected to Deepgram WebSocket!")
                    connection_attempts = 0
                    
                    async def sender(ws):
                        sent_count = 0
                        try:
                            while True:
                                audio_chunk = await audio_queue.get()
                                await ws.send(audio_chunk)
                                sent_count += 1
                                if sent_count % 50 == 0:
                                    LOG.info(f"📤 Sent {sent_count} audio chunks to Deepgram")
                        except Exception as e:
                            LOG.error(f"❌ Sender error: {e}")
                            raise
                    
                    async def receiver(ws):
                        received_count = 0
                        try:
                            async for msg in ws:
                                received_count += 1
                                data = json.loads(msg)
                                
                                if received_count % 10 == 0:
                                    LOG.info(f"📥 Received {received_count} messages from Deepgram")
                                
                                transcript = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                                is_final = data.get("is_final", False)
                                
                                if transcript:
                                    LOG.info(f"🎧 [STT] Transcript (final={is_final}): '{transcript}'")
                                    
                                    if is_final:
                                        if speaking_event.is_set():
                                            LOG.info(f"⏭️ [STT] Skipped (assistant speaking): '{transcript}'")
                                        else:
                                            LOG.info(f"✅ [STT] Queuing transcript: '{transcript}'")
                                            await out_queue.put(transcript)
                                            last_transcript_time[0] = loop.time()
                                
                                if "speech_final" in data:
                                    LOG.info("🗣️ Speech final event received")
                                
                        except Exception as e:
                            LOG.error(f"❌ Receiver error: {e}")
                            raise

                    sender_task = asyncio.create_task(sender(ws))
                    receiver_task = asyncio.create_task(receiver(ws))
                    
                    done, pending = await asyncio.wait(
                        [sender_task, receiver_task], 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
                    
                    for task in done:
                        if task.exception():
                            LOG.error(f"Task failed with: {task.exception()}")

            except websockets.exceptions.WebSocketException as e:
                LOG.error(f"❌ WebSocket error: {e}. Reconnecting in 3 seconds...")
                await asyncio.sleep(3)
            except Exception as e:
                LOG.error(f"❌ Deepgram connection error: {e}. Reconnecting in 3 seconds...")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(3)
    
    return asyncio.create_task(stream_worker())