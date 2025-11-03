import os
import asyncio
import logging
import json
import re
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

LOG = logging.getLogger(__name__)

# ==================== AI AGENT ORCHESTRATOR ====================

class AIAgentOrchestrator:
    """
    Orchestrates multiple AI agents working as a team:
    1. Context Agent - Understands website deeply
    2. Q&A Agent - Answers questions with full context
    3. Action Agent - Executes commands based on vision
    """

    def __init__(self, demo_state: dict, demo_page=None, creds: tuple = None):
        self.demo_state = demo_state
        self.demo_page = demo_page
        self.creds = creds
        self.website_knowledge = None  # Deep website understanding
        self.conversation_memory = []  # Remember Q&A history

    async def initialize_website_knowledge(self, url: str, screenshot_path: str = None):
        """
        Context Agent: Build deep understanding of the website ONCE
        This runs at the start and creates a comprehensive knowledge base
        """
        LOG.info("🧠 Context Agent: Analyzing website comprehensively...")

        if not screenshot_path or not os.path.exists(screenshot_path):
            LOG.warning("⚠️ No screenshot for deep analysis")
            return None

        try:
            img = Image.open(screenshot_path)
            model = genai.GenerativeModel('gemini-2.5-flash')

            prompt = f"""You are a Context Analysis Agent. Your job is to deeply understand this website.

Website URL: {url}

Analyze EVERYTHING you see in this screenshot and provide a COMPREHENSIVE knowledge base:

1. IDENTITY & PURPOSE
   - Official website name (exact)
   - Primary purpose (what problem does it solve?)
   - Industry/category
   - Target audience

2. VISUAL DESIGN & BRANDING
   - Color scheme
   - Logo and branding elements
   - UI/UX style (modern, minimal, corporate, etc.)
   - Key visual elements

3. FEATURES & CAPABILITIES (be SPECIFIC based on what you SEE)
   - Main features visible
   - User workflows you can identify
   - Types of content/data it manages
   - Integration capabilities (if visible)

4. PAGE STRUCTURE
   - Current page type (login, dashboard, etc.)
   - Visible UI elements (buttons, forms, navigation)
   - Expected user flow from this page

5. TECHNICAL NOTES
   - Authentication method (if visible)
   - Form structure
   - Any special UI patterns

Provide a detailed JSON response with ALL this information. Be SPECIFIC - don't use generic terms!

{{
  "name": "Exact website name",
  "tagline": "Their tagline/slogan if visible",
  "purpose": "Detailed purpose",
  "category": "Specific category",
  "target_users": "Who uses this",
  "color_scheme": "Primary colors",
  "design_style": "Design aesthetic",
  "main_features": ["Feature 1", "Feature 2", "Feature 3"],
  "visible_ui_elements": ["Element 1", "Element 2"],
  "current_page_type": "Page type",
  "authentication": "Auth method details",
  "user_workflow": "Expected flow from here",
  "special_notes": "Any unique observations"
}}"""

            response = await asyncio.to_thread(
                model.generate_content,
                [prompt, img],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=2048
                )
            )

            # --- SAFETY CHECK ---
            if not response.parts:
                finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"
                LOG.error(f"❌ Context Agent error: Gemini response blocked. Finish reason: {finish_reason}")
                return None

            # Parse JSON response
            text = response.text.strip()
            # Try to find JSON block, be more lenient
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL) # Look for markdown block first
            if not match:
                 match = re.search(r'(\{.*?\})', text, re.DOTALL) # Fallback to any JSON block

            if match:
                try:
                    json_str = match.group(1)
                    knowledge = json.loads(json_str)
                    self.website_knowledge = knowledge
                    LOG.info(f"✅ Context Agent: Learned about {knowledge.get('name', 'website')}")
                    LOG.info(f"   Purpose: {knowledge.get('purpose', 'N/A')[:100]}")
                    LOG.info(f"   Features: {', '.join(knowledge.get('main_features', [])[:3])}")
                    return knowledge
                except json.JSONDecodeError as json_e:
                    LOG.error(f"⚠️ Context Agent: Failed to decode JSON - {json_e}")
                    LOG.debug(f"Invalid JSON string: {json_str}")
                    return None
            else:
                LOG.warning(f"⚠️ Could not parse context analysis JSON from response: {text[:200]}...")
                return None

        except Exception as e:
            LOG.error(f"❌ Context Agent failed: {e}", exc_info=True)
            return None

    async def answer_question(self, question: str, screenshot_path: str = None) -> str:
        """
        Q&A Agent: Answer questions with FULL context (visual + knowledge base + demo state)
        """
        LOG.info(f"🤔 Q&A Agent processing: {question}")

        try:
            # Build comprehensive context package
            context_package = self._build_context_package()

            # Use vision if screenshot available
            if screenshot_path and os.path.exists(screenshot_path):
                return await self._answer_with_full_vision(question, context_package, screenshot_path)
            else:
                return await self._answer_with_knowledge(question, context_package)

        except Exception as e:
            LOG.error(f"❌ Q&A Agent error: {e}", exc_info=True)
            return self._generate_smart_fallback(question)

    async def _get_interactable_elements(self):
        """Helper to safely get links and buttons from the page."""
        all_links = []
        all_buttons = []
        if not self.demo_page or self.demo_page.is_closed():
             LOG.warning("⚠️ Demo page not available for getting elements.")
             return [], []

        try:
            # Removed invalid timeout argument
            all_links = await self.demo_page.locator('a[href]:visible').evaluate_all(
                '(elements) => elements.map(e => ({ text: e.innerText.trim(), href: e.href })).filter(e => e.text && e.text.length > 1 && e.text.length < 100)'
                # Removed timeout=3000
            )
        except Exception as e:
            LOG.warning(f"⚠️ Could not get links: {e}")

        try:
            # Removed invalid timeout argument
            all_buttons = await self.demo_page.locator('button:visible, [role="button"]:visible').evaluate_all(
                '(elements) => elements.map(e => ({ text: e.innerText.trim(), name: e.name, id: e.id })).filter(e => e.text && e.text.length > 1 && e.text.length < 100)'
                 # Removed timeout=3000
            )
        except Exception as e:
            LOG.warning(f"⚠️ Could not get buttons: {e}")

        # Limit the number of elements sent to AI
        return all_links[:20], all_buttons[:20]


    async def execute_command(self, command: str, screenshot_path: str = None) -> dict:
        """
        Action Agent: Execute user commands with full visual understanding
        Returns action sequence to perform
        """
        LOG.info(f"🎯 Action Agent processing command: {command}")

        if not self.demo_page or self.demo_page.is_closed():
            LOG.error("❌ No demo page available for command execution.")
            return {"error": "Demo page not available"}

        try:
            # Take fresh screenshot if not provided
            if not screenshot_path or not os.path.exists(screenshot_path):
                screenshot_path = os.path.join("temp", f"cmd_{int(asyncio.get_event_loop().time())}.png")
                try:
                    await self.demo_page.screenshot(path=screenshot_path, timeout=5000)
                except Exception as ss_e:
                     LOG.error(f"❌ Failed to take screenshot for command: {ss_e}")
                     return {"error": "Failed to capture screen state"}

            # Get current page state
            current_url = self.demo_page.url

            # *** Get interactable elements ***
            all_links, all_buttons = await self._get_interactable_elements()

            # Build context for action planning
            context_package = self._build_context_package()

            # Ask Action AI to plan the action sequence with FULL context
            try:
                 img = Image.open(screenshot_path)
            except Exception as img_e:
                 LOG.error(f"❌ Failed to open screenshot image: {img_e}")
                 return {"error": "Failed to process screen image"}

            model = genai.GenerativeModel('gemini-2.5-flash')

            email, password = self.creds if self.creds else ("", "")

            prompt = f"""You are an Action Planning Agent executing user commands on a live website.

WEBSITE KNOWLEDGE (from Context Agent):
{json.dumps(self.website_knowledge, indent=2) if self.website_knowledge else "Limited knowledge"}

CURRENT DEMO STATE:
- URL: {current_url}
- Current Step: {self.demo_state.get('current_step', 'Unknown')}
- Last Action: {self.demo_state.get('last_action', 'Unknown')}

AVAILABLE INTERACTABLE ELEMENTS (Visible on current page):
- Links: {json.dumps(all_links, indent=2)}
- Buttons: {json.dumps(all_buttons, indent=2)}

USER COMMAND: "{command}"

Your task: Look at the screenshot and plan the EXACT actions to execute this command.

CRITICAL RULES:
1. **ANALYZE THE SCREENSHOT CAREFULLY** - Base your plan primarily on what you SEE.
2. **VERIFY ELEMENT EXISTENCE:** Critically verify the requested element (e.g., button text, link href from the command) EXISTS and is VISIBLE in the screenshot AND matches an entry in the ELEMENT LIST before generating a click/fill action.
3. **USE THE ELEMENT LIST:** Cross-reference visual analysis with the list to create ACCURATE selectors (e.g., `a[href="{all_links[0]['href']}"]` or `button:has-text("{all_buttons[0]['text']}")`). Prioritize text matches.
4. **Handle "go back"** → Use action 'back' with selector 'none'.
5. **Handle multi-step commands** like "go back and click X" → Provide both actions in the 'actions' array.
6. **IMPOSSIBLE COMMANDS:** If the command cannot be done on the *current visible page* (e.g., "click 'Book Demo'" when it's not visible or in the element list), return an EMPTY "actions" array and explain why in the "visual_analysis".
7. **BE SPECIFIC:** Use precise CSS selectors based on text or attributes from the element list/visuals.

Provide a JSON response:
{{
  "understood_command": "Your interpretation of what user wants",
  "visual_analysis": "What you see in the screenshot relevant to this command, explaining IF/WHY it's possible or impossible.",
  "actions": [
    {{
      "action": "fill|click|navigate|back|stop",
      "selector": "precise CSS selector or 'none'",
      "value": "text to fill or URL",
      "reasoning": "Why this action (referencing visual/element list)",
      "pre_narration": "What I'm about to do",
      "post_narration": "Confirmation",
      "expect_new_page": true/false
    }}
    // Include multiple actions if needed for multi-step commands
  ],
  "confidence": "high|medium|low",
  "potential_issues": "Any concerns"
}}"""

            response = await asyncio.to_thread(
                model.generate_content,
                [prompt, img],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048 # Increased previously
                )
            )

            # --- SAFETY CHECK ---
            if not response.parts:
                finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"
                error_msg = f"Gemini response blocked. Finish reason: {finish_reason}"
                LOG.error(f"❌ Action Agent error: {error_msg}")
                # Try to get safety ratings if available
                try:
                    safety_info = response.prompt_feedback
                    LOG.error(f"Safety Feedback: {safety_info}")
                except Exception:
                    pass
                return {"error": error_msg}


            # Parse response
            text = response.text.strip()
            # Try to find JSON block, be more lenient
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL) # Look for markdown block first
            if not match:
                 match = re.search(r'(\{.*?\})', text, re.DOTALL) # Fallback to any JSON block

            if match:
                try:
                    json_str = match.group(1)
                    action_plan = json.loads(json_str)
                    LOG.info(f"✅ Action Agent planned: {action_plan.get('understood_command')}")
                    LOG.info(f"   Visual analysis: {action_plan.get('visual_analysis', 'N/A')[:100]}...")
                    LOG.info(f"   Confidence: {action_plan.get('confidence', 'unknown')}")
                    LOG.info(f"   Actions planned: {len(action_plan.get('actions', []))}")

                    # Store in conversation memory
                    self.conversation_memory.append({
                        "type": "command",
                        "command": command,
                        "plan": action_plan, # Store the whole plan for context
                        "timestamp": asyncio.get_event_loop().time()
                    })

                    return action_plan
                except json.JSONDecodeError as json_e:
                     LOG.error(f"❌ Action Agent: Failed to decode JSON - {json_e}")
                     LOG.debug(f"Invalid JSON string: {json_str}")
                     return {"error": "Failed to parse action plan JSON"}
            else:
                LOG.error(f"❌ Could not parse action plan JSON from response: {text[:200]}...")
                return {"error": "Failed to parse action plan from AI response"}

        except Exception as e:
            LOG.error(f"❌ Action Agent error: {e}", exc_info=True)
            return {"error": str(e)}

    def _build_context_package(self) -> dict:
        """Build comprehensive context from all sources"""
        return {
            "website_knowledge": self.website_knowledge or {},
            "demo_state": self.demo_state,
            "conversation_history": self.conversation_memory[-5:],  # Last 5 interactions
            "current_url": self.demo_state.get("url", ""),
            "website_name": self.demo_state.get("website_name", "")
        }

    async def _answer_with_full_vision(self, question: str, context_package: dict, screenshot_path: str) -> str:
        """Answer using vision with FULL context awareness"""
        try:
            img = Image.open(screenshot_path)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Extract key info
            website_knowledge = context_package.get("website_knowledge", {})
            demo_state = context_package.get("demo_state", {})

            prompt = f"""You are a Q&A Agent demonstrating a website to a user. You have FULL context.

DEEP WEBSITE KNOWLEDGE (from Context Agent):
{json.dumps(website_knowledge, indent=2)}

CURRENT DEMO STATE:
- Current Step: {demo_state.get('current_step', 'Unknown')}
- Page: {demo_state.get('page_description', 'Unknown')}
- Progress: {demo_state.get('context', '')[-600:]}

RECENT INTERACTIONS:
{json.dumps(context_package.get('conversation_history', []), indent=2)}

USER'S QUESTION: "{question}"

INSTRUCTIONS:
1. **Look at the SCREENSHOT** - See what's actually on screen RIGHT NOW
2. **Use your WEBSITE KNOWLEDGE** - You know this platform deeply
3. **Reference DEMO STATE** - You know what you've been doing
4. **Be SPECIFIC and ACCURATE** - Don't be generic!
5. **Answer in 2-4 sentences** - Be concise but thorough
6. **Use the website's ACTUAL NAME** from your knowledge
7. **Reference what you SEE** in the screenshot when relevant
8. **Sound natural** - You're giving a live demo

Answer the question naturally and accurately:"""

            response = await asyncio.to_thread(
                model.generate_content,
                [prompt, img],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=200,
                    top_p=0.9
                )
            )

            # --- SAFETY CHECK ---
            if not response.parts:
                finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"
                LOG.error(f"❌ Q&A (Vision) error: Gemini response blocked. Finish reason: {finish_reason}")
                return await self._answer_with_knowledge(question, context_package) # Fallback

            answer = response.text.strip()

            # Store in conversation memory
            self.conversation_memory.append({
                "type": "question",
                "question": question,
                "answer": answer,
                "timestamp": asyncio.get_event_loop().time()
            })

            LOG.info(f"✅ Q&A Agent answered: {answer[:100]}...")
            return answer

        except Exception as e:
            LOG.error(f"❌ Vision Q&A failed: {e}", exc_info=True)
            return await self._answer_with_knowledge(question, context_package)

    async def _answer_with_knowledge(self, question: str, context_package: dict) -> str:
        """Fallback: Answer using knowledge base without vision"""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')

            website_knowledge = context_package.get("website_knowledge", {})
            demo_state = context_package.get("demo_state", {})

            prompt = f"""You are demonstrating a website. Answer based on your knowledge.

WEBSITE KNOWLEDGE:
{json.dumps(website_knowledge, indent=2)}

CURRENT STATUS:
{json.dumps(demo_state, indent=2)}

QUESTION: "{question}"

Provide a helpful 2-3 sentence answer. Be specific and reference the website by name."""

            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=150
                )
            )

            # --- SAFETY CHECK ---
            if not response.parts:
                finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"
                LOG.error(f"❌ Q&A (Knowledge) error: Gemini response blocked. Finish reason: {finish_reason}")
                return self._generate_smart_fallback(question) # Fallback

            answer = response.text.strip()
            LOG.info(f"✅ Knowledge-based answer: {answer[:100]}...")
            return answer

        except Exception as e:
            LOG.error(f"❌ Knowledge Q&A failed: {e}", exc_info=True)
            return self._generate_smart_fallback(question)

    def _generate_smart_fallback(self, question: str) -> str:
        """Last resort fallback using demo state"""
        website_name = self.demo_state.get("website_name", "this website")
        current_step = self.demo_state.get("current_step", "demonstrating")

        if self.website_knowledge:
            purpose = self.website_knowledge.get("purpose", "a web platform")
            return f"Based on what I'm showing you, {website_name} {purpose}. I'm currently {current_step}. Let me continue and it should become clearer."
        else:
            return f"That's a great question about {website_name}. I'm currently {current_step}. Watch as I continue the demonstration and it should answer your question."


# ==================== INTEGRATION WRAPPER ====================

async def handle_user_question(question: str, orchestrator: AIAgentOrchestrator, screenshot_path: str = None) -> str:
    """
    Handle user question through the orchestrator
    """
    # Auto-detect screenshot if not provided
    if not screenshot_path:
        screenshot_path = find_latest_screenshot()

    return await orchestrator.answer_question(question, screenshot_path)


async def handle_user_command(command: str, orchestrator: AIAgentOrchestrator, screenshot_path: str = None) -> dict:
    """
    Handle user command through the orchestrator
    """
    # Auto-detect screenshot if not provided
    if not screenshot_path:
        screenshot_path = find_latest_screenshot()

    return await orchestrator.execute_command(command, screenshot_path)


def find_latest_screenshot() -> str:
    """Find the most recent screenshot"""
    try:
        temp_dir = Path("temp")
        if not temp_dir.exists():
            return None

        # Prioritize obs_ screenshots
        screenshots = list(temp_dir.glob("obs_*.png"))
        if not screenshots:
             # Fallback to any png
            screenshots = list(temp_dir.glob("*.png"))

        if screenshots:
            latest = max(screenshots, key=lambda p: p.stat().st_mtime)
            return str(latest)

        return None
    except Exception as e:
        LOG.warning(f"Error finding latest screenshot: {e}")
        return None