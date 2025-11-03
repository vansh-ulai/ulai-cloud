import os
import time
import json
import re
import asyncio
import logging
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page # Import Page type hint
from PIL import Image
import google.generativeai as genai

# Import TTS and user speaking event check (if available)
try:
    from core.tts_handler import speak_text_virtual
    #REMOVED circular import 'from core.meet_bot import user_speaking'
except ImportError:
    # Fallbacks if imports fail (e.g., running standalone)
    def speak_text_virtual(text):
        print(f"[TTS-Fallback] {text}")
    # user_speaking event will be passed in as an argument
    
# ---------------- CONFIG ----------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

#FIX: Use the latest, fastest flash model
MODEL_NAME = "gemini-2.5-flash" 
TEMP_DIR = "temp"
LOG = logging.getLogger(__name__) # Use standard logger

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Custom exception for interruptions
class DemoInterruptedException(Exception):
    pass

# ---------------- HELPER FUNCTIONS ----------------

async def get_interactable_elements(page: Page): # Added type hint
    """Helper to safely get links and buttons from the page."""
    all_links = []
    all_buttons = []
    if not page or page.is_closed():
        LOG.warning("⚠️ Demo page not available for getting elements.")
        return [], []

    try:
        # Removed invalid timeout argument
        all_links = await page.locator('a[href]:visible').evaluate_all(
            '(elements) => elements.map(e => ({ text: e.innerText.trim(), href: e.href })).filter(e => e.text && e.text.length > 1 && e.text.length < 100)'
            # Removed timeout=3000
        )
    except Exception as e:
        LOG.warning(f"⚠️ Could not get links: {e}")

    try:
        # Removed invalid timeout argument
        all_buttons = await page.locator('button:visible, [role="button"]:visible').evaluate_all(
            '(elements) => elements.map(e => ({ text: e.innerText.trim(), name: e.name, id: e.id })).filter(e => e.text && e.text.length > 1 && e.text.length < 100)'
             # Removed timeout=3000
        )
    except Exception as e:
        LOG.warning(f"⚠️ Could not get buttons: {e}")

    # Limit the number of elements sent to AI
    return all_links[:20], all_buttons[:20]


# ---------------- VISION-GUIDED GEMINI ENGINE ----------------
async def ask_gemini_vision_for_actions(screenshot_path, current_url, goal, memory_context, creds,
                                        website_knowledge=None, demo_state=None, interactable_elements=None):
    """
    FULLY VISION-GUIDED: Ask Gemini to analyze screenshot and plan actions.
    Enhanced with interactable elements for better selector accuracy.
    """
    try:
        img = Image.open(screenshot_path)
    except Exception as img_e:
        LOG.error(f"❌ Failed to open screenshot image for vision: {img_e}")
        raise ValueError("Failed to process screen image") from img_e

    email, password = creds

    # Build rich context from website knowledge if available
    context_info = ""
    if website_knowledge:
        context_info = f"""
WEBSITE KNOWLEDGE (from Context Agent):
- Name: {website_knowledge.get('name', 'Unknown')}
- Purpose: {website_knowledge.get('purpose', 'Unknown')}
- Features: {', '.join(website_knowledge.get('main_features', [])[:3])}
- Auth Method: {website_knowledge.get('authentication', 'Unknown')}
"""

    if demo_state:
        context_info += f"""
CURRENT DEMO STATE:
- Current Step: {demo_state.get('current_step', 'Unknown')}
- Page: {demo_state.get('page_description', 'Unknown')}
- Last Action: {demo_state.get('last_action', 'Unknown')}
"""

    # --- Safely create example selectors ---
    example_link_selector = 'a:has-text("Example Link")' # Fallback
    example_button_selector = 'button:has-text("Example Button")' # Fallback
    if interactable_elements:
        links, buttons = interactable_elements
        #Remove indent=2 for smaller, faster prompt
        context_info += f"""
AVAILABLE INTERACTABLE ELEMENTS (Visible on current page):
- Links: {json.dumps(links)}
- Buttons: {json.dumps(buttons)}
"""
        # Only add examples if lists are not empty and elements have needed keys
        if links and 'href' in links[0] and links[0]['href']:
            example_link_selector = f'a[href="{links[0]["href"]}"]'
        if buttons and 'text' in buttons[0] and buttons[0]['text']:
            example_button_selector = f'button:has-text("{buttons[0]["text"]}")'
    # --- End Fix ---

    prompt = f"""You are a VISION-FIRST autonomous web agent. Your ONLY source of truth is what you SEE in the screenshot.

{context_info}

GOAL: {goal}

USER CREDENTIALS:
- Email: {email}
- Password: {password}

MEMORY (what you've done so far):
{memory_context[-2000:]}

Current URL: {current_url}

CRITICAL INSTRUCTIONS - VISION-FIRST APPROACH:
1. **LOOK AT THE SCREENSHOT CAREFULLY** - This is your primary data source.
2. **VERIFY ELEMENT EXISTENCE:** Critically verify the target element (e.g., button text, input placeholder) EXISTS and is VISIBLE in the screenshot AND matches an entry in the ELEMENT LIST before planning a click/fill action.
3. **USE THE ELEMENT LIST:** Cross-reference visual analysis with the list to create ACCURATE selectors (e.g., `{example_link_selector}` or `{example_button_selector}`). Prioritize text matches. If an element is clearly visible but NOT in the list, attempt a selector based purely on visuals (e.g., placeholder text).
4. **BATCH VISIBLE ACTIONS:** If you see email field + continue button, plan both actions. If you see email + password + sign in, plan all three.
5. **IMPOSSIBLE ACTIONS:** If the *next logical step* towards the goal isn't visible or interactable (e.g., no 'Login' button visible), return an EMPTY "actions" array and explain why in "visual_analysis".

6. **STOP Condition (*** MOST IMPORTANT RULE ***):**
    - Stop (set `goal_status: "complete"`) ONLY when you clearly SEE proof of success (e.g., a dashboard, a "Welcome" message, user profile).
    - If you see a login form, input fields, or a "Sign In" / "Login" button, the goal is **`in_progress`**, NOT `complete`.
    - Do NOT set `goal_status: "complete"` just because a login button is visible. You must *click* it and *then* see the success page.

SELECTOR BUILDING STRATEGY:
- Buttons/Links: Prefer `*:has-text("Exact Visible Text")`. Use element list href/name/id as fallback.
- Inputs: Use `input[placeholder*="keyword"]`, `input[type="email/password"]`, or associated label text.

Your response MUST be valid JSON:
{{
  "actions": [
    {{
      "action": "fill|click|navigate|back|wait|stop",
      "selector": "CSS selector built from visual analysis AND element list",
      "value": "text or URL",
      "reasoning": "WHY you chose this based on what you SEE and the ELEMENT LIST",
      "pre_narration": "SHORT description of action (max 10 words)",
      "post_narration": "2-3 word confirmation",
      "expect_new_page": true/false,
      "confidence": "high|medium|low"
    }}
    // Include multiple actions if batching
  ],
  "page_state": "login_page|password_page|dashboard|error|loading|unknown", // Best guess based on visuals
  "goal_status": "not_started|in_progress|complete|blocked", // Is goal achieved? (See Rule 6)
  "next_observation_needed": true/false // Usually true unless goal_status is complete or blocked
}}

Now analyze the screenshot and provide your vision-guided action plan:"""

    model = genai.GenerativeModel(MODEL_NAME)
    response = await asyncio.to_thread(
        model.generate_content,
        [prompt, img],
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=2048 # Increased token limit
        )
    )

    # --- SAFETY CHECK ---
    if not response.parts:
        finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"
        error_msg = f"Vision analysis blocked. Finish reason: {finish_reason}"
        LOG.error(f"❌ Vision Agent Error: {error_msg}")
        try:
            LOG.error(f"Safety Feedback: {response.prompt_feedback}")
        except Exception: pass
        raise ValueError(error_msg)

    text = response.text.strip()
    # Try to find JSON block, be more lenient
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL) # Look for markdown block first
    if not match:
        match = re.search(r'(\{.*?\})', text, re.DOTALL) # Fallback to any JSON block

    if not match:
        LOG.error(f"❌ Vision Agent did not return valid JSON structure: {text[:500]}...")
        raise ValueError(f"AI did not return valid JSON structure")

    try:
        json_str = match.group(1)
        # Handle potential escape sequences before parsing
        json_str = json_str.replace('\\`', '`').replace('\\*', '*') # Common issues
        parsed = json.loads(json_str)
        return parsed
    except json.JSONDecodeError as json_e:
        LOG.error(f"❌ Vision Agent: Failed to decode JSON - {json_e}")
        LOG.debug(f"Invalid JSON string from Vision Agent: {json_str}")
        raise ValueError("Failed to parse vision action plan JSON") from json_e


# ---------------- SAFE ACTION EXECUTION ----------------
async def safe_click(page: Page, selector: str, force=False, silent=False):
    """Try to click an element with multiple fallback strategies"""
    if not page or page.is_closed(): return False
    try:
        locator = page.locator(selector).first
        # Increased timeout, wait for element to exist first
        await locator.wait_for(state="attached", timeout=3000)

        # Check visibility and enabled state before clicking
        is_visible = await locator.is_visible(timeout=2000)
        is_enabled = await locator.is_enabled(timeout=1000)

        if is_visible and is_enabled:
            await locator.click(timeout=4000) # Slightly increased click timeout
            if not silent: LOG.info(f"✅ Clicked selector: {selector}")
            return True
        elif force and is_visible: # Force only if visible but maybe not enabled
            if not silent: LOG.warning(f"⚠️ Forcing click on potentially disabled element: {selector}")
            await locator.click(timeout=4000, force=True)
            return True
        else:
            if not silent: LOG.warning(f"⚠️ Element not clickable (Visible: {is_visible}, Enabled: {is_enabled}): {selector}")
            return False

    except Exception as e:
        # Reduce log noise for common timeout errors unless verbose logging is on
        if "timeout" in str(e).lower() and LOG.getEffectiveLevel() > logging.DEBUG:
            if not silent: LOG.warning(f"⏳ Timeout during click for {selector}")
        else:
            if not silent: LOG.error(f"❌ Click failed for {selector}: {e}", exc_info=False) # Less verbose log
    return False


async def smart_fill_field(page: Page, selector: str, value: str, is_sensitive=False, silent=False):
    """Smart field filling with multiple strategies"""
    if not page or page.is_closed(): return False
    try:
        locator = page.locator(selector).first
        
        # INCREASED TIMEOUTS 
        await locator.wait_for(state="attached", timeout=5000) # From 3000

        if not await locator.is_visible(timeout=3000): # From 2000
            if not silent:
                print(f"⚠️ Field not visible: {selector}")
            return False

        # Click to focus
        await locator.click(timeout=3000)
        await asyncio.sleep(0.05)

        # Clear existing content using JS for reliability
        await locator.evaluate('element => element.value = ""')
        await asyncio.sleep(0.05)


        # Fill value
        display_value = value[:3] + "***" if is_sensitive else value
        if not silent:
            print(f"✏️ Filling field '{selector}' with: {display_value}")

        # Use fill directly, it's generally more reliable than type
        # INCREASED TIMEOUT
        await locator.fill(value, timeout=7000) # From 5000
        await asyncio.sleep(0.15) # Short pause after filling

        # Verification step (optional but good)
        current_val = await locator.input_value()
        if current_val != value:
            if not silent: LOG.warning(f"⚠️ Fill verification failed for {selector}. Expected '{value}', got '{current_val}'")
            # Optional: Retry with type?
            # await locator.press_sequentially(value, delay=50)

        return True
    except Exception as e:
        if not silent:
            # Less verbose logging for fill failures unless debugging
            if "timeout" in str(e).lower() and LOG.getEffectiveLevel() > logging.DEBUG:
                LOG.warning(f"⏳ Timeout during fill for {selector}")
            else:
                LOG.error(f"❌ Fill failed for {selector}: {e}", exc_info=False)
    return False


# ---------------- ENHANCED ACTION EXECUTOR ----------------
async def async_speak_and_wait(text, base_delay=0.8, tts_lock=None, speaking_event=None, user_speaking_event=None):
    """Speak with TTS lock and speaking event, check for user interruption"""
    if not text or text.strip() == "":
        return
        
    # Check if user is speaking BEFORE trying to speak
    if user_speaking_event and user_speaking_event.is_set():
        LOG.info("🤫 User is speaking, skipping AI speech.")
        return

    LOG.info(f"🔊 Speaking: {text}")

    if speaking_event:
        speaking_event.set()

    await asyncio.sleep(0.03) # Small buffer

    interrupted = False
    try:
        # Correct pattern for acquiring a lock with a timeout
        await asyncio.wait_for(tts_lock.acquire(), timeout=5.0)
        try:
            # We now have the lock
            # Check again inside lock
            if user_speaking_event and user_speaking_event.is_set():
                LOG.info("🤫 User started speaking during lock, cancelling AI speech.")
                interrupted = True
                return # Exit early

            # --- Actual TTS Call ---
            await asyncio.to_thread(speak_text_virtual, text)
            # --- End TTS Call ---

        finally:
            tts_lock.release() # ALWAYS release the lock

        # Wait after speaking, but allow interruption
        word_count = len(text.split())
        estimated_duration = (word_count / 3.5) # Slightly faster WPM assumption
        wait_time = max(estimated_duration, base_delay, 0.5) # Shorter min wait

        start_wait = time.time()
        while time.time() - start_wait < wait_time:
            if user_speaking_event and user_speaking_event.is_set():
                LOG.info("🤫 User started speaking, cutting AI wait short.")
                interrupted = True
                break # Exit wait loop
            await asyncio.sleep(0.1) # Check every 100ms

    except asyncio.TimeoutError:
        LOG.error("❌ Timed out waiting for TTS lock.")
        interrupted = True # Treat timeout as interruption
    except Exception as tts_e:
        LOG.error(f"❌ Error during TTS or waiting: {tts_e}")
        interrupted = True # Treat other errors as interruption
    finally:
        await asyncio.sleep(0.1) # Short buffer
        if speaking_event:
            speaking_event.clear()


async def check_pause(pause_event, demo_interrupted_event):
    """Check and wait for pause event OR interruption event"""

    # Check for interruption first (higher priority)
    if demo_interrupted_event and demo_interrupted_event.is_set():
        LOG.info("check_pause: Interruption event is set.")
        demo_interrupted_event.clear() # Consume the event
        raise DemoInterruptedException("Demo interrupted by user command")

    # Check for pause
    if pause_event and not pause_event.is_set():
        LOG.info("⏸️ ========== DEMO PAUSED (check_pause) ==========")
        try:
            # Wait indefinitely until pause_event is set OR interruption occurs
            wait_pause = asyncio.create_task(pause_event.wait())
            # Ensure demo_interrupted_event exists before creating task
            wait_interrupt = asyncio.create_task(demo_interrupted_event.wait()) if demo_interrupted_event else None

            tasks_to_wait = [task for task in [wait_pause, wait_interrupt] if task]
            if not tasks_to_wait: # Should not happen if pause_event exists
                LOG.error("check_pause: No events to wait for!")
                return

            done, pending = await asyncio.wait(tasks_to_wait, return_when=asyncio.FIRST_COMPLETED)

            # Cancel pending waits
            for task in pending:
                task.cancel()
                try: await task # Allow cancellation to propagate
                except asyncio.CancelledError: pass

            if wait_interrupt in done:
                LOG.info("check_pause: Interrupted while paused.")
                if demo_interrupted_event: demo_interrupted_event.clear() # Consume the event
                raise DemoInterruptedException("Demo interrupted by user command while paused")
            elif wait_pause in done:
                LOG.info("▶️ ========== DEMO RESUMED (check_pause) ==========")
                # Pause finished normally, re-check interruption just in case
                if demo_interrupted_event and demo_interrupted_event.is_set():
                    LOG.info("check_pause: Interrupted immediately after resume.")
                    demo_interrupted_event.clear()
                    raise DemoInterruptedException("Demo interrupted immediately after resume")

        except asyncio.CancelledError:
            LOG.info("check_pause: Wait cancelled.")
            raise # Re-raise cancellation

async def perform_single_vision_action(page: Page, action_obj: dict, creds: tuple, pause_event=None,
                                       tts_lock=None, speaking_event=None, silent=False,
                                       demo_interrupted_event=None, user_speaking_event=None):
    """
    Execute a single action from vision-guided analysis.
    Returns:
    - "STOP": AI wants to stop
    - "CONTINUE": Action done, continue sequence
    - "PAGE_CHANGED": Autonomous action caused navigation, force re-observe
    - "FAILED": The action (e.g., fill, click) failed
    - Page (object): User command opened a new tab, return it
    """
    await check_pause(pause_event, demo_interrupted_event)

    action = action_obj.get("action")
    selector = action_obj.get("selector", "")
    value = action_obj.get("value", "")
    reasoning = action_obj.get("reasoning", "")
    confidence = action_obj.get("confidence", "medium")
    pre_narration = action_obj.get("pre_narration", "")
    post_narration = action_obj.get("post_narration", "")
    expect_new_page = action_obj.get("expect_new_page", False)

    # Basic validation
    if not action:
        LOG.warning("⚠️ Received action object with no 'action' specified.")
        return "CONTINUE" # Skip this invalid action

    email, password = creds

    # Replace credential placeholders
    if value:
        value_lower = value.lower()
        reasoning_lower = reasoning.lower() if reasoning else ""
        # Be more specific: check if 'email' is mentioned without 'password'
        if "{email}" in value_lower or ("email" in reasoning_lower and "password" not in reasoning_lower):
            value = email
        elif "{password}" in value_lower or "password" in reasoning_lower:
            value = password

    if not silent:
        print(f"\n🎯 ACTION: {action}")
        if selector and selector != 'none': print(f"   Selector: {selector}")
        if value and action == "fill": print(f"   Value: {'***' if 'password' in reasoning_lower else value[:20]}")
        print(f"   Confidence: {confidence}")
        if reasoning: print(f"   Reasoning: {reasoning[:100]}...")


    try:
        # --- Execute action ---
        success = False # Flag for action success
        page_changed = False # Flag if action likely changed the page

        if action == "stop":
            return "STOP"

        if action == "wait":
            wait_time = 1.5
            try:
                wait_time = float(value) if value else 1.5
            except ValueError:
                LOG.warning(f"Invalid wait time '{value}', defaulting to 1.5s")

            if not silent: print(f"⏳ Waiting {wait_time}s...")
            # Wait but allow interruption
            start_wait = time.time()
            while time.time() - start_wait < wait_time:
                await check_pause(pause_event, demo_interrupted_event) # Check within wait loop
                await asyncio.sleep(0.1)
            success = True # Wait action always "succeeds"
            # return "CONTINUE" # <-- This was the old logic, let it fall through

        # Pre-action narration
        if pre_narration and not silent:
            await check_pause(pause_event, demo_interrupted_event)
            await async_speak_and_wait(pre_narration, 0.2, tts_lock, speaking_event, user_speaking_event)

        await check_pause(pause_event, demo_interrupted_event)


        if action == "back":
            if not silent: print("🔙 Going back...")
            try:
                # Try to go back normally first
                async with page.expect_navigation(timeout=5000, wait_until="domcontentloaded"):
                    await page.go_back()
                if not silent: print("✅ Navigated back successfully.")
                success = True
                page_changed = True # This is a normal navigation, force re-observe
            except Exception as nav_e:
                if not silent: print(f"⚠️ Go back failed or timed out: {nav_e}")
                
                # Fallback for "go back" command (close tab)
                all_pages = page.context.pages
                if "no navigation" in str(nav_e) and len(all_pages) > 1:
                    if not silent: print(f"...No navigation, trying to close current tab (total pages: {len(all_pages)}).")
                    try:
                        # Find the *previous* page (page before the last one)
                        previous_page = all_pages[-2]
                        
                        await page.close() # Close the current page
                        if not silent: print("...Closed current tab.")
                        
                        # Return the *previous* page to the caller
                        await previous_page.bring_to_front()
                        if not silent: print(f"✅ Switched back to previous page: {previous_page.url}")
                        return previous_page # <-- Return the Page object
                        
                    except Exception as close_e:
                        if not silent: print(f"⚠️ Failed to close tab or find previous: {close_e}")
                        success = False
                        page_changed = False # Failed
                else:
                    success = False # Mark as failed for narration
            
            # If we got here, it was either a successful page.go_back() or a failed close
            if page_changed: # Only true if page.go_back() worked
                # Force re-observe
                LOG.info(f"Action '{action}' changed the page. Stopping current action sequence to re-observe.")
                return "PAGE_CHANGED"
            else:
                success = False # Explicitly


        elif action == "navigate" and value and value.startswith("http"):
            if not silent: print(f"🌐 Navigating to: {value}")
            try:
                # Use context manager for 'goto'
                async with page.expect_navigation(timeout=15000, wait_until="domcontentloaded"):
                    await page.goto(value)
                if not silent: print(f"✅ Navigated to {value} successfully.")
                success = True
                page_changed = True
            except Exception as nav_e:
                if not silent: print(f"⚠️ Navigation to {value} failed or timed out: {nav_e}")
                success = False
            await asyncio.sleep(1.0) # Pause after navigation attempt

        elif action == "fill" and selector:
            is_password = "password" in selector.lower() or ("password" in reasoning.lower() if reasoning else False)
            success = await smart_fill_field(page, selector, value, is_password, silent=silent)
            # 'success' flag is now set to True or False

        elif action == "click" and selector:
            # Check if expecting navigation based on AI or element type (<a> tag)
            navigation_expected = expect_new_page or selector.strip().startswith('a[href')

            if navigation_expected:
                if not silent: print(f"🖱️ Clicking (expecting navigation OR new tab): {selector}")
                context = page.context

                # Use wait_for_event("load") instead of wait_for_navigation()
                nav_task = asyncio.create_task(page.wait_for_event("load", timeout=7000))
                new_page_task = asyncio.create_task(context.wait_for_event("page", timeout=7000))
                
                await asyncio.sleep(0.1) # small delay for listeners
                
                # Perform the click
                click_success = await safe_click(page, selector, silent=silent)
                if not click_success:
                    if not silent: print("... Retrying click with force")
                    click_success = await safe_click(page, selector, force=True, silent=silent)
                
                if not click_success:
                    if not silent: print(f"⚠️ FINAL Click failed for: {selector}")
                    nav_task.cancel()
                    new_page_task.cancel()
                    success = False # Click itself failed
                else:
                    # Wait for *either* event to complete
                    done, pending = await asyncio.wait(
                        [nav_task, new_page_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    try:
                        if new_page_task in done:
                            # New page opened! Return it, DO NOT CLOSE IT.
                            new_page_info = await new_page_task # Get the new page object
                            if not silent: print(f"✅ New tab opened (event detected). URL: {new_page_info.url}")
                            
                            # Wait for the new page to finish loading
                            try:
                                await new_page_info.wait_for_load_state("domcontentloaded", timeout=5000)
                            except Exception as load_e:
                                if not silent: print(f"⚠️ New tab opened, but load state timed out: {load_e}")

                            success = True
                            return new_page_info # <-- Return the new Page object
                        
                        elif nav_task in done:
                            # Navigation happened on the *current* page
                            await nav_task # Will raise exception if nav failed
                            if not silent: print("✅ Click successful, navigation completed on current page.")
                            page_changed = True
                            success = True
                            
                    except Exception as click_nav_e:
                        # This catches timeout if *neither* event happens
                        if not silent: print(f"⚠️ Click (expecting nav/tab) failed or timed out: {click_nav_e}")
                        success = False
                    
                    # Cancel any pending tasks
                    for task in pending:
                        task.cancel()
                        try: await task # Allow cancellation
                        except asyncio.CancelledError: pass
                        
                await asyncio.sleep(1.0) # Pause after potential navigation
            
            else:
                # Standard click, no navigation expected
                if not silent: print(f"🖱️ Clicking (no navigation expected): {selector}")
                success = await safe_click(page, selector, silent=silent)
                if not success:
                    if not silent: print("... Retrying click with force")
                    success = await safe_click(page, selector, force=True, silent=silent)
                await asyncio.sleep(0.5) # Shorter pause for non-nav clicks

            # Final check if click failed completely
            if not success:
                if not silent: print(f"⚠️ FINAL Click failed for: {selector}")
        
        elif action not in ["back", "navigate", "fill", "click", "wait", "stop"]:
             LOG.warning(f"⚠️ Unknown action type: {action}")
             success = False # Mark unknown actions as failed


        # --- Post-action ---
        # Post-action narration (only if action was attempted)
        if post_narration and not silent:
            await check_pause(pause_event, demo_interrupted_event)
            final_narration = post_narration if success else f"Tried to {action}, but encountered an issue."
            await async_speak_and_wait(final_narration, 0.15, tts_lock, speaking_event, user_speaking_event)

        # If action (like nav/click) changed page, stop sequence & re-observe 
        if page_changed:
            LOG.info(f"Action '{action}' changed the page. Stopping current action sequence to re-observe.")
            return "PAGE_CHANGED"

        # Return FAILED if success is false 
        if not success:
            LOG.warning(f"Action '{action}' failed. Returning FAILED.")
            return "FAILED"

        return "CONTINUE" # Continue the normal flow (unless interrupted)

    except DemoInterruptedException:
        raise # Re-raise interruption to be caught by the main loop
    except Exception as e:
        if not silent:
            print(f"❌ Action execution failed critically: {e}")
            import traceback
            traceback.print_exc()
        return "FAILED" # Treat critical errors as failures

async def perform_action_sequence(page: Page, ai_response: dict, creds: tuple, pause_event=None, demo_state=None,
                                  tts_lock=None, speaking_event=None, silent=False,
                                  demo_interrupted_event=None, user_speaking_event=None):
    """
    Execute vision-guided action sequence
    Returns: "CONTINUE", "STOP", "PAGE_CHANGED", "FAILED", or a Page object
    """
    # Page for type checking 
    from playwright.async_api import Page
    
    await check_pause(pause_event, demo_interrupted_event)

    actions = ai_response.get("actions", [])
    page_state = ai_response.get("page_state", "unknown")
    goal_status = ai_response.get("goal_status", "in_progress")

    if not silent:
        print(f"\n{'='*70}")
        print(f"📄 Page State: {page_state}")
        print(f"🎯 Goal Status: {goal_status}")
        print(f"🎬 Planned Actions: {len(actions)}")
        print(f"{'='*70}")

    # Update demo state with context
    if demo_state is not None:
        demo_state["current_step"] = f"{page_state} - {len(actions)} actions planned"
        demo_state["page_description"] = page_state # Update page description
        demo_state["last_action"] = actions[0].get("action") if actions else "analyzing"

        context_update = f"Observed state: {page_state}. Planned {len(actions)} actions."
        current_context = demo_state.get("context", "")
        if len(current_context) > 500:
            demo_state["context"] = current_context[-500:] + f"\n{context_update}"
        else:
            demo_state["context"] = current_context + f"\n{context_update}"

    # Check for completion
    if goal_status == "complete":
        if not silent:
            print("🎉 Goal marked as COMPLETE by vision analysis!")
        if actions and actions[0].get("action") == "stop" and actions[0].get("pre_narration") and not silent:
            await check_pause(pause_event, demo_interrupted_event)
            await async_speak_and_wait(actions[0].get("pre_narration"), 0.4, tts_lock, speaking_event, user_speaking_event)
        return "STOP" # Signal completion

    # Check if AI decided it's blocked or no actions needed
    if not actions and goal_status != "complete":
        if not silent:
            print("⚠️ AI returned 0 actions. Goal status is not complete. Assuming blocked or waiting.")
            analysis = ai_response.get("visual_analysis", "AI determined no actions possible currently.")
            await async_speak_and_wait(f"Hmm, {analysis[:150]}. Let me re-evaluate.", 0.4, tts_lock, speaking_event, user_speaking_event)
        return "CONTINUE" # Forces re-observation


    # Execute actions
    final_result = "CONTINUE"
    for idx, action_obj in enumerate(actions, 1):
        if not silent:
            print(f"\n▶️ Executing Action {idx}/{len(actions)}")

        result = await perform_single_vision_action(
            page, action_obj, creds, pause_event, tts_lock, speaking_event, silent=silent,
            demo_interrupted_event=demo_interrupted_event, user_speaking_event=user_speaking_event
        )

        if result == "STOP":
            final_result = "STOP"
            break # Exit action loop if stop signal received
        if result == "FAILED":
            final_result = "FAILED"
            LOG.warning("Action sequence failed, breaking loop.")
            break
        
        #  Check for autonomous page change
        if result == "PAGE_CHANGED":
            final_result = "CONTINUE" # The main loop should continue
            LOG.info("Page changed during action sequence, breaking to re-observe.")
            break # Exit action loop to force re-observation

        #Check for new Page object (from user command) 
        if isinstance(result, Page):
            final_result = result # Pass the Page object up
            LOG.info("New page detected, passing Page object up to caller.")
            break

        # Small delay between batched actions IF the loop continues
        if idx < len(actions):
            await check_pause(pause_event, demo_interrupted_event) # Check between batched actions
            await asyncio.sleep(0.2)

    return final_result


# ---------------- MAIN FLOW WITH FULL VISION GUIDANCE ----------------
async def async_autonomous_web_flow_with_narration(demo_page_param: Page, goal="login", headless=False, creds=None,
                                                 pause_event=None, demo_state=None, tts_lock=None,
                                                 speaking_event=None, website_knowledge=None,
                                                 demo_interrupted_event=None, user_speaking_event=None): # Pass user_speaking
    """
    FULLY VISION-GUIDED autonomous flow with AI orchestrator integration.
    Handles interruptions.
    """
    page = demo_page_param
    if not page or page.is_closed():
        LOG.error("❌ CRITICAL: demo_page is None or closed - cannot proceed")
        await async_speak_and_wait("An error occurred - the demo page is not available.",
                                  0.3, tts_lock, speaking_event, user_speaking_event) # Pass user_speaking_event
        return

    memory_context = demo_state.get("context", "") # Initialize memory from state

    try:
        observation_count = 0
        consecutive_failures = 0
        max_observations = 18 # Increased slightly

        while observation_count < max_observations:
            await check_pause(pause_event, demo_interrupted_event) # Check at start of loop

            observation_count += 1
            print(f"\n{'='*70}")
            print(f"🔍 OBSERVATION #{observation_count}")
            print(f"{'='*70}")

            # Take screenshot - our source of truth
            screenshot_path = os.path.join(TEMP_DIR, f"obs_{observation_count}.png")

            try:
                # Ensure page is still valid before screenshot
                if page.is_closed(): raise Exception("Page closed unexpectedly")
                await page.screenshot(path=screenshot_path, timeout=5000)
            except Exception as e:
                LOG.error(f"❌ Screenshot failed: {e}")
                await async_speak_and_wait("Unable to capture the screen state.", 0.3, tts_lock, speaking_event, user_speaking_event)
                consecutive_failures += 1
                if consecutive_failures >= 2: break # Stop after 2 screenshot failures
                await asyncio.sleep(1.0)
                continue # Try next observation

            current_url = page.url
            print(f"📍 Current URL: {current_url}")
            if demo_state: demo_state["url"] = current_url # Update state

            try:
                interactable_elements = await get_interactable_elements(page)

                # Get vision-guided action plan from Gemini
                ai_response = await ask_gemini_vision_for_actions(
                    screenshot_path=screenshot_path,
                    current_url=current_url,
                    goal=goal,
                    memory_context=memory_context,
                    creds=creds,
                    website_knowledge=website_knowledge,
                    demo_state=demo_state,
                    interactable_elements=interactable_elements
                )

                consecutive_failures = 0  # Reset on success

            except Exception as e:
                LOG.error(f"⚠️ Vision analysis error: {e}", exc_info=True) # Log traceback for vision errors
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    LOG.error("❌ Too many consecutive vision failures. Stopping demo flow.")
                    await async_speak_and_wait("I'm having trouble understanding the page right now. Let me stop here.",
                                                0.5, tts_lock, speaking_event, user_speaking_event)
                    break # Exit loop

                await async_speak_and_wait("Let me take another look.", 0.5, tts_lock, speaking_event, user_speaking_event)
                await asyncio.sleep(1.5)
                continue # Try next observation

            # Update memory
            memory_context += f"\n\nObs {observation_count}: State '{ai_response.get('page_state', 'unknown')}'. Planned {len(ai_response.get('actions', []))} actions."

            # Keep memory manageable
            if len(memory_context) > 2500:
                memory_context = memory_context[-2500:]
            if demo_state: demo_state["context"] = memory_context # Update state


            # Execute vision-guided actions
            # This block can now raise DemoInterruptedException
            result = await perform_action_sequence(
                page, ai_response, creds, pause_event, demo_state, tts_lock, speaking_event,
                silent=False, demo_interrupted_event=demo_interrupted_event, user_speaking_event=user_speaking_event
            )

            if result == "STOP":
                LOG.info(f"🏁 GOAL '{goal}' COMPLETE! Total observations: {observation_count}")
                # Don't speak here, let the calling function handle completion message
                break # Exit observation loop
            
            # Check for hard failure from autonomous flow
            if result == "FAILED":
                LOG.warning(f"⚠️ Autonomous action sequence failed (Observation {observation_count}).")
                consecutive_failures += 1
                # Don't break immediately, let the loop retry
            
            # If result was "PAGE_CHANGED" or "CONTINUE", the loop continues normally

            # Check if AI indicated no more observations needed (e.g., blocked)
            if not ai_response.get("next_observation_needed", True):
                LOG.warning("⚠️ AI indicated no further observations needed, but goal not complete. Stopping.")
                await async_speak_and_wait("It seems I'm stuck or finished unexpectedly. Stopping the current flow.", 0.5, tts_lock, speaking_event, user_speaking_event)
                break

            # Small delay between observations
            await check_pause(pause_event, demo_interrupted_event)
            await asyncio.sleep(0.5)

        # End of loop checks
        if observation_count >= max_observations:
            LOG.warning(f"⚠️ Reached max observations ({observation_count})")
            await check_pause(pause_event, demo_interrupted_event) # Check one last time
            await async_speak_and_wait("Reached the maximum steps for this task. Stopping here.", 0.5, tts_lock, speaking_event, user_speaking_event)

    except DemoInterruptedException:
        # This is caught by the run_demo_async which will handle restart/re-observation logic
        LOG.info("async_autonomous_web_flow_with_narration caught DemoInterruptedException. Exiting.")
        raise # Re-raise for the caller
    except asyncio.CancelledError:
        LOG.info("async_autonomous_web_flow_with_narration cancelled.")
        # Don't raise again, let the caller handle
    except Exception as e:
        LOG.error(f"❌ Critical error in autonomous flow: {e}", exc_info=True)
        await async_speak_and_wait("An unexpected error occurred during the demonstration.", 0.3, tts_lock, speaking_event, user_speaking_event)
        try:
            # Check page validity before screenshot
            if page and not page.is_closed():
                await page.screenshot(path=os.path.join(TEMP_DIR, "error_autonomous_flow.png"))
        except Exception as ss_e:
            LOG.error(f"Could not take error screenshot: {ss_e}")
        # Optionally re-raise or handle cleanup


# ---------------- SILENT PRE-CHECK FLOW ----------------
async def async_autonomous_web_flow(url, goal="login", headless=True, creds=None):
    """Silent pre-check with vision guidance"""
    LOG.info(f"🚀 Starting silent pre-check for {url} with goal '{goal}'")
    memory_context = ""

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            LOG.info(f"✅ Pre-check page loaded: {page.url}")
            await asyncio.sleep(1.0) # Allow page scripts to run

            for step in range(10): # Limit pre-check steps
                screenshot_path = os.path.join(TEMP_DIR, f"precheck_{step+1}.png")
                try:
                    await page.screenshot(path=screenshot_path, timeout=5000)
                except Exception as e:
                    LOG.error(f"❌ Pre-check screenshot failed: {e}")
                    return False # Abort pre-check if screenshot fails

                try:
                    interactable_elements = await get_interactable_elements(page)
                    ai_response = await ask_gemini_vision_for_actions(
                        screenshot_path, page.url, goal, memory_context, creds,
                        interactable_elements=interactable_elements
                    )
                except Exception as e:
                    LOG.warning(f"⚠️ Pre-check vision analysis error (Step {step+1}): {e}")
                    await asyncio.sleep(0.5) # Small delay before retry
                    continue # Try next step

                memory_context += f"\nPrecheck {step+1}: State '{ai_response.get('page_state', 'unknown')}', {len(ai_response.get('actions', []))} actions."
                memory_context = memory_context[-2000:] # Keep memory trimmed

                if not ai_response.get("actions"):
                    LOG.info(f"ℹ️ Pre-check (Step {step+1}): AI planned 0 actions. Checking goal status.")
                    # If goal is complete or blocked, check is done
                    if ai_response.get("goal_status") in ["complete", "blocked"]:
                        break
                    else:
                        # AI might be waiting for something, continue loop
                        await asyncio.sleep(0.5)
                        continue


                # Silent execution - no narration, no speaking events
                try:
                    result = await perform_action_sequence(
                        page, ai_response, creds, silent=True,
                        pause_event=None, demo_interrupted_event=None # No interruption in pre-check
                        )
                except Exception as exec_e:
                    LOG.error(f"❌ Pre-check action execution failed (Step {step+1}): {exec_e}")
                    return False # Abort if execution fails badly

                if result == "STOP" or ai_response.get("goal_status") == "complete":
                    LOG.info("✅ Pre-check successful: Goal marked as complete.")
                    return True
                
                # Check for failure in pre-check
                if result == "FAILED":
                    LOG.warning(f"⚠️ Pre-check action failed (Step {step+1}). Aborting.")
                    return False # Abort if any action fails

                # If result is PAGE_CHANGED or CONTINUE, we just continue the loop

                if not ai_response.get("next_observation_needed", True):
                    LOG.info(f"ℹ️ Pre-check (Step {step+1}): AI indicated no next observation needed.")
                    break # Exit loop if AI says so

                await asyncio.sleep(0.5) # Delay between steps

            # If loop finished without success
            LOG.warning(f"⚠️ Pre-check finished after {step+1} steps without reaching goal completion.")
            return False

        except Exception as e:
            LOG.error(f"❌ Pre-check failed critically: {e}", exc_info=True)
            return False
        finally:
            if browser:
                await browser.close()
            LOG.info("🏁 Pre-check finished.")