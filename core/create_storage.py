
import argparse
import asyncio
from playwright.async_api import async_playwright

async def create_state(out_path="storage_state.json"):
    async with async_playwright() as p:
        # Headful so you can interactively log in
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        print("Chromium opened. Please log into the target Google account in the browser window.")
        await page.goto("https://accounts.google.com/ServiceLogin")
        input("When you have completed login (and any 2FA), press Enter here to save storage state...")
        await context.storage_state(path=out_path)
        print(f"Saved storage state to {out_path}")
        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="storage_state.json", help="Output storage state JSON path")
    args = parser.parse_args()
    asyncio.run(create_state(args.out))
