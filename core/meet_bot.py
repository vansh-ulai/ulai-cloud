import argparse
import asyncio
import logging
import os
import sys
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page as PlaywrightPage
import playwright
from urllib.parse import urlparse
import sounddevice as sd
from core.meet_creator import create_google_meet_link
from core.audio_manager import speak_text_virtual
from core.utils import safe_click
from core.login_demo import async_autonomous_web_flow_with_narration, async_autonomous_web_flow, DemoInterruptedException
from core.qa_handler import AIAgentOrchestrator, handle_user_question, handle_user_command

SILENCE_THRESHOLD_SECONDS = 1.4

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("meet_ai_log.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Global flags
demo_running = False
demo_paused = asyncio.Event()
demo_ready = asyncio.Event()
demo_interrupted = asyncio.Event()
stop_demo = False
demo_browser = None
demo_context = None
demo_page = None
demo_state = {
    "current_step": "",
    "context": "",
    "url": "",
    "website_name": "",
    "last_action": "",
    "page_description": ""
}
tts_lock = asyncio.Lock()
user_speaking = asyncio.Event()
last_user_speech_time = [0]
creds_global = None
orchestrator_global = None
current_demo_task = None

# --- Helper for timestamped screenshots ---
async def take_diagnostic_screenshot(page: PlaywrightPage, name: str):
    """Takes a screenshot with a timestamp for debugging."""
    if not page or page.is_closed():
        logging.warning(f"⚠️ Cannot take screenshot '{name}', page is closed.")
        return
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        screenshot_dir = "debug_screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(screenshot_dir, f"{timestamp}_{name}.png")
        await page.screenshot(path=path, timeout=5000)
        logging.info(f"📸 Saved diagnostic screenshot: {path}")
    except Exception as e:
        logging.error(f"❌ Failed to take diagnostic screenshot '{name}': {e}")

# ------------------ UTILITY FUNCTIONS ------------------ #
def normalize_url(url):
    """Ensure URL has proper protocol."""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def extract_website_name(url):
    """Extract clean website name from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace('www.', '')
        name = domain.split('.')[0]
        return name.capitalize()
    except:
        return "the website"

def get_first_name(full_name):
    """Extract first name from full name."""
    if not full_name:
        return "there"
    first = full_name.split()[0].strip()
    first = ''.join(c for c in first if c.isalnum())
    return first if first else "there"

def find_latest_screenshot() -> str:
    """Get the most recent screenshot from temp/ directory."""
    try:
        temp_dir = Path("temp")
        if not temp_dir.exists():
            return None
        screenshots = list(temp_dir.glob("obs_*.png"))
        if not screenshots:
            screenshots = list(temp_dir.glob("*.png"))
        if screenshots:
            latest = max(screenshots, key=lambda p: p.stat().st_mtime)
            logging.info(f"📸 Found latest screenshot: {latest.name}")
            return str(latest)
        return None
    except Exception as e:
        logging.warning(f"⚠️ Could not find screenshot: {e}")
        return None

async def take_fresh_screenshot(page: PlaywrightPage) -> str:
    """Takes a new screenshot with a unique name and returns the path."""
    try:
        if not page or page.is_closed():
            logging.warning("⚠️ Cannot take fresh screenshot, page is closed.")
            return find_latest_screenshot()
        timestamp = int(time.time() * 1000)
        os.makedirs("temp", exist_ok=True)
        screenshot_path = os.path.join("temp", f"obs_interrupt_{timestamp}.png")
        await page.screenshot(path=screenshot_path, timeout=4000)
        logging.info(f"📸 Took fresh screenshot: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"❌ Failed to take fresh screenshot: {e}")
        return find_latest_screenshot()

# ------------------ DIBRA PRELOAD ------------------ #
def preload_dibra_in_background():
    """Simulate Dibra module loading in background."""
    logging.info("🔄 [Background] Starting Dibra module preload...")
    def load_dibra():
        time.sleep(2.5)
        logging.info("✅ [Background] Dibra module ready")
    thread = threading.Thread(target=load_dibra, daemon=True)
    thread.start()
    return thread

# ------------------ DEMO BROWSER PRE-LAUNCH ------------------ #
async def prelaunch_demo_browser():
    """Pre-launch the demo browser with virtual screen support (headless Docker)."""
    global demo_browser, demo_context, demo_page
    logging.info("🚀 Pre-launching demo browser (virtual screen feed ready)...")
    try:
        from playwright.async_api import async_playwright

        playwright_instance = await async_playwright().start()

        browser = await playwright_instance.chromium.launch(
            headless=False,  # must be False so Google Meet detects the “screen” capture
            args=[
              "--start-maximized",
    "--no-sandbox",
    "--disable-infobars",
    "--enable-usermedia-screen-capturing",
    "--auto-select-desktop-capture-source=Entire screen",
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--window-size=1920,1080",
    "--use-gl=swiftshader",
    "--disable-gpu",
    "--allow-http-screen-capture",
    "--allow-file-access-from-files",
    "--enable-blink-features=GetDisplayMedia",
    "--use-file-for-fake-video-capture=/dev/video0",
    "--use-file-for-fake-audio-capture=/dev/null"
            ]
        )

        demo_context = await browser.new_context(viewport=None)
        demo_page = await demo_context.new_page()
        await demo_page.goto("about:blank")
        demo_browser = browser
        logging.info("✅ Demo browser ready with virtual screen support")

        # Diagnostic log
        try:
            devices = await demo_page.evaluate(
                "navigator.mediaDevices.enumerateDevices()"
            )
            logging.info(f"🎥 Available virtual devices: {devices}")
        except Exception as e:
            logging.warning(f"⚠️ Could not list media devices: {e}")

        return True

    except Exception as e:
        logging.error(f"❌ Demo browser pre-launch failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# ------------------ DEMO PREPARATION ------------------ #
async def prepare_demo_silently(url, creds):
    """Pre-check the demo flow in headless mode."""
    logging.info("🔧 [Background] Pre-checking demo flow silently...")
    try:
        success = await async_autonomous_web_flow(url, goal="login", headless=True, creds=creds)
        if success:
            logging.info("✅ Pre-check successful. Demo validated.")
            return True
        else:
            logging.warning("⚠️ Pre-check completed with issues, but will proceed.")
            return False
    except Exception as e:
        logging.warning(f"⚠️ Pre-check failed: {e}")
        return False

# ------------------ ASYNC DEMO RUNNER ------------------ #
async def run_demo_async(url, assistant_speaking_event=None, pause_event=None, demo_state=None, tts_lock=None, demo_interrupted_event=None, user_speaking_event=None):
    """Start the live demo with narration."""
    global demo_running, stop_demo, demo_page
    logging.info("🎬 Starting live demo with narration...")
    if demo_page is None or demo_page.is_closed():
        logging.error("❌ CRITICAL: demo_page is None or closed in run_demo_async!")
        if assistant_speaking_event: assistant_speaking_event.set()
        async with tts_lock: await asyncio.to_thread(speak_text_virtual, "Sorry, the demo page is not available. Please restart.")
        if assistant_speaking_event: assistant_speaking_event.clear()
        return
    demo_running = True
    pause_event.set()
    try:
        logging.info(f"🌐 Opening website: {url}")
        current_page_url = demo_page.url
        target_domain = urlparse(url).netloc
        current_domain = urlparse(current_page_url).netloc
        if target_domain != current_domain or current_page_url != url:
            logging.info(f"Navigating from {current_page_url} to {url}")
            await demo_page.goto(url, timeout=15000, wait_until="domcontentloaded")
        else:
            logging.info(f"✅ Already on the correct page/domain: {current_page_url}")
        await asyncio.sleep(1.0)
        logging.info(f"✅ Website ready at: {demo_page.url}")
        await async_autonomous_web_flow_with_narration(
            demo_page, goal="login", headless=False, creds=creds_global,
            pause_event=pause_event, demo_state=demo_state, tts_lock=tts_lock,
            speaking_event=assistant_speaking_event,
            website_knowledge=orchestrator_global.website_knowledge if orchestrator_global else None,
            demo_interrupted_event=demo_interrupted_event,
            user_speaking_event=user_speaking_event
        )
        if not stop_demo and demo_interrupted_event and demo_interrupted_event.is_set():
             logging.info("✅ Demo flow finished due to interruption signal.")
        elif not stop_demo:
            logging.info("✅ Autonomous demo flow completed.")
    except DemoInterruptedException:
        logging.info("🔄 Demo task interrupted by user command. Will re-observe.")
    except asyncio.CancelledError:
        logging.info("🔄 Demo task was cancelled externally.")
    except Exception as e:
        logging.exception(f"❌ Demo runner failed: {e}")
        if assistant_speaking_event: assistant_speaking_event.set()
        async with tts_lock: await asyncio.to_thread(speak_text_virtual, "Sorry, there was an issue during the demonstration.")
        await asyncio.sleep(0.8)
        if assistant_speaking_event: assistant_speaking_event.clear()
    finally:
        logging.info("🏁 Demo runner task finished.")
        demo_running = False
        demo_ready.set()

# ------------------ PARTICIPANT MONITOR ------------------ #
async def auto_admit_participants(page):
    """Continuously auto-admit users who request to join."""
    logging.info("🤖 Auto-admit loop started...")
    while True:
        try:
            buttons = await page.locator("button:has-text('Admit')").all()
            for btn in buttons:
                try:
                    await btn.click(timeout=1000)
                    logging.info("✅ Auto-admitted a participant.")
                except Exception: pass
        except Exception as e:
            logging.debug(f"Auto-admit check error: {e}")
        await asyncio.sleep(2)

async def monitor_participants(meet_page):
    """Continuously monitor for participants joining."""
    logging.info("👥 Monitoring for participants...")
    try:
        await safe_click(meet_page, ['button[aria-label*="Show everyone"]', 'button[aria-label*="People"]', 'button[aria-label*="Participants"]'])
        logging.info("✅ Participant panel opened.")
        await asyncio.sleep(1.5)
    except Exception as e:
        logging.warning(f"⚠️ Could not open participant panel: {e}")
    all_participants = set()
    check_count = 0
    while True:
        try:
            participant_elements_text = []
            try:
                elements = await meet_page.locator('div[role="listitem"]').all()
                for elem in elements:
                    try:
                        text = await elem.inner_text(timeout=500)
                        if text and text.strip(): participant_elements_text.append(text.strip())
                    except Exception: pass
            except Exception as e: logging.debug(f"⚠️ Error getting listitems: {e}")
            try:
                elements = await meet_page.locator('[data-participant-id]').all()
                for elem in elements:
                    try:
                        name_span = elem.locator('span').first
                        if await name_span.is_visible(timeout=500):
                            text = await name_span.inner_text(timeout=500)
                            if text and text.strip(): participant_elements_text.append(text.strip())
                    except Exception: pass
            except Exception as e: logging.debug(f"⚠️ Error getting data-participant-id: {e}")
            clean_names = set()
            for name_block in participant_elements_text:
                lines = name_block.split('\n')
                potential_name = lines[0].strip()
                name_lower = potential_name.lower()
                skip_words = ['you', 'host', 'presenting', 'mute', 'unmute', 'camera', 'raise', 'hand', 'more', 'options', 'menu', 'in call']
                if not potential_name or len(potential_name) < 3 or len(potential_name) > 50 or any(skip in name_lower for skip in skip_words) or potential_name.isdigit():
                    continue
                clean_names.add(potential_name)
            if clean_names:
                new_participants = clean_names - all_participants
                if new_participants:
                    logging.info(f"👥 New participants detected: {', '.join(new_participants)}")
                    all_participants.update(clean_names)
                    logging.info(f"👥 Current participants: {', '.join(all_participants)}")
                real_participants = [name for name in all_participants if 'you' not in name.lower()]
                if real_participants:
                    participant_name = real_participants[0]
                    logging.info(f"✅ Detected participant: {participant_name}")
                    return participant_name
            check_count += 1
            if check_count % 10 == 0: logging.info(f"👀 Still waiting for participants... ({check_count * 2}s elapsed)")
        except Exception as e:
            logging.warning(f"⚠️ Error checking participants: {e}")
        await asyncio.sleep(2)

# ------------------ MEET AGENT ------------------ #
async def run_meet_agent(meet_url: str, url: str, creds: tuple, headful: bool = True):
    """Main Meet agent with Multi-AI orchestration."""
    global demo_state, tts_lock, user_speaking, last_user_speech_time, creds_global, orchestrator_global, demo_page, demo_interrupted, current_demo_task

    meet_url = normalize_url(meet_url)
    url = normalize_url(url)
    creds_global = creds
    website_name = extract_website_name(url)
    demo_state["url"] = url
    demo_state["website_name"] = website_name

    # PHASE 1: Background preparation
    logging.info("🔄 Phase 1: Starting background preparations...")
    try:
        logging.info("=== Available Audio Devices (from Python) ===")
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            dtype = "INPUT" if d.get('max_input_channels', 0) > 0 else "OUTPUT"
            logging.info(f"   [{i}] {d['name']} ({dtype})")
        logging.info("============================================")
    except Exception as e:
        logging.error(f"❌ Failed to query audio devices at start: {e}")
    
    dibra_thread = preload_dibra_in_background()
    demo_browser_ready = await prelaunch_demo_browser()
    if not demo_browser_ready: return
    if demo_page is None: 
        logging.error("❌ CRITICAL: demo_page is still None after pre-launch!")
        return
    
    logging.info(f"✅ Demo page validated (blank page ready)")
    logging.info("✅ Skipping silent demo pre-check as requested.")
    logging.info("🎤 [Background] Pre-starting Deepgram STT worker...")
    
    stt_queue = asyncio.Queue()
    assistant_speaking = asyncio.Event()
    stt_task = None
    try:
        from core.stt_deepgram import start_stt_listener
        # We tell STT to listen to the *monitor* of the Meet Output sink
        stt_task = await start_stt_listener(out_queue=stt_queue, speaking_event=assistant_speaking, device_name_hint="Meet_Output.monitor")
        logging.info("✅ [Background] Deepgram STT worker pre-started and ready")
    except Exception as e:
        logging.warning(f"⚠️ STT pre-start failed (will continue without it): {e}")
    
    logging.info(f"🎯 Target: {website_name}")

    async with async_playwright() as p:
        # PHASE 2: Join Meet
        logging.info("🌐 Phase 2: Joining Google Meet...")
        context = None
        try:
            # Build environment dict with PulseAudio vars
            pulse_env = {
                "DISPLAY": os.getenv("DISPLAY", ":99"),
                "PULSE_SERVER": os.getenv("PULSE_SERVER", "unix:/tmp/pulse/native"),
                "XDG_RUNTIME_DIR": os.getenv("XDG_RUNTIME_DIR", "/tmp/pulse"),
            }

            # ========================= FIX START =========================
            # Ensure the PULSE_COOKIE path is absolute and expanded
            pulse_cookie_path_str = os.getenv("PULSE_COOKIE")
            
            if pulse_cookie_path_str:
                expanded_cookie_path = os.path.expanduser(pulse_cookie_path_str)
                if os.path.exists(expanded_cookie_path):
                    # Pass the *absolute, expanded* path to Chromium
                    pulse_env["PULSE_COOKIE"] = expanded_cookie_path
                    logging.info(f"✅ Using PulseAudio cookie: {expanded_cookie_path}")
                else:
                    logging.warning(f"⚠️ PULSE_COOKIE file not found at: {expanded_cookie_path}")
            else:
                logging.warning("⚠️ PULSE_COOKIE env var not set")
            # ========================== FIX END ==========================

            logging.info(f"🔧 Launching Chromium with PulseAudio environment")
            logging.info(f"   PULSE_SERVER: {pulse_env['PULSE_SERVER']}")
            logging.info(f"   XDG_RUNTIME_DIR: {pulse_env['XDG_RUNTIME_DIR']}")

            

            context = await p.chromium.launch_persistent_context(
                user_data_dir="meet_profile",
                headless=not headful,
                args=[
                    "--start-maximized",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--auto-select-desktop-capture-source=Entire screen",
                    "--enable-usermedia-screen-capturing",
                    "--use-file-for-fake-video-capture=/tmp/video_stream/live_screen.y4m",
                    "--disable-extensions",
                    # PulseAudio specific
                    "--use-pulseaudio",
                    "--enable-features=AudioServiceOutOfProcess",
                    # WebRTC
                    "--alsa-input-device=pulse",
                    "--alsa-output-device=pulse",
                    "--enable-features=WebRTCPipeWireCapturer,AudioServiceSandbox",
                    "--use-fake-ui-for-media-stream"
                    # "--use-fake-device-for-media-stream"

                ],
                permissions=['microphone', 'camera'],
                env=pulse_env
            )

            logging.info("✅ Chromium context created")

            

            # Grant permissions BEFORE navigating
            logging.info("🔐 Granting microphone permission to Meet...")
            try:
                await context.grant_permissions(['microphone','camera'], origin="https://meet.google.com")
                logging.info("✅ Microphone permission granted")
            except Exception as e:
                logging.error(f"❌ Failed to grant permissions: {e}")
            meet_page = await context.new_page()

            # Navigate to Meet
            devices = await context.new_cdp_session(meet_page)

            logging.info(f"🌐 Navigating to: {meet_url}")
            await meet_page.goto(meet_url, wait_until="domcontentloaded", timeout=60000)
            await meet_page.wait_for_load_state("networkidle")

# Now test mediaDevices AFTER page load
            mic_info = await meet_page.evaluate("async()=>{for(let i=0;i<15;i++){if(window.navigator&&navigator.mediaDevices&&navigator.mediaDevices.enumerateDevices)break;await new Promise(r=>setTimeout(r,700));}if(!navigator.mediaDevices)return{error:'navigator.mediaDevices still undefined after full page load'};try{const d=await navigator.mediaDevices.enumerateDevices();return d.map(x=>({kind:x.kind,label:x.label,deviceId:x.deviceId}));}catch(e){return{error:e.message}}}")
            logging.info(f'🎧 Chromium devices (after navigation): {mic_info}')

            logging.info(f"✅ Page loaded successfully")
            await take_diagnostic_screenshot(meet_page, "01_after_navigate")

            # Verify browser can enumerate devices (non-invasive check)
            try:
                device_list = await meet_page.evaluate('''
                    async () => {
                        const devices = await navigator.mediaDevices.enumerateDevices();
                        return devices.map(d => ({kind: d.kind, label: d.label}));
                    }
                ''')
                audio_inputs = [d for d in device_list if d['kind'] == 'audioinput']
                audio_outputs = [d for d in device_list if d['kind'] == 'audiooutput']
                logging.info(f"🎤 Browser sees {len(audio_inputs)} audio input(s)")
                logging.info(f"🔊 Browser sees {len(audio_outputs)} audio output(s)")
                
                if len(audio_inputs) == 0:
                    logging.error("❌ CRITICAL: Browser sees NO audio inputs! Meet lobby will fail.")
                    logging.error("   This means Chromium cannot connect to PulseAudio.")
                    logging.error("   Check that PULSE_SERVER, PULSE_COOKIE are correct.")
                else:
                    logging.info("✅ Audio devices detected, lobby should load")
                    for d in audio_inputs: logging.info(f"   [Input] {d['label']}")
                    for d in audio_outputs: logging.info(f"   [Output] {d['label']}")
            except Exception as e:
                logging.error(f"❌ Could not enumerate devices: {e}")

            # Robust lobby waiting
            try:
                try:
                    await meet_page.wait_for_url("**/accounts.google.com/**", timeout=5000)
                    logging.error("❌ Redirected to Google Accounts page - LOGIN FAILED!")
                    await take_diagnostic_screenshot(meet_page, "error_redirected_to_login")
                    if context: await context.close()
                    return
                except playwright._impl._errors.TimeoutError:
                    logging.info("✅ Not redirected to login page (Login successful).")
                    pass
                
                # Wait for lobby OR error
                logging.info("⏳ Waiting for Meet lobby or join button...")

                # === NEW ROBUST JOIN SECTION (copied from working code) ===
                logging.info("🎯 Attempting to join the meeting...")
                # Try to toggle mic/cam like in working flow (helps UI render)
                await safe_click(meet_page, ['div[aria-label*="Turn off camera"]'])
                await safe_click(meet_page, ['div[aria-label*="Turn off microphone"]'])
                await asyncio.sleep(1.0)
                await safe_click(meet_page, ['div[aria-label*="Turn on camera"]'])
                await safe_click(meet_page, ['div[aria-label*="Turn on microphone"]'])
                await asyncio.sleep(0.8)
                # Try to click Join or Ask to join
                joined = await safe_click(
                    meet_page,
                    ['button:has-text("Join now")', 'button:has-text("Ask to join")'],
                    retries=12,
                    delay=2
                )
                if joined:
                    logging.info("✅ Joined Meet successfully.")
                    asyncio.create_task(auto_admit_participants(meet_page))

                else:
                    logging.error("❌ Could not join Meet (Join button not clickable after retries).")
                    await take_diagnostic_screenshot(meet_page, "error_join_failed")
                    raise Exception("Join button not found or not clickable.")
                # === END PATCH ===
            except Exception as e:
                logging.error(f"❌ Failed during lobby/join phase: {e}")
                await take_diagnostic_screenshot(meet_page, "error_lobby_join_phase")
                if context:
                    await context.close()
                return

            asyncio.create_task(auto_admit_participants(meet_page))
            logging.info("🧠 Auto-admit task started.")

            # PHASE 3: Wait for participant
            assistant_speaking.set()
            async with tts_lock:
                await asyncio.to_thread(speak_text_virtual, "I'm ready and waiting for participants to join the demonstration.")
            await asyncio.sleep(0.8)
            assistant_speaking.clear()
            
            logging.info("👥 Phase 3: Waiting for participant...")
            participant_full_name = await monitor_participants(meet_page)
            participant_first_name = get_first_name(participant_full_name)

            # PHASE 4: Greet participant
            logging.info(f"🎤 Phase 4: Greeting {participant_first_name}...")
            greeting = f"Hello {participant_first_name}! Welcome to the demonstration. Today I'll be showing you how to use {website_name}."
            assistant_speaking.set()
            async with tts_lock:
                await asyncio.to_thread(speak_text_virtual, greeting)
            await asyncio.sleep(2.5)
            assistant_speaking.clear()

            # PHASE 5: Share screen
            logging.info("📺 Phase 5: Sharing screen...")
            assistant_speaking.set()
            async with tts_lock:
                await asyncio.to_thread(speak_text_virtual, "Let me share my screen with you.")
            await asyncio.sleep(1.5)
            assistant_speaking.clear()
            
            await safe_click(meet_page, ['button:has-text("Present now")','button[aria-label*="Present now"]','button[aria-label*="Share screen"]'])
            await asyncio.sleep(1.5)
            await take_diagnostic_screenshot(meet_page, "06_after_present_click")
            
            try:
                shared = await safe_click(meet_page, ['button:has-text("Share")','button:has-text("Share this tab")','button[aria-label*="Share"]'], retries=3, delay=1)
                if shared: logging.info("✅ Screen sharing started.")
                try:
                   await meet_page.wait_for_selector('div[aria-label*="Stop presenting"]', timeout=10000)
                   logging.info("✅ Verified: Screen sharing successfully active (Stop presenting visible).")
                   await meet_page.screenshot(path="debug_screenshots/verify_share_success.png")
                except Exception as e:
                     logging.error(f"❌ Screen share verification failed: {e}")
                     await meet_page.screenshot(path="debug_screenshots/verify_share_failed.png")
                else: logging.warning("⚠️ Could not confirm share button click")
            except Exception as e: 
                logging.warning(f"⚠️ Share click failed: {e}")
            
            await take_diagnostic_screenshot(meet_page, "07_after_share_attempt")
            await asyncio.sleep(1.5)

            # PHASE 5.5: Initialize AI Orchestrator
            logging.info("🧠 Phase 5.5: Initializing Multi-AI Orchestrator...")
            orchestrator_global = AIAgentOrchestrator(demo_state=demo_state, demo_page=demo_page, creds=creds_global)
            initial_screenshot = find_latest_screenshot()
            
            if initial_screenshot:
                assistant_speaking.set()
                async with tts_lock:
                    await asyncio.to_thread(speak_text_virtual, "Analyzing the website to understand it better.")
                await asyncio.sleep(0.8)
                assistant_speaking.clear()
                
                website_knowledge = await orchestrator_global.initialize_website_knowledge(url, initial_screenshot)
                logging.info("✅ AI Orchestrator initialized with website knowledge" if website_knowledge else "⚠️ AI Orchestrator: Could not initialize website knowledge")
            else: 
                logging.warning("⚠️ No screenshot available for initial analysis - AI will learn as we go")

            # PHASE 6: Start live demo
            logging.info("🎬 Phase 6: Starting live demonstration...")
            assistant_speaking.set()
            async with tts_lock:
                await asyncio.to_thread(speak_text_virtual, f"Now I'll demonstrate the login process on {website_name}. Feel free to ask any questions or give commands during the demo, like 'click this button' or 'go back', and I'll pause to handle it.")
            await asyncio.sleep(1.5)
            assistant_speaking.clear()
            
            if demo_context:
                try:
                    if demo_page and not demo_page.is_closed(): 
                        await demo_page.bring_to_front()
                    elif demo_context.pages: 
                        demo_page = demo_context.pages[0]
                        await demo_page.bring_to_front()
                    logging.info("✅ Demo browser focused and ready")
                except Exception as e: 
                    logging.warning(f"⚠️ Could not bring demo browser to front: {e}")
            
            await asyncio.sleep(1)
            current_demo_task = asyncio.create_task(run_demo_async(url, assistant_speaking, demo_paused, demo_state, tts_lock, demo_interrupted, user_speaking))

            # PHASE 7: Interactive Q&A
            logging.info("🎧 Phase 7: Multi-AI interactive handler active...")
            if not stt_task:
                 logging.warning("⚠️ STT not available, continuing without interactive Q&A")
                 await current_demo_task
                 assistant_speaking.set()
                 async with tts_lock:
                     await asyncio.to_thread(speak_text_virtual, "Thank you for watching the demonstration.")
                 await asyncio.sleep(2)
                 assistant_speaking.clear()
                 if context: await context.close()
                 logging.info("🛑 Meet session ended.")
                 return

            # --- speak_and_log function ---
            async def speak_and_log(text: str):
                if user_speaking.is_set(): 
                    logging.info("🤫 User is speaking, skipping AI speech.")
                    return
                logging.info(f"🤖 AI: {text}")
                assistant_speaking.set()
                await asyncio.sleep(0.05)
                try:
                    await asyncio.wait_for(tts_lock.acquire(), timeout=5.0)
                    try:
                        if user_speaking.is_set(): 
                            logging.info("🤫 User started speaking during lock, cancelling AI speech.")
                            return
                        await asyncio.to_thread(speak_text_virtual, text)
                    finally: 
                        tts_lock.release()
                    word_count = len(text.split())
                    estimated_duration = (word_count / 3.0)
                    wait_time = max(estimated_duration, 0.6)
                    start_wait = time.time()
                    while time.time() - start_wait < wait_time:
                        if user_speaking.is_set(): 
                            logging.info("🤫 User started speaking, cutting AI wait short.")
                            break
                        await asyncio.sleep(0.1)
                except asyncio.TimeoutError: 
                    logging.error("❌ Timed out waiting for TTS lock in speak_and_log.")
                except Exception as e: 
                    logging.error(f"❌ Error in speak_and_log TTS: {e}")
                finally: 
                    await asyncio.sleep(0.1)
                    assistant_speaking.clear()

            # --- handle_stt function ---
            async def handle_stt():
                global stop_demo, demo_state, demo_page, creds_global, orchestrator_global, demo_interrupted, current_demo_task, demo_running
                logging.info("🎧 STT handler started with Multi-AI orchestration...")
                accumulated_text = ""
                last_fragment_time = time.time()
                command_keywords = ["click", "go back", "back", "fill", "type", "enter", "navigate", "go to", "button", "press", "select", "open", "close", "scroll", "find", "search", "previous"]
                
                while not stop_demo:
                    try:
                        if current_demo_task and current_demo_task.done():
                            logging.info("🏁 Demo task finished processing.")
                            try: 
                                current_demo_task.result()
                            except asyncio.CancelledError: 
                                logging.info("✅ Demo task was cancelled.")
                            except DemoInterruptedException: 
                                logging.info("✅ Demo task was interrupted as expected.")
                            except Exception as e: 
                                logging.error(f"❌ Demo task failed with exception: {e}")
                            current_demo_task = None
                            demo_running = False
                            if not demo_interrupted.is_set(): 
                                logging.info("Demo finished naturally, STT loop will exit soon.")
                                await asyncio.sleep(5)
                                break
                        
                        try:
                            fragment = await asyncio.wait_for(stt_queue.get(), timeout=0.5)
                            stt_queue.task_done()
                            if not fragment: continue
                            accumulated_text += " " + fragment
                            last_fragment_time = time.time()
                            if not user_speaking.is_set(): 
                                logging.info("🗣️ User started speaking.")
                                user_speaking.set()
                            logging.debug(f"👂 [FRAGMENT] {fragment}")
                        except asyncio.TimeoutError:
                            current_time = time.time()
                            silence_duration = current_time - last_fragment_time
                            if user_speaking.is_set() and silence_duration > SILENCE_THRESHOLD_SECONDS:
                                logging.info(f"🗣️ User stopped speaking (silence: {silence_duration:.2f}s).")
                                user_speaking.clear()
                                text = accumulated_text.strip().lower()
                                accumulated_text = ""
                                if not text or len(text.split()) < 2: 
                                    logging.info(f"⏩ Ignoring short utterance: '{text}'")
                                    continue
                                logging.info(f"👂 [USER COMPLETE] {text}")
                                
                                question_words = ["what", "why", "how", "explain", "tell", "can you", "could you", "would", "is this", "are you", "do you", "does", "is", "where", "when", "who", "which"]
                                is_question = any(word in text for word in question_words) or "?" in text
                                is_command = any(kw in text for kw in command_keywords)
                                is_resume = "resume" in text
                                should_handle = (is_question or is_command) and (demo_running or (demo_page and not demo_page.is_closed()))
                                
                                if should_handle:
                                    logging.info("⏸️ ========== PAUSING DEMO FOR INPUT ==========")
                                    demo_paused.clear()
                                    demo_interrupted.clear()
                                    if current_demo_task and not current_demo_task.done():
                                        logging.info("Cancelling current demo task...")
                                        current_demo_task.cancel()
                                        try: 
                                            await current_demo_task
                                        except asyncio.CancelledError: 
                                            logging.info("✅ Demo task cancellation confirmed.")
                                        except DemoInterruptedException: 
                                            logging.info("✅ Demo task cancellation (interrupted) confirmed.")
                                        current_demo_task = None
                                        demo_running = False
                                    await asyncio.sleep(0.5)
                                    screenshot_path = await take_fresh_screenshot(demo_page)
                                    if not screenshot_path: 
                                        logging.error("❌ Cannot proceed, failed to get screenshot.")
                                        await speak_and_log("Sorry, I can't see the screen.")
                                        continue
                                    
                                    if is_command:
                                        logging.info(f"🎯 Routing to Action Agent: {text}")
                                        async def get_action_plan():
                                            if not demo_page or demo_page.is_closed(): 
                                                return {"error": "Demo page not available"}
                                            logging.info(f"🎯 Action Agent processing command: {text}")
                                            return await handle_user_command(text, orchestrator_global, screenshot_path)
                                        
                                        ai_task = asyncio.create_task(get_action_plan())
                                        tts_task = asyncio.create_task(speak_and_log("Understood, let me do that."))
                                        action_plan = await ai_task
                                        await tts_task
                                        
                                        if "error" in action_plan and action_plan["error"] == "Demo page not available": 
                                            logging.error("Action Agent error: Demo page not available.")
                                            demo_paused.set()
                                            continue
                                        
                                        try:
                                            if "error" in action_plan: 
                                                logging.error(f"❌ Action planning failed: {action_plan['error']}")
                                                await speak_and_log("I'm having trouble with that command.")
                                            elif not action_plan.get("actions"): 
                                                logging.info("⚠️ Action Agent returned 0 actions.")
                                                await speak_and_log("I can't do that from here.")
                                            else:
                                                logging.info(f"📋 Action Plan: Understood={action_plan.get('understood_command')}, Confidence={action_plan.get('confidence')}")
                                                from core.login_demo import perform_action_sequence, DemoInterruptedException
                                                result = await perform_action_sequence(
                                                    demo_page, action_plan, creds_global, 
                                                    pause_event=None, demo_state=demo_state, 
                                                    tts_lock=tts_lock, speaking_event=assistant_speaking, 
                                                    silent=False, demo_interrupted_event=demo_interrupted, 
                                                    user_speaking_event=user_speaking
                                                )
                                                if isinstance(result, PlaywrightPage):
                                                    logging.info(f"🔄 Swapping to new page: {result.url}")
                                                    demo_page = result
                                                    orchestrator_global.demo_page = demo_page
                                                    globals()['demo_page'] = demo_page
                                                    await demo_page.bring_to_front()
                                                    await speak_and_log("Okay, moved to the new page.")
                                                    demo_paused.clear()
                                                else:
                                                    is_interrupting = any(a.get("action") in ["back", "navigate"] for a in action_plan.get("actions",[]))
                                                    if is_interrupting: 
                                                        logging.info("🔄 User command caused navigation.")
                                                        demo_interrupted.set()
                                                    else:
                                                        if result == "CONTINUE": 
                                                            await speak_and_log("Done! Say 'resume' when ready.")
                                                        elif result == "STOP": 
                                                            await speak_and_log("Task completed.")
                                        except DemoInterruptedException as nav_e: 
                                            logging.info(f"✅ User command action caused interruption: {nav_e}")
                                            await speak_and_log("Okay, done. Say 'resume' when ready.")
                                        except Exception as e: 
                                            logging.error(f"⚠️ Command execution error: {e}", exc_info=True)
                                            await speak_and_log("Issue with that command.")
                                    
                                    elif is_question:
                                        logging.info(f"🤔 Routing to Q&A Agent: {text}")
                                        try:
                                            answer = await handle_user_question(text, orchestrator_global, screenshot_path)
                                            if answer and len(answer) > 10: 
                                                await speak_and_log(answer)
                                                await asyncio.sleep(0.4)
                                                await speak_and_log("Let me know when to resume.")
                                            else: 
                                                await speak_and_log("Good question. Let me know when to resume.")
                                            logging.info("▶️ Waiting for resume command (after Q&A)")
                                            demo_paused.clear()
                                        except Exception as e: 
                                            logging.error(f"⚠️ Q&A error: {e}", exc_info=True)
                                            await speak_and_log("Interesting. Let me know when to resume.")
                                            logging.info("▶️ Waiting for resume (after Q&A error)")
                                            demo_paused.clear()
                                
                                elif is_resume:
                                    logging.info("▶️ ========== RESUMING DEMO (User Request) ==========")
                                    if demo_running: 
                                        logging.info("...Demo running, unpausing.")
                                        await speak_and_log("Resuming.")
                                        demo_paused.set()
                                    else:
                                        await speak_and_log("Resuming the demonstration.")
                                        demo_paused.set()
                                        if not current_demo_task or current_demo_task.done():
                                            logging.info("Restarting demo task...")
                                            current_demo_task = asyncio.create_task(run_demo_async(url, assistant_speaking, demo_paused, demo_state, tts_lock, demo_interrupted, user_speaking))
                                        else: 
                                            logging.info("...Demo task found, setting pause event.")
                                
                                elif "stop demo" in text or "end demo" in text:
                                    stop_demo = True
                                    demo_paused.set()
                                    if current_demo_task and not current_demo_task.done(): 
                                        current_demo_task.cancel()
                                    await speak_and_log("Stopping demo.")
                                    break
                                elif "thank" in text: 
                                    await speak_and_log("You're welcome!")
                                elif "bye" in text or "goodbye" in text:
                                    stop_demo = True
                                    demo_paused.set()
                                    if current_demo_task and not current_demo_task.done(): 
                                        current_demo_task.cancel()
                                    await speak_and_log("Goodbye!")
                                    break
                    except Exception as e:
                        logging.warning(f"⚠️ STT handler main loop error: {e}")
                        await asyncio.sleep(0.1)
                
                logging.info("🛑 STT handler stopped.")

            try:
                await handle_stt()
            except Exception as e:
                logging.exception(f"Error in STT handler: {e}")

            # Wait for any remaining demo task
            logging.info("⏳ Waiting for any remaining demo task completion...")
            if current_demo_task and not current_demo_task.done():
                try: 
                    await current_demo_task
                except asyncio.CancelledError: 
                    logging.info("✅ Final demo task cancelled.")
                except DemoInterruptedException: 
                    logging.info("✅ Final demo task interrupted.")
                except Exception as e: 
                    logging.error(f"❌ Final demo task failed: {e}")

            # Final message
            if not stop_demo:
                assistant_speaking.set()
                async with tts_lock: 
                    await asyncio.to_thread(speak_text_virtual, "Thank you for watching the demonstration. Any final questions?")
                await asyncio.sleep(3)
                assistant_speaking.clear()

        finally:
            logging.info("🧹 Cleaning up resources...")
            try:
                if meet_page and not meet_page.is_closed(): 
                    await meet_page.close()
            except Exception as e: 
                logging.warning(f"⚠️ Error closing meet_page: {e}")
            try:
                if context and context.browser and context.browser.is_connected(): 
                    await context.close()
            except Exception as e: 
                logging.warning(f"⚠️ Error closing meet context: {e}")
            try:
                if demo_page and not demo_page.is_closed(): 
                    await demo_page.close()
            except Exception as e: 
                logging.warning(f"⚠️ Error closing demo_page: {e}")
            try:
                if demo_context and demo_context.browser and demo_context.browser.is_connected(): 
                    await demo_context.close()
            except Exception as e: 
                logging.warning(f"⚠️ Error closing demo context: {e}")
            try:
                if demo_browser and demo_browser.is_connected(): 
                    await demo_browser.close()
            except Exception as e: 
                logging.warning(f"⚠️ Error closing demo browser: {e}")
            logging.info("🛑 Meet session ended.")


# ------------------ MAIN ENTRY ------------------ #
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Meet Demo Agent")
    parser.add_argument("--meet-url", required=False, help="Google Meet URL")
    parser.add_argument("--headful", action="store_true", help="Run headful")
    args = parser.parse_args()

    print("\n" + "="*70 + "\n" + "🤖 AI MEET DEMO AGENT".center(70) + "\n" + "="*70 + "\n")

    demo_url = os.getenv("DEMO_URL")
    demo_email = os.getenv("DEMO_EMAIL")
    demo_password = os.getenv("DEMO_PASSWORD")
    if demo_url and demo_email and demo_password:
        print("✅ Loaded from launcher")
        site_url = demo_url
        email = demo_email
        password = demo_password
    else:
        print("📋 Enter website details:")
        site_url = input("Website URL: ").strip()
        email = input("Email/Username: ").strip()
        password = input("Password: ").strip()
    creds = (email, password)

    print("\n✅ Configuration complete!")
    print(f"🎯 Target: {site_url}")
    print(f"👤 Username: {email}")
    
    if args.meet_url: 
        meet_link = args.meet_url
    else:
        print("🌐 No Meet link provided — creating a new one automatically...")
        meet_link = create_google_meet_link()
        if not meet_link: 
            print("❌ Failed to create Google Meet link. Exiting.")
            sys.exit(1)
    
    print(f"🔗 Meet: {meet_link}")
    print("\nStarting agent...\n")
    
    try:
        asyncio.run(run_meet_agent(meet_link, site_url, creds, headful=args.headful))
    except KeyboardInterrupt:
        logging.info("\n🛑 User interrupted. Shutting down gracefully.")
        print("\n👋 Goodbye!")
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
    finally:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-f", "chromium.*--user-data-dir=meet_profile"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["pkill", "-f", "chromium.*--user-data-dir=/app/meet_profile"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("🧹 Attempted final browser process cleanup.")
        except Exception as cleanup_e:
            logging.warning(f"⚠️ Error during final browser cleanup: {cleanup_e}")