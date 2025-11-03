import asyncio
import logging
from core.audio_manager import speak_text_virtual


async def handle_tts_input(page, safe_click, assistant_speaking):
    """
    Console-driven TTS loop (manual).
    Lets you type text that will be spoken through VB-Cable into Google Meet.
    While speaking, 'assistant_speaking' flag is set so STT ignores self speech.
    """

    logging.info("🗣️ Manual TTS mode active. Type a message and press Enter to speak. Type 'exit' to quit.")

    while True:
        try:
            # Read from stdin in a non-blocking thread
            user_input = await asyncio.to_thread(input, "Say> ")
        except (EOFError, KeyboardInterrupt):
            logging.info("🛑 Manual TTS stopped by user.")
            break

        user_input = user_input.strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            logging.info("👋 Exiting manual TTS loop.")
            break

        assistant_speaking.set()
        try:
            # Try turning mic on — helpful if Meet auto-mutes
            try:
                await safe_click(
                    page,
                    [
                        'button[aria-label*="Turn on microphone"]',
                        'div[aria-label*="Turn on microphone"]',
                        'button[aria-label*="Unmute"]'
                    ],
                    retries=2,
                    delay=0.3
                )
            except Exception:
                logging.debug("🎙️ Could not toggle mic on — possibly already unmuted.")

            logging.info(f"🔊 Speaking (manual): {user_input}")
            await asyncio.to_thread(speak_text_virtual, user_input)

        except Exception as e:
            logging.exception("❌ Manual TTS error: %s", e)
        finally:
            # Grace delay to ensure speech finishes before unsetting flag
            await asyncio.sleep(0.5)
            assistant_speaking.clear()
