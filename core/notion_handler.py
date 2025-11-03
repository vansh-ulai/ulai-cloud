    import os
    import asyncio
    import random
    import logging
    from dotenv import load_dotenv
    from playwright.async_api import Playwright, Page
    from notion_client import AsyncClient

    # === load env ===
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(DOTENV_PATH):
        load_dotenv(dotenv_path=DOTENV_PATH)

    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")
    if not NOTION_TOKEN or not PARENT_PAGE_ID:
        raise ValueError("NOTION_TOKEN and/or PARENT_PAGE_ID are not set in your .env file.")

    PROFILE_PATH = r"C:\Ulai\ulai_meet_ai\playwright_notion_profile"
    NOTION_URL = "https://www.notion.so"

    notion_api = AsyncClient(auth=NOTION_TOKEN)

    # === optimized timing constants ===
    PAUSE_SHORT = 0.4
    PAUSE_MED = 0.8
    PAUSE_LONG = 1.2


    # === browser/profile launcher ===
    async def launch_notion_with_profile(p: Playwright):
        """Launch persistent Playwright context using the dedicated saved profile."""
        os.makedirs(PROFILE_PATH, exist_ok=True)
        logging.info(f"🌐 Launching Notion with saved profile from: {PROFILE_PATH}")

        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            args=["--start-maximized"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.bring_to_front()
        return context, page


    # === Notion API helpers ===
    async def create_page_api(title: str):
        try:
            response = await notion_api.pages.create(
                parent={"page_id": PARENT_PAGE_ID},
                properties={"title": [{"text": {"content": title}}]},
            )
            logging.info(f"✅ API: Created page '{title}'.")
            return response
        except Exception as e:
            logging.error(f"❌ API: Error creating page: {e}")
            return None


    async def create_empty_table_api(page_id: str):
        """Create an empty table with Department and Lead headers using Notion API"""
        try:
            response = await notion_api.blocks.children.append(
                page_id,
                children=[
                    {
                        "object": "block",
                        "type": "table",
                        "table": {
                            "table_width": 2,
                            "has_column_header": True,
                            "has_row_header": False,
                            "children": [
                                {
                                    "type": "table_row",
                                    "table_row": {
                                        "cells": [
                                            [{"type": "text", "text": {"content": "Department"}}],
                                            [{"type": "text", "text": {"content": "Lead"}}]
                                        ]
                                    }
                                },
                                {
                                    "type": "table_row",
                                    "table_row": {
                                        "cells": [
                                            [{"type": "text", "text": {"content": ""}}],
                                            [{"type": "text", "text": {"content": ""}}]
                                        ]
                                    }
                                },
                                {
                                    "type": "table_row",
                                    "table_row": {
                                        "cells": [
                                            [{"type": "text", "text": {"content": ""}}],
                                            [{"type": "text", "text": {"content": ""}}]
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ],
            )
            logging.info(f"📊 API: Created empty table in {page_id}")
            return response
        except Exception as e:
            logging.warning(f"⚠️ API empty table creation failed: {e}")
            return None


    async def create_project_timeline_database_api(parent_page_id: str, title: str):
        """Create a unified project timeline/task database with Name, Status, Lead, and Due Date"""
        try:
            response = await notion_api.databases.create(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": title}}],
                properties={
                    "Task Name": {
                        "title": {}
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "Scheduled", "color": "gray"},
                                {"name": "In Progress", "color": "blue"},
                                {"name": "Completed", "color": "green"}
                            ]
                        }
                    },
                    "Lead": {
                        "select": {
                            "options": [
                                {"name": "Sarah Chen", "color": "purple"},
                                {"name": "David Kumar", "color": "blue"},
                                {"name": "Emma Wilson", "color": "pink"},
                                {"name": "James Rodriguez", "color": "orange"},
                                {"name": "Lisa Wang", "color": "green"}
                            ]
                        }
                    },
                    "Due Date": {
                        "date": {}
                    }
                }
            )
            logging.info(f"✅ API: Created project timeline database '{title}' with ID: {response['id']}")
            return response
        except Exception as e:
            logging.error(f"❌ API: Error creating project timeline database: {e}")
            return None


    async def add_timeline_tasks_via_api(database_id: str, tasks: list):
        """Add timeline tasks with status colors and assigned leads via Notion API - row by row"""
        try:
            logging.info("📅 Adding project timeline tasks via API...")
            
            for task_name, status, lead_name, due_date in tasks:
                logging.info(f"📝 Adding: {task_name} - Status: {status} - Lead: {lead_name} - Due: {due_date}")
                
                await notion_api.pages.create(
                    parent={"database_id": database_id},
                    properties={
                        "Task Name": {
                            "title": [{"text": {"content": task_name}}]
                        },
                        "Status": {
                            "select": {"name": status}
                        },
                        "Lead": {
                            "select": {"name": lead_name}
                        },
                        "Due Date": {
                            "date": {"start": due_date}
                        }
                    }
                )
                logging.info(f"✅ Added: {task_name} - Assigned to {lead_name}")
                await asyncio.sleep(0.3)
            
            logging.info("✅ All timeline tasks added successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error adding timeline tasks: {e}")
            return False


    async def type_with_human_delay(page: Page, text: str, base_delay: int = 40):
        """Type text with faster, natural delays"""
        for ch in text:
            await page.keyboard.type(ch, delay=random.randint(base_delay - 15, base_delay + 20))
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.05, 0.1))


    async def fill_table_manually(page: Page, data: list):
        """Fill the table row by row with faster typing using Tab navigation"""
        try:
            logging.info("⌨️ Starting manual table fill...")
            await asyncio.sleep(0.8)
            
            # Click on the first data cell
            await page.evaluate(
                """
                () => {
                    const rows = document.querySelectorAll('table tr');
                    if (rows && rows.length > 1) {
                        const firstDataRow = rows[1];
                        const firstCell = firstDataRow.querySelector('td div[contenteditable="true"]');
                        if (firstCell) {
                            firstCell.click();
                            firstCell.focus();
                            firstCell.textContent = '';
                        }
                    }
                }
                """
            )
            await asyncio.sleep(0.5)
            
            # Fill each row using Tab to navigate
            for row_idx, row_data in enumerate(data):
                for col_idx, cell_value in enumerate(row_data):
                    await type_with_human_delay(page, cell_value, 35)
                    await asyncio.sleep(0.2)
                    
                    # Use Tab to move to next cell
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(0.3)
            
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.3)
            
            logging.info("✅ Table filled successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error filling table manually: {e}")
            return False


    # === DOM-based focus ===
    async def focus_editor(page: Page):
        try:
            logging.debug("🎯 Focusing Notion editor via DOM...")
            await page.bring_to_front()
            await asyncio.sleep(0.15)

            focused = await page.evaluate(
                """
                () => {
                    const nodes = Array.from(document.querySelectorAll('div[role="textbox"], [contenteditable="true"]'));
                    if (!nodes || nodes.length === 0) return false;
                    const editor = nodes.length > 1 ? nodes[nodes.length - 1] : nodes[0];
                    try {
                        editor.scrollIntoView({ behavior: 'auto', block: 'center' });
                        editor.focus();
                        const range = document.createRange();
                        range.selectNodeContents(editor);
                        range.collapse(false);
                        const sel = window.getSelection();
                        sel.removeAllRanges();
                        sel.addRange(range);
                        return true;
                    } catch (err) {
                        return false;
                    }
                }
                """
            )

            if focused:
                await asyncio.sleep(0.1)
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.05)
                logging.debug("✅ Editor focused via DOM.")
                return True

            logging.warning("⚠️ DOM focus failed — falling back to center click.")
            vp = await page.evaluate("() => ({ w: window.innerWidth, h: window.innerHeight })")
            await page.mouse.click(vp["w"] / 2, vp["h"] / 2)
            await asyncio.sleep(0.1)
            await page.keyboard.press("Enter")
            return True

        except Exception as e:
            logging.error(f"❌ focus_editor error: {e}")
            return False


    # === navigation helpers ===
    async def go_to_page_ui(page: Page, page_id: str):
        notion_url = f"https://www.notion.so/{page_id.replace('-', '')}"
        logging.info(f"🌐 UI: Navigating to {notion_url}")
        await page.goto(notion_url)
        for attempt in range(3):
            try:
                await page.wait_for_selector(
                    "div[role='textbox'], [contenteditable='true'], [data-block-id]",
                    timeout=8000,
                )
                logging.debug("✅ UI: Notion page loaded successfully.")
                return
            except Exception:
                logging.warning(f"⚠️ go_to_page_ui attempt {attempt + 1} failed — reloading...")
                await page.reload()
                await asyncio.sleep(1)
        await page.screenshot(path="notion_debug.png")
        logging.error("❌ go_to_page_ui: page still not loaded. Screenshot saved → notion_debug.png")


    async def go_to_demo_home_ui(page: Page):
        await go_to_page_ui(page, PARENT_PAGE_ID)


    async def show_sidebar(page: Page):
        try:
            logging.debug("🔎 Showing sidebar (if collapsed).")
            await page.evaluate(
                """
                () => {
                    const btn = document.querySelector('[aria-label*="Toggle sidebar"], [aria-label*="Side"]');
                    if (btn) btn.click();
                }
                """
            )
            await asyncio.sleep(PAUSE_SHORT)
        except Exception as e:
            logging.debug(f"show_sidebar warning: {e}")


    # === main demo sequence ===
    async def run_demo_sequence(notion_page: Page, speak_func):
        logging.info("🤖 Starting optimized Notion demo sequence...")
        try:
            # === 1. INTRODUCTION ===
            await speak_func("Hi, I'm going to show you Notion - an all-in-one workspace that keeps teams organized.")
            await asyncio.sleep(PAUSE_MED)

            # === 2. DASHBOARD & INTERFACE ===
            await go_to_demo_home_ui(notion_page)
            await show_sidebar(notion_page)
            await asyncio.sleep(PAUSE_SHORT)
            
            await speak_func("Here's the dashboard. The sidebar has all your pages and workspaces. Everything is built from blocks - text, tables, databases, checklists - making it infinitely flexible.")
            await asyncio.sleep(PAUSE_MED)

            # Add intro text AFTER speaking
            await focus_editor(notion_page)
            await type_with_human_delay(notion_page, "Project Apollo - Central Hub", 45)
            await asyncio.sleep(PAUSE_MED)

            # === 3. CREATE PAGE & CONTENT ===
            await speak_func("Creating pages is instant. Let me build a kickoff meeting page with structured content.")
            await asyncio.sleep(PAUSE_SHORT)
            
            kickoff_page = await create_page_api("Project Apollo - Kickoff")
            if not kickoff_page:
                await speak_func("Couldn't create the page. Continuing.")
                return
            
            page_id = kickoff_page["id"]
            await go_to_page_ui(notion_page, page_id)
            await asyncio.sleep(1.0)
            await focus_editor(notion_page)
            await asyncio.sleep(PAUSE_SHORT)
            
            await speak_func("I'm adding headings, to-do lists, and callouts. You can drag and drop any block to reorganize instantly.")
            await asyncio.sleep(PAUSE_SHORT)
            
            # NOW type AFTER speaking
            await notion_page.keyboard.type("/h2", delay=40)
            await asyncio.sleep(0.5)
            await notion_page.keyboard.press("Enter")
            await asyncio.sleep(0.2)
            await type_with_human_delay(notion_page, "Agenda & Goals", 50)
            await notion_page.keyboard.press("Enter")
            await asyncio.sleep(0.3)
            
            # Add to-do list
            await notion_page.keyboard.type("/todo", delay=40)
            await asyncio.sleep(0.5)
            await notion_page.keyboard.press("Enter")
            await type_with_human_delay(notion_page, "Define Q4 launch timeline", 45)
            await notion_page.keyboard.press("Enter")
            await type_with_human_delay(notion_page, "Assign initial roles", 45)
            await notion_page.keyboard.press("Enter")
            await notion_page.keyboard.press("Enter")
            await asyncio.sleep(0.3)
            
            # Add callout
            await notion_page.keyboard.type("/callout", delay=40)
            await asyncio.sleep(0.5)
            await notion_page.keyboard.press("Enter")
            await asyncio.sleep(0.2)
            await type_with_human_delay(notion_page, "Launch date: November 25th", 45)
            await notion_page.keyboard.press("Enter")
            await asyncio.sleep(PAUSE_MED)

            # === 4. TABLE DEMO ===
            await speak_func("Here's a quick table for team structure.")
            await asyncio.sleep(PAUSE_SHORT)
            
            await create_empty_table_api(page_id)
            await asyncio.sleep(1.5)
            
            table_data = [
                ["Marketing", "Sarah"],
                ["Engineering", "David"]
            ]
            await fill_table_manually(notion_page, table_data)
            await asyncio.sleep(PAUSE_MED)

            # === 5. PROJECT TIMELINE DATABASE ===
            await speak_func("Now the power feature: unified project databases. This combines timeline tracking, task management, and team assignments.")
            await asyncio.sleep(PAUSE_SHORT)
            
            timeline_db = await create_project_timeline_database_api(PARENT_PAGE_ID, "Project Apollo - Timeline")
            if not timeline_db:
                await speak_func("Couldn't create the database.")
                return
            
            timeline_id = timeline_db["id"]
            await go_to_page_ui(notion_page, timeline_id)
            await asyncio.sleep(1.5)
            
            await speak_func("I'll now create tasks with color-coded statuses. Scheduled tasks in gray, In Progress in blue, and Completed in green. Each assigned to a team lead with due dates.")
            await asyncio.sleep(PAUSE_SHORT)
            
            # Populate database
            timeline_tasks = [
                ["Design Phase Complete", "Completed", "Emma Wilson", "2025-10-31"],
                ["Development Kickoff", "In Progress", "David Kumar", "2025-11-05"],
                ["Beta Launch", "Scheduled", "James Rodriguez", "2025-11-15"],
                ["Draft marketing copy", "In Progress", "Sarah Chen", "2025-10-24"],
                ["Develop landing page", "Scheduled", "David Kumar", "2025-11-07"],
                ["Finalize launch assets", "Scheduled", "Emma Wilson", "2025-11-18"],
                ["Public Release", "Scheduled", "Sarah Chen", "2025-11-25"],
                ["Post-Launch Support", "Scheduled", "Lisa Wang", "2025-12-05"]
            ]
            
            await add_timeline_tasks_via_api(timeline_id, timeline_tasks)
            await asyncio.sleep(PAUSE_LONG)

            # === 6. COLLABORATION - PARALLEL TYPING AND SPEAKING ===
            # Create and navigate to page FIRST
            collab_page = await create_page_api("Collaboration & Integrations")
            if not collab_page:
                await speak_func("Couldn't create collaboration page.")
                return
            
            collab_page_id = collab_page["id"]
            await go_to_page_ui(notion_page, collab_page_id)
            await asyncio.sleep(1.5)
            await focus_editor(notion_page)
            await asyncio.sleep(0.5)
            
            # Now speak and type in parallel
            async def type_collaboration():
                await asyncio.sleep(0.8)  # Small delay to let speech start
                
                await notion_page.keyboard.type("/bullet", delay=40)
                await asyncio.sleep(0.5)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Invite team members with custom access", 40)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Add inline comments for feedback", 40)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Assign tasks with due dates", 40)
                await notion_page.keyboard.press("Enter")
                await notion_page.keyboard.press("Enter")
                await asyncio.sleep(0.4)
                
                await notion_page.keyboard.type("/h2", delay=40)
                await asyncio.sleep(0.5)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Integrations", 50)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Embed Figma, Google Drive, and videos directly", 40)
            
            typing_task = asyncio.create_task(type_collaboration())
            
            await speak_func("Collaboration is seamless. Invite teammates with specific permissions, add comments on any block, and assign tasks with deadlines.")
            await asyncio.sleep(PAUSE_SHORT)
            await speak_func("You can also embed live content from Figma, Google Drive, and YouTube directly into your pages.")
            
            await typing_task
            await asyncio.sleep(PAUSE_LONG)

            # === 7. PRICING - PARALLEL TYPING AND SPEAKING ===
            plans_page = await create_page_api("Pricing")
            if not plans_page:
                await speak_func("Couldn't create pricing page.")
                return
            
            # Navigate to pricing page FIRST
            await go_to_page_ui(notion_page, plans_page["id"])
            await asyncio.sleep(1.5)
            await focus_editor(notion_page)
            await asyncio.sleep(0.5)
            
            # Type pricing in parallel with speaking
            async def type_pricing():
                await asyncio.sleep(0.6)  # Small delay to let speech start
                
                # Free plan
                await notion_page.keyboard.type("/h2", delay=40)
                await asyncio.sleep(0.5)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Free - Unlimited pages", 45)
                await notion_page.keyboard.press("Enter")
                await notion_page.keyboard.press("Enter")
                
                # Personal Pro
                await notion_page.keyboard.type("/h2", delay=40)
                await asyncio.sleep(0.5)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Personal Pro - $10/month", 45)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "File uploads, version history", 40)
                await notion_page.keyboard.press("Enter")
                await notion_page.keyboard.press("Enter")
                
                # Team
                await notion_page.keyboard.type("/h2", delay=40)
                await asyncio.sleep(0.5)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Team - $20/person/month", 45)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Advanced permissions, analytics", 40)
                await notion_page.keyboard.press("Enter")
                await notion_page.keyboard.press("Enter")
                
                # Enterprise
                await notion_page.keyboard.type("/h2", delay=40)
                await asyncio.sleep(0.5)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Enterprise - Custom pricing", 45)
                await notion_page.keyboard.press("Enter")
                await type_with_human_delay(notion_page, "Advanced security, SSO", 40)
            
            pricing_task = asyncio.create_task(type_pricing())
            
            await speak_func("Four plans to choose from. Free with unlimited pages. Personal Pro at ten dollars monthly. Team at twenty per person. And Enterprise with custom pricing.")
            
            await pricing_task
            await asyncio.sleep(PAUSE_LONG)

            # === 8. WRAP-UP ===
            await go_to_demo_home_ui(notion_page)
            await asyncio.sleep(1.0)

            await speak_func("That's Notion. One workspace for everything. Happy to answer any questions.")
            
            logging.info("✅ Optimized Notion demo finished.")

        except Exception as e:
            logging.exception(f"❌ Error during demo: {e}")
            await speak_func("An error occurred. Ready for new commands.")