import logging
import os
import shutil
import subprocess
import hashlib

def build_y4m_from_image(image_path: str, out_y4m: str = None, duration_s: int = 120, fps: int = 30) -> str:
    """
    Convert an image into a Y4M looping video file for virtual camera.
    Uses caching so ffmpeg runs only if needed.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg not found in PATH.")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Create a cache filename based on image hash + params
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "cache")
    os.makedirs(cache_dir, exist_ok=True)

    with open(image_path, "rb") as f:
        image_hash = hashlib.md5(f.read()).hexdigest()[:8]

    cached_y4m = os.path.join(cache_dir, f"static_{image_hash}_{fps}fps_{duration_s}s.y4m")

    # ✅ Use existing cached file if already generated
    if os.path.exists(cached_y4m):
        logging.info(f"✅ Using cached Y4M: {cached_y4m}")
        return cached_y4m

    # 🎥 Generate once using ffmpeg with correct aspect + padding
    logging.info("🎥 Generating Y4M from image (first time)...")
    cmd = [
        ffmpeg_path,
        "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease:flags=lanczos,"
                "pad=1280:720:(ow-iw)/2:(oh-ih)/2:white",
        "-t", str(duration_s),
        "-r", str(fps),
        "-pix_fmt", "yuv420p",
        cached_y4m,
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(result.stderr.decode(errors="ignore"))
        raise RuntimeError("❌ ffmpeg failed to create Y4M file.")

    logging.info(f"✅ Y4M created and cached: {cached_y4m}")
    return cached_y4m
