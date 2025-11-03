import asyncio
import os
import random
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from core import notion_api_actions

load_dotenv()

NOTION_URL = "https://www.notion.so"
# Use the profile path you created with save_notion_profile.py
PROFILE_PATH = r"C:\Ulai\ulai_meet_ai\playwright_notion_profile"
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")

# If you want the API to also write (in addition to visible typing), set env var:
# NOTION_API_SYNC=true
NOTION_API_SYNC = os.getenv("NOTION_API_SYNC", "false").lower() in ("1", "true", "yes")


async def human_type_in_editor(page, text, delay_min=40, delay_max=110):
    """Type into the first contenteditable on the page like a human and press Enter."""
    editor = await page.query_selector("div[contenteditable='true']")
    if not editor:
        print("⚠️ Editor not found — typing aborted.")
        return False

    # click to ensure focus
    try:
        box = await editor.bounding_box()
        if box:
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            await page.mouse.move(cx, cy, steps=10)
            await page.mouse.click(cx, cy)
    except Exception:
        # fallback: just click the element
        try:
            await editor.click()
        except Exception:
            pass

    # type char-by-char
    for ch in text:
        await page.keyboard.type(ch, delay=random.randint(delay_min, delay_max))
    # press Enter to finish the paragraph
    await page.keyboard.press("Enter")
    await asyncio.sleep(0.2)
    return True


async def move_mouse_to_editor_center(page):
    """Move mouse to the center of the editor (if available) or center of viewport."""
    try:
        editor = await page.query_selector("div[contenteditable='true']")
        if editor:
            box = await editor.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2
                await page.mouse.move(x, y, steps=25)
                await asyncio.sleep(0.08)
                return
    except Exception:
        pass

    # fallback: center of the viewport
    vp = await page.evaluate("() => ({ w: window.innerWidth, h: window.innerHeight })")
    await page.mouse.move(vp["w"] / 2, vp["h"] / 2, steps=25)
    await asyncio.sleep(0.08)


async def launch_notion_profile(p):
    """Launch persistent Playwright context using your dedicated profile."""
    os.makedirs(PROFILE_PATH, exist_ok=True)
    print("🌐 Launching Notion with your saved Playwright profile...")
    context = await p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_PATH,
        headless=False,
        args=["--start-maximized"],
    )
    # prefer existing open page
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(NOTION_URL)
    try:
        await page.wait_for_selector("div[aria-label='Notion sidebar']", timeout=10000)
        print("✅ Notion workspace detected (logged in).")
    except Exception:
        print("⚠️ Could not detect workspace automatically — ensure the profile is logged in.")
    return context, page


async def main():
    print("--- 🧠 Notion AI Automation (visual demo) ---")
    print("Commands:")
    print("  create page [title]")
    print("  type [text]")
    print("  exit")
    if NOTION_API_SYNC:
        print("⚠️ NOTE: NOTION_API_SYNC=true -> API will also write blocks (may duplicate if editor typing also happens).")

    async with async_playwright() as p:
        context, page = await launch_notion_profile(p)
        last_page_id = None

        while True:
            try:
                command = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                command = "exit"

            if command == "exit":
                print("👋 Exiting...")
                await context.close()
                break

            if command.startswith("create page"):
                title = command.split("create page", 1)[1].strip() or "Untitled"
                page_data = await notion_api_actions.create_new_page(title, PARENT_PAGE_ID)
                if page_data:
                    last_page_id = page_data["id"]
                    notion_url = f"https://www.notion.so/{page_data['id'].replace('-', '')}"
                    print(f"✅ Created page '{title}' via API.")
                    await page.goto(notion_url)
                    # give it a bit to render and then focus
                    await page.wait_for_timeout(1000)
                    await move_mouse_to_editor_center(page)
                    await page.wait_for_timeout(300)

            elif command.startswith("type"):
                if not last_page_id:
                    print("⚠️ Please create a page first using 'create page [title]'.")
                    continue

                text = command.split("type", 1)[1].strip()
                # visually focus editor
                await move_mouse_to_editor_center(page)
                print("⌨️ Typing visibly in editor...")
                ok = await human_type_in_editor(page, text)
                if ok:
                    print(f"✅ Typed visibly: '{text}'")
                else:
                    print("❌ Visible typing failed.")

                # Optionally also sync via Notion API (disabled by default to avoid duplicates)
                if NOTION_API_SYNC:
                    try:
                        await notion_api_actions.add_paragraph(last_page_id, text)
                        print("🔁 Also wrote via Notion API (NOTION_API_SYNC enabled).")
                    except Exception as e:
                        print(f"⚠️ API sync failed: {e}")

            else:
                print("Unknown command. Try:")
                print("  create page [title]")
                print("  type [text]")
                print("  exit")


if __name__ == "__main__":
    asyncio.run(main())
