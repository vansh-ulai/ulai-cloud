import os
import asyncio
import logging
from typing import Optional

# llama-cpp-python import
try:
    from llama_cpp import Llama
except Exception as e:
    logging.exception("llama_cpp import failed — install llama-cpp-python with GPU support if available.")
    raise

# ===== CONFIG =====
# Point this to your downloaded GGUF model (TinyLlama recommended for speed)
DEFAULT_MODEL_PATH = r"C:\models\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"  # <-- update if needed

# Tunables for low latency
DEFAULT_N_CTX = 1024
DEFAULT_MAX_TOKENS = 60   # keep answers short for real-time
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.9
DEFAULT_N_THREADS = os.cpu_count() or 4
# If GPU present and llama-cpp-python built with CUDA, we will set n_gpu_layers automatically
DEFAULT_N_GPU_LAYERS = None  # None -> auto-detect and use a safe default

# singleton LLM
_LLM: Optional[Llama] = None
_LLM_CONFIG = {}

def _detect_cuda_layers_guess():
    """
    Heuristic for n_gpu_layers for RTX 3050 (6GB). Use conservative default.
    If you have >=6GB VRAM, 16-24 is often good for small models.
    """
    # default to 20 for RTX 3050 (user reported), but allow env override
    env = os.environ.get("LLM_GPU_LAYERS")
    if env:
        try:
            return int(env)
        except Exception:
            pass
    return 20

def init_llm(model_path: Optional[str] = None, n_ctx: int = DEFAULT_N_CTX,
             n_threads: int = DEFAULT_N_THREADS, n_gpu_layers: Optional[int] = DEFAULT_N_GPU_LAYERS):
    """
    Initialize the Llama instance once. If GPU is available, pass n_gpu_layers>0.
    """
    global _LLM, _LLM_CONFIG
    if _LLM is not None:
        return _LLM

    model_path = model_path or DEFAULT_MODEL_PATH
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")

    # decide n_gpu_layers if None
    if n_gpu_layers is None:
        n_gpu_layers = _detect_cuda_layers_guess()

    logging.info("Initializing LLM: %s (ctx=%s threads=%s gpu_layers=%s)",
                 model_path, n_ctx, n_threads, n_gpu_layers)

    # Create Llama instance
    try:
        _LLM = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )
    except TypeError:
        logging.warning("llama-cpp-python refused n_gpu_layers param; retrying without GPU arg.")
        _LLM = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads, verbose=False)

    _LLM_CONFIG = {
        "model_path": model_path, "n_ctx": n_ctx, "n_threads": n_threads, "n_gpu_layers": n_gpu_layers
    }
    logging.info("LLM initialized.")
    return _LLM

async def get_local_llm_response_async(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    """
    Async wrapper returning a short, focused assistant reply.
    """
    global _LLM
    if _LLM is None:
        # lazy init
        init_llm()

    prompt = (prompt or "").strip()
    if not prompt:
        return ""

    # --- MODIFIED: Updated system instruction with the new persona ---
    system_instruction = (
        "You are an AI assistant. Your name is Ulai AI. You must always refer to yourself as Ulai AI. "
        "Do not misspell or change your name. Your purpose is to provide quick, accurate information to participants in a live meeting. "
        "Keep your answers brief and direct (one or two sentences)."
    )
    
    full_prompt = f"{system_instruction}\n\nUser asks: {prompt}\nUlai AI answers:"

    def _call():
        # run the generation synchronously in background thread
        gen = _LLM(
            full_prompt,
            max_tokens=max_tokens,
            temperature=DEFAULT_TEMPERATURE,
            top_p=DEFAULT_TOP_P,
            echo=False,
            # Updated stop tokens to match the new prompt structure
            stop=["\n", "User asks:", "Ulai AI answers:"]
        )

        # extract text robustly
        try:
            text = gen["choices"][0]["text"]
        except Exception:
            if isinstance(gen, dict) and "choices" in gen and gen["choices"]:
                text = gen["choices"][0].get("text", "")
            else:
                text = str(gen)
        return (text or "").strip()

    # run in thread to keep event loop responsive
    return await asyncio.to_thread(_call)