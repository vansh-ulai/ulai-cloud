"""
Gemini API Handler for Ulai AI Agent
=====================================
This module provides integration with Google's Gemini API for generating
demo scripts based on website analysis.

Author: Ulai Systems Architecture
"""

import os
import logging
import google.generativeai as genai

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found in environment variables")
else:
    genai.configure(api_key=GEMINI_API_KEY)


def get_gemini_response(prompt: str, model_name: str = "gemini-pro") -> str:
    """
    Send a prompt to Gemini API and return the generated response.
    
    Parameters
    ----------
    prompt : str
        The prompt to send to Gemini
    model_name : str
        The Gemini model to use (default: "gemini-pro")
    
    Returns
    -------
    str
        The generated text response from Gemini, or None if error
    
    Example
    -------
    >>> code = get_gemini_response("Generate a Python function...")
    >>> print(code)
    """
    try:
        if not GEMINI_API_KEY:
            logger.error("Cannot call Gemini API: GEMINI_API_KEY not configured")
            return None
        
        # Initialize the model
        model = genai.GenerativeModel(model_name)
        
        # Generate content
        logger.info(f"📡 Sending request to Gemini ({model_name})...")
        response = model.generate_content(prompt)
        
        # Extract text from response
        if response and response.text:
            logger.info(f"✅ Received {len(response.text)} characters from Gemini")
            return response.text
        else:
            logger.warning("Gemini returned empty response")
            return None
            
    except Exception as e:
        logger.exception(f"Error calling Gemini API: {e}")
        return None


async def get_gemini_response_async(prompt: str, model_name: str = "gemini-pro") -> str:
    """
    Async wrapper for get_gemini_response.
    
    Parameters
    ----------
    prompt : str
        The prompt to send to Gemini
    model_name : str
        The Gemini model to use (default: "gemini-pro")
    
    Returns
    -------
    str
        The generated text response from Gemini, or None if error
    """
    import asyncio
    return await asyncio.to_thread(get_gemini_response, prompt, model_name)


def extract_code_from_response(response: str) -> str:
    """
    Extract Python code from Gemini's response, removing markdown formatting.
    
    Parameters
    ----------
    response : str
        The raw response from Gemini
    
    Returns
    -------
    str
        Clean Python code
    """
    if not response:
        return ""
    
    # Remove markdown code blocks if present
    if "```python" in response:
        start = response.find("```python") + len("```python")
        end = response.find("```", start)
        if end != -1:
            return response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + len("```")
        end = response.find("```", start)
        if end != -1:
            return response[start:end].strip()
    
    return response.strip()