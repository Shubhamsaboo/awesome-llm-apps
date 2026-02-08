"""Media generation module: images, voiceover, and video assembly.

- Image generation via DALL-E 3 (OpenAI)
- Voiceover via OpenAI TTS
- Video assembly via ffmpeg (image + audio → vertical video)
"""

import os
import uuid
from pathlib import Path
from textwrap import dedent
from typing import Optional

from openai import OpenAI
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat

MEDIA_DIR = Path(os.getenv("MEDIA_DIR", "media"))
MEDIA_DIR.mkdir(exist_ok=True)


# ── Image Generation (DALL-E 3) ────────────────────────────────────────


def generate_image_prompt(
    topic: str,
    content_type: str,
    service_focus: str,
    openai_api_key: str,
) -> str:
    """Use an AI agent to craft a DALL-E prompt for the given content."""
    agent = Agent(
        name="Image Prompt Designer",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description="You design DALL-E 3 prompts for professional agricultural drone imagery.",
        instructions=[
            "Create a detailed DALL-E 3 image prompt for a website banner/hero image.",
            "The image must represent AgroDrone Europe — a professional agricultural drone company in Germany.",
            "Style: modern, clean, professional photography look. NO text in the image.",
            "Include relevant visual elements: agricultural drones, German farmland, crops, precision agriculture.",
            "For Pflanzenschutz: drone spraying over green fields.",
            "For Aussaat: drone seeding over prepared soil.",
            "For NDVI: drone with multispectral camera, colorful NDVI overlay on fields.",
            "For Dachreinigung: drone near a rooftop, cleaning equipment.",
            "Output ONLY the prompt text, nothing else. Max 200 words.",
        ],
        markdown=False,
    )

    response: RunOutput = agent.run(
        f"Create image prompt for: {content_type} about '{topic}' (service: {service_focus})",
        stream=False,
    )
    return response.content.strip()


def generate_image(
    prompt: str,
    openai_api_key: str,
    size: str = "1792x1024",
    quality: str = "standard",
) -> dict:
    """Generate an image using DALL-E 3.

    Args:
        prompt: The DALL-E prompt.
        size: Image size. Use '1792x1024' for website banners, '1024x1792' for vertical/social.
        quality: 'standard' or 'hd'.

    Returns:
        Dict with 'url' (OpenAI hosted), 'local_path', and 'prompt'.
    """
    client = OpenAI(api_key=openai_api_key)

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )

    image_url = response.data[0].url
    revised_prompt = response.data[0].revised_prompt

    return {
        "url": image_url,
        "revised_prompt": revised_prompt,
        "original_prompt": prompt,
        "size": size,
    }


def generate_content_image(
    topic: str,
    content_type: str,
    service_focus: str,
    openai_api_key: str,
    size: str = "1792x1024",
) -> dict:
    """Full pipeline: generate prompt → generate image.

    Returns dict with url, prompt, etc.
    """
    prompt = generate_image_prompt(topic, content_type, service_focus, openai_api_key)
    result = generate_image(prompt, openai_api_key, size=size)
    return result


# ── Voiceover (OpenAI TTS) ─────────────────────────────────────────────


def generate_voiceover(
    text: str,
    openai_api_key: str,
    voice: str = "nova",
    model: str = "tts-1",
) -> dict:
    """Generate voiceover audio using OpenAI TTS.

    Args:
        text: Text to convert to speech.
        voice: Voice choice — alloy, echo, fable, onyx, nova, shimmer.
        model: tts-1 (fast) or tts-1-hd (high quality).

    Returns:
        Dict with 'local_path' and metadata.
    """
    client = OpenAI(api_key=openai_api_key)

    filename = f"voiceover_{uuid.uuid4().hex[:8]}.mp3"
    filepath = MEDIA_DIR / filename

    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
    )
    response.stream_to_file(str(filepath))

    return {
        "local_path": str(filepath),
        "filename": filename,
        "voice": voice,
        "model": model,
        "text_length": len(text),
    }


# ── Social Media Content Agent ─────────────────────────────────────────


def generate_social_media_pack(
    topic: str,
    content_markdown: str,
    service_focus: str,
    openai_api_key: str,
    language: str = "German",
) -> dict:
    """Generate social media content pack: posts + voiceover scripts.

    Returns dict with posts for each platform and voiceover scripts.
    """
    agent = Agent(
        name="Social Media Manager",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent("""\
            You are the social media manager for AgroDrone Europe (agrodroneeurope.com).
            You create engaging social media content for agricultural drone services
            in Germany. You specialize in short-form vertical video scripts."""),
        instructions=[
            f"Create social media content in {language} based on the provided article.",
            "Generate content for these platforms:",
            "",
            "1. **LinkedIn** — professional B2B post (max 1300 chars). Target: farmers, agronomists, farm managers.",
            "2. **Instagram** — engaging caption (max 500 chars) + 5 relevant hashtags. Visual-first.",
            "3. **Facebook** — informative post (max 800 chars) with call-to-action.",
            "4. **TikTok/Reels Script** — 30-60 second vertical video script with:",
            "   - Hook (first 3 seconds to grab attention)",
            "   - 3-4 key points with timestamps",
            "   - Call-to-action ending",
            "   - Suggested background music mood",
            "5. **Voiceover Text** — clean narration text for the vertical video (no timestamps, no stage directions).",
            "   This will be fed to TTS, so write naturally spoken text only.",
            "",
            "Format output as clear sections with platform headers.",
            "Always mention agrodroneeurope.com in the CTA.",
            "Use relevant emojis for social platforms.",
        ],
        add_datetime_to_context=True,
        markdown=True,
    )

    prompt = dedent(f"""\
        Create a social media content pack for AgroDrone Europe.

        Topic: {topic}
        Service Focus: {service_focus}
        Language: {language}

        Source article (summarize for social, don't copy):
        {content_markdown[:3000]}
    """)

    response: RunOutput = agent.run(prompt, stream=False)

    # Extract voiceover text (the agent puts it in the Voiceover Text section)
    full_text = response.content
    voiceover_text = ""
    if "Voiceover" in full_text:
        parts = full_text.split("Voiceover")
        if len(parts) > 1:
            voiceover_section = parts[-1]
            # Clean up markdown headers and get just the text
            lines = voiceover_section.strip().split("\n")
            clean_lines = [
                l for l in lines
                if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("**")
            ]
            voiceover_text = "\n".join(clean_lines).strip()

    return {
        "social_media_content": full_text,
        "voiceover_text": voiceover_text,
        "platforms": ["linkedin", "instagram", "facebook", "tiktok_reels"],
    }


# ── Video Assembly (ffmpeg) ─────────────────────────────────────────────


def assemble_vertical_video(
    image_path: str,
    audio_path: str,
    output_filename: Optional[str] = None,
) -> dict:
    """Create a vertical video (9:16) from a static image + voiceover audio using ffmpeg.

    Args:
        image_path: Path to the background image.
        audio_path: Path to the voiceover MP3.
        output_filename: Optional custom filename.

    Returns:
        Dict with 'local_path' and metadata.
    """
    import subprocess

    if not output_filename:
        output_filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
    output_path = MEDIA_DIR / output_filename

    # ffmpeg: scale image to 1080x1920 (9:16), loop for audio duration, add audio
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        return {
            "error": result.stderr,
            "local_path": None,
        }

    return {
        "local_path": str(output_path),
        "filename": output_filename,
        "image_source": image_path,
        "audio_source": audio_path,
    }
