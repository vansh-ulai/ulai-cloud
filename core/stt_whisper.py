import asyncio
import logging
from typing import Optional

import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel
import noisereduce as nr

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("stt_whisper_fast")

# ---------- CONFIG ----------
SAMPLE_RATE = 16000
CHUNK_SECONDS = 2.0
OVERLAP_SECONDS = 0.35
MAX_PENDING_TASKS = 3
MODEL_NAME = "medium.en"
# ----------------------------

def _compute_type_for_device(device: str) -> str:
    return "float16" if device.lower().startswith("cuda") else "int8"

class FasterWhisperSTT:
    def __init__(self, model_name: str = MODEL_NAME, device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.compute_type = _compute_type_for_device(self.device)
        LOG.info(f"🗣️ Initializing Faster-Whisper: model={model_name}, device={self.device}, compute_type={self.compute_type}")
        self.model = WhisperModel(model_name, device=self.device, compute_type=self.compute_type)

    def transcribe_array(self, audio: np.ndarray) -> str:
        try:
            # MODIFIED: Increased min silence duration slightly
            vad_parameters = dict(min_silence_duration_ms=700, threshold=0.6)

            segments, _ = self.model.transcribe(
                audio,
                beam_size=5,
                language="en",
                vad_filter=True,
                vad_parameters=vad_parameters,
            )
            text = " ".join(seg.text for seg in segments).strip()
            return text
        except Exception as e:
            LOG.exception("Transcription error: %s", e)
            return ""

async def start_stt_listener(
    out_queue: asyncio.Queue,
    speaking_event: asyncio.Event,
    device_name_hint: str = "cable",
):
    try:
        devices = sd.query_devices()
        device_index = next(
            i for i, d in enumerate(devices)
            if device_name_hint.lower() in (d.get("name") or "").lower()
        )
        device_name = devices[device_index]['name']
        LOG.info(f"✅ Using audio device: {device_name}")
    except (StopIteration, ValueError):
        LOG.warning(f"⚠️ Audio device hint '{device_name_hint}' not found. Falling back to default.")
        device_index = None

    stt = FasterWhisperSTT(model_name=MODEL_NAME)
    
    chunk_samples = int(CHUNK_SECONDS * SAMPLE_RATE)
    overlap_samples = int(OVERLAP_SECONDS * SAMPLE_RATE)
    step_samples = chunk_samples - overlap_samples

    audio_queue = asyncio.Queue(maxsize=80)
    loop = asyncio.get_event_loop()

    def audio_callback(indata, frames, time, status):
        if speaking_event.is_set():
            return
        if status:
            LOG.warning(f"SoundDevice status: {status}")
        try:
            loop.call_soon_threadsafe(audio_queue.put_nowait, indata.copy())
        except asyncio.QueueFull:
            LOG.warning("STT audio queue is full, dropping audio frames.")

    async def run_inference(chunk_array: np.ndarray):
        try:
            text = await loop.run_in_executor(None, stt.transcribe_array, chunk_array)
            if text:
                LOG.info(f"[STT] 🎧 {text}")
                await out_queue.put(text)
        except Exception as e:
            LOG.exception(f"Error in inference task: {e}")

    async def worker():
        audio_buffer = np.array([], dtype=np.float32)
        pending_tasks = set()
        LOG.info(f"🎙️ Whisper STT listening (chunk={CHUNK_SECONDS}s, overlap={OVERLAP_SECONDS}s)")
        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32",
            device=device_index, callback=audio_callback
        ):
            while True:
                new_data = await audio_queue.get()
                audio_buffer = np.concatenate((audio_buffer, new_data.flatten()))
                while len(audio_buffer) >= chunk_samples:
                    chunk = audio_buffer[:chunk_samples]
                    audio_buffer = audio_buffer[step_samples:]
                    chunk = nr.reduce_noise(y=chunk, sr=SAMPLE_RATE)
                    if len(pending_tasks) >= MAX_PENDING_TASKS:
                        _, pending_tasks = await asyncio.wait(
                            pending_tasks, return_when=asyncio.FIRST_COMPLETED
                        )
                    task = asyncio.create_task(run_inference(chunk))
                    pending_tasks.add(task)
                    task.add_done_callback(pending_tasks.discard)

    return asyncio.create_task(worker())