# core/assistant_manager.py
import asyncio
import logging
import time
from typing import List

from core.local_llm import get_local_llm_response_async
from core.audio_manager import speak_text_virtual

QUESTION_WORDS = ("what", "why", "how", "when", "who", "which", "where", "can", "could", "would", "please", "explain", "tell me")
MIN_SECONDS_BETWEEN_ANSWERS = 2.0  # throttle answers

def looks_like_question(text: str) -> bool:
    t = text.lower().strip()
    if "?" in t:
        return True
    # short heuristic: starts with question words OR contains polite request
    for w in QUESTION_WORDS:
        if t.startswith(w + " ") or (" " + w + " ") in t:
            return True
    # also check for "can you" etc
    if any(phrase in t for phrase in ["can you", "could you", "please explain", "please describe", "please show"]):
        return True
    return False

async def assistant_worker(
    caption_queue: asyncio.Queue,
    assistant_speaking: asyncio.Event,
    page,
    safe_click,
    *,
    max_tokens: int = 180,
    verbose: bool = False
):
    """
    Worker that consumes captions and replies to questions.
    - caption_queue: queue of caption strings
    - assistant_speaking: Event used to block captions when assistant speaks
    - page & safe_click: used to ensure mic is enabled (if desired)
    """
    last_answer_time = 0.0
    recent_context: List[str] = []

    while True:
        text = await caption_queue.get()
        try:
            # maintain a short rolling context
            recent_context.append(text)
            if len(recent_context) > 12:
                recent_context.pop(0)

            # skip very short noise lines
            if len(text) < 3:
                continue

            # Decide whether to respond
            if not looks_like_question(text):
                # Not a question; we skip (but keep in context)
                if verbose:
                    logging.debug("Not a question: %s", text)
                continue

            now = time.time()
            if now - last_answer_time < MIN_SECONDS_BETWEEN_ANSWERS:
                logging.debug("Throttling: recently answered, skipping.")
                continue

            # Build prompt using short context + question (concise, presentation-aware)
            context = "\n".join(recent_context[-6:])
            prompt = (
                f"You are Hornet AI, a concise voice assistant for live presentations. "
                f"Use the context when relevant and give a direct helpful answer.\n\n"
                f"Context:\n{context}\n\nQuestion:\n{text}\n\nAnswer:"
            )

            logging.info("Querying local LLM for question: %s", text)
            assistant_speaking.set()  # prevent caption ingestion of assistant speech

            # Optionally ensure mic is ON inside the meeting UI before playback (best-effort)
            try:
                # unmute mic in meet so the TTS injected via VB-Cable gets heard
                await safe_click(page, ['button[aria-label*="Turn on microphone"]', 'div[aria-label*="Turn on microphone"]'], retries=2, delay=0.4)
            except Exception:
                logging.debug("Could not click to ensure mic on; continuing and playing audio anyway.")

            # Query LLM (async)
            answer = await get_local_llm_response_async(prompt, max_tokens=max_tokens)
            if not answer:
                answer = "Sorry, I couldn't generate an answer."

            logging.info("Assistant answer: %s", answer.replace("\n", " "))

            # Speak via VB-Cable (blocking call) but run in thread so we don't block event loop
            await asyncio.to_thread(speak_text_virtual, answer)

            last_answer_time = time.time()
            # leave assistant_speaking set for a tiny grace period to avoid fed-back captions
            await asyncio.sleep(0.5)
            assistant_speaking.clear()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.exception("Error in assistant worker: %s", e)
            assistant_speaking.clear()
        finally:
            caption_queue.task_done()
