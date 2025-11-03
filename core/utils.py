import asyncio
import logging


async def safe_click(page, selectors, retries=6, delay=1.5):
    """Safely click one of multiple selectors with retries."""
    for _ in range(retries):
        for s in selectors:
            try:
                el = await page.query_selector(s)
                if el:
                    await el.click(timeout=2000)
                    logging.info("Clicked selector: %s", s)
                    return True
            except Exception:
                continue
        await asyncio.sleep(delay)
    return False
