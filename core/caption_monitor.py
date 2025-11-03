# core/caption_monitor.py
import asyncio
import logging

async def capture_captions(page, js_script: str, seen: set, out_queue: asyncio.Queue, assistant_speaking: asyncio.Event):
    """
    Continuously fetch captions from the Meet DOM, deduplicate, and push NEW captions
    into `out_queue` for the assistant to process.

    - page: Playwright page
    - js_script: JS snippet to extract captions (returns     list)
    - seen: set used to dedupe captions across calls
    - out_queue: asyncio.Queue where captions are placed
    - assistant_speaking: asyncio.Event; when set, captions produced while assistant speaks are ignored
    """
    try:
        while True:
            try:
                captions = await page.evaluate(js_script)
                if captions:
                    for text in captions:
                        text = text.strip()
                        if not text:
                            continue
                        if text in seen:
                            continue
                        # don't push assistant-sourced captions while assistant is speaking
                        if assistant_speaking.is_set():
                            logging.debug("Ignoring caption while assistant is speaking: %s", text)
                            seen.add(text)
                            continue
                        seen.add(text)
                        logging.info("CAPTION (new): %s", text.replace("\n", " "))
                        # push into queue for assistant to consume
                        try:
                            out_queue.put_nowait(text)
                        except asyncio.QueueFull:
                            logging.warning("Caption queue full. Dropping caption: %s", text)
                await asyncio.sleep(0.7)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logging.exception("Error in caption capture loop: %s", e)
                await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        logging.info("Caption monitor cancelled; exiting.")
