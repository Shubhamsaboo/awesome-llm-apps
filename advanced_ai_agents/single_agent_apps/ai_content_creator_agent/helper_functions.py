import requests
import pyttsx3
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ColorClip, CompositeAudioClip
import os

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

# ==========================================IMAGE MAKER FUNCTIONS==========================================


# =============================================================================
# FONT HELPER: Load default font at given size
# =============================================================================
def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Returns PIL default font scaled to the specified size
    return ImageFont.load_default(size)


# =============================================================================
# FONT SIZING: Binary search for largest font that fits text in given dimensions
# =============================================================================
def _find_font_size(text: str, max_width: int, max_height: int) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    # Binary search bounds: min 16px, max 80px
    lo, hi = 16, 80
    best_font = _get_font(hi)
    best_lines = textwrap.wrap(text, width=30)
    
    while lo <= hi:
        mid = (lo + hi) // 2
        font = _get_font(mid)
        # Estimate chars per line based on font size and width (0.55 = approx char width ratio)
        chars_per_line = max(10, int(max_width / (mid * 0.55)))
        lines = textwrap.wrap(text, width=chars_per_line)
        # Compute line height from font bbox; 8px spacing between lines
        line_h = max(font.getbbox(l)[3] - font.getbbox(l)[1] for l in lines) if lines else mid
        total_h = len(lines) * line_h + max(0, len(lines) - 1) * 8
        
        if total_h <= max_height:
            best_font, best_lines = font, lines
            lo = mid + 1
        else:
            hi = mid - 1
    
    return best_font, best_lines


# =============================================================================
# MAIN: Create image from Pexels API with text overlay
# =============================================================================
def create_pexels_image_with_text(
    pexels_api_key: str, search_query: str, text: str
) -> str | None:
    """
    Fetch a single image from the Pexels API using search_query
    and overlay the provided text on top of it.
    Returns the path to the saved image, or None on failure.
    """
    # --- API Request: Search Pexels for a single image ---
    headers = {"Authorization": pexels_api_key}
    resp = requests.get(
        "https://api.pexels.com/v1/search",
        params={"query": search_query, "per_page": 1},
        headers=headers,
        timeout=15,
    )

    # --- Response validation: Check HTTP status and presence of photos ---
    if resp.status_code != 200:
        return "Failed to fetch image from Pexels API"

    data = resp.json()
    photos = data.get("photos") or []
    if not photos:
        return "No photos found in Pexels API response"

    # --- Image URL extraction: Prefer large/2x, fallback to medium/original ---
    src = photos[0].get("src") or {}
    image_url = (
        src.get("large") or src.get("large2x") or src.get("medium") or src.get("original")
    )
    if not image_url:
        return "No image URL found in Pexels API response"

    # --- Image fetch: Download image bytes from URL ---
    img_resp = requests.get(image_url, timeout=15)
    if img_resp.status_code != 200:
        return "Failed to fetch image from Pexels API"

    # --- Image load: Open from bytes, convert to RGB ---
    image = Image.open(BytesIO(img_resp.content)).convert("RGB")
    # --- Crop to square: Center-crop using the smaller dimension ---
    width, height = image.size
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    image = image.crop((left, top, left + size, top + size))

    # --- Resize: Standard 1080x1080 for social/reels format ---
    STANDARD_SIZE = 1080  # or 720, 1024, etc.
    image = image.resize((STANDARD_SIZE, STANDARD_SIZE), Image.Resampling.LANCZOS)
    

    # --- Text overlay setup: Create draw context and define text box region ---
    draw = ImageDraw.Draw(image, "RGBA")


    width, height = image.size
    margin = int(0.05 * width)
    box_height = int(0.25 * height)
    box_y0 = height - box_height - margin
    box_y1 = height - margin

    # Semi-transparent black rectangle for text background
    draw.rectangle(
        [margin, box_y0, width - margin, box_y1],
        fill=(0, 0, 0, 180),
    )

    max_text_width = width - 2 * margin

    # --- Text layout: Find optimal font size and wrap lines to fit box ---
    font, wrapped_lines = _find_font_size(text, max_text_width, box_height - 20)
    line_heights = []
    for line in wrapped_lines:
        bbox = font.getbbox(line)
        line_heights.append(bbox[3] - bbox[1])

    line_height = max(line_heights) if line_heights else 16
    total_text_height = len(wrapped_lines) * line_height + max(len(wrapped_lines) - 1, 0) * 4

    # --- Text rendering: Center each line horizontally, stack vertically ---
    current_y = box_y0 + (box_height - total_text_height) / 2
    for line in wrapped_lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        if line_width > max_text_width:
            # Fall back: scale wrapping based on approximate character width
            pass
        x = margin + (max_text_width - line_width) / 2
        draw.text((x, current_y), line, font=font, fill=(255, 255, 255, 255))
        current_y += line_height + 4

    # --- Save: Write final image to disk as JPEG ---
    os.makedirs('./output', exist_ok=True)        
    output_path = "./output/generated_image.jpg"
    image.save(output_path, format="JPEG")
    return "Image created successfully!"


# ==========================================REELS MAKER FUNCTIONS==========================================


# =============================================================================
# PEXELS VIDEO DOWNLOAD
# =============================================================================
def download_pexels_video(api_key: str, query: str, clip_number: int) -> str | None:
    # Construct the Pexels API endpoint and headers
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
    headers = {"Authorization": api_key}

    # Make the API request to fetch videos
    print(f"Using API for {clip_number} with {query}")
    response = requests.get(url, headers=headers)

    # Handle the response from the API
    if response.status_code == 200:
        videos = response.json().get('videos')
        if not videos:
            print(f"No videos found for {query}.")
            return None

        video_url = videos[0]['video_files'][0]['link']

        print(f"Downloading video {clip_number} from {video_url}...")

    else:
        print(f"Failed to fetch video for {query}. Status code: {response.status_code}")
        return None

    # Download the video file to disk
    os.makedirs('./temp_data', exist_ok=True)        

    video_filename = f'./temp_data/clip_{clip_number}.mp4'
    video_data = requests.get(video_url)
    if video_data.status_code == 400:
        print(f"Failed to fetch video using url {video_url}. Status code: {response.status_code}")
        return None
    with open(video_filename, 'wb') as file:
        file.write(video_data.content)

    # Return the path to the downloaded video
    print(f"Video {clip_number} downloaded successfully.")
    return video_filename
   

# =============================================================================
# VOICEOVER GENERATION
# =============================================================================
def generate_voiceover(text, clip_number) -> str:
    """Generate TTS voiceover from text using pyttsx3 and save as MP3."""
    # Create the temporary data directory if it doesn't exist
    os.makedirs('./temp_data', exist_ok=True)        
    
    # Create the audio filename
    audio_filename = f'./temp_data/voiceover_{clip_number}.mp3'
    
    # Initialize, setup and save the TTS engine
    engine = pyttsx3.init()
    engine.save_to_file(text, audio_filename)
    engine.runAndWait()
    
    # Print the voiceover generation status
    print(f"Voiceover {clip_number} generated.")
    
    # Return the path to the generated audio file
    return audio_filename


# =============================================================================
# CLIP CREATION (VIDEO + AUDIO + CAPTIONS)
# =============================================================================
def create_clip(video_file: str, audio_file: str, caption_text: str) -> VideoFileClip | None:
    """Compose a single reel clip: video trimmed to audio length, resized to 1080x1920, with captions overlay."""
    
    # --- Load and prepare video/audio ---
    try:
        # Load audio
        audio_clip = AudioFileClip(audio_file)
        print(audio_clip.duration)

        # Load video
        video_clip = VideoFileClip(video_file)
        if video_clip is None:
            print(f"Error: Failed to load video file {video_file}")
            return None
            
        video_clip = video_clip.subclipped(0, audio_clip.duration)

        # Resize video to a vertical height of 1920
        video_clip = video_clip.resized(height=1920)

        # Center crop to 1080x1920 (Reels size)
        if video_clip.w > 1080:
            x_center = video_clip.w / 2
            video_clip = video_clip.cropped(x_center=x_center, y_center=960, width=1080, height=1920)
        else:
            # If the width is less than 1080, add black bars (optional)
            video_clip = video_clip.resized(width=1080)
        
        video_clip = video_clip.with_audio(audio_clip)
    except Exception as e:
        print(f"Error creating clip from {video_file}: {e}")
        return None


    # --- Caption overlay: dark box + animated text ---
    # Create caption text with stroke
    char_count = len(caption_text)
    font_size = max(40, min(100, 100 - char_count * 0.6))

    caption = TextClip(text=caption_text, font_size=font_size, color='white',
                       stroke_color='black', stroke_width=3, method='caption', size=(1080, 200), text_align='center')

    caption = caption.with_duration(video_clip.duration)

    # Create background box behind the text
    box_height = caption.h + 60
    background_box = ColorClip(size=(1080, box_height), color=(0, 0, 0))
    background_box = background_box.with_opacity(0.6)
    background_box = background_box.with_duration(video_clip.duration)
    background_box = background_box.with_position(('center', 'center'))

    # Text sliding animation (slide in from the left)
    def slide_in(t):
        return (-caption.w + (t / 0.5) * caption.w) if t < 0.5 else 0

    animated_caption = caption.with_position(lambda t: (slide_in(t), 'center'))

    # Combine video, background box, and animated text
    final_clip = CompositeVideoClip([video_clip, background_box, animated_caption], size=(1080, 1920))

    return final_clip


# =============================================================================
# MAIN WORKFLOW - CREATE COMPLETE REEL
# =============================================================================
def create_complete_reel(items: list[dict], pexels_api_key: str) -> str | None:
    """
    Create a complete reel from a list of dictionaries, where each dictionary has:
      - "line": caption / voiceover text
      - "search_query": query string for Pexels
    """

    os.makedirs('./output', exist_ok=True)        
    FINAL_OUTPUT_FILE = './output/generated_reel.mp4'

    all_clips = []

    # --- Generate individual clips (video + voiceover + captions) ---
    for i, item in enumerate(items, start=1):
        line = (item.get("line") or "").strip()
        search_query = (item.get("search_query") or "").strip()

        if not line or not search_query:
            continue

        video_file = download_pexels_video(pexels_api_key, search_query, i)
        if not video_file:
            continue

        audio_file = generate_voiceover(line, i)
        
        final_clip = create_clip(video_file, audio_file, line)
        if final_clip is not None:
            all_clips.append(final_clip)
        else:
            print(f"Warning: Skipping clip {i} due to creation error")

    # --- Concatenate clips, add background music, and export ---
    if all_clips:
        final_reel = concatenate_videoclips(all_clips, method="compose")

        try:
            background_music = AudioFileClip('./background_music.mp3').with_volume_scaled(0.3).subclipped(0, final_reel.duration)
            final_audio = CompositeAudioClip([final_reel.audio, background_music])

        except Exception as e:
            final_audio = final_reel.audio  # use voiceover only

        final_reel = final_reel.with_audio(final_audio)

        final_reel.write_videofile(FINAL_OUTPUT_FILE, fps=24)

        return f"Final multi-clip video created successfully!"

    else:
        print("No clips were successfully processed.")
        return "No clips were successfully processed."


# =============================================================================
# CLEAR TEMP DATA
# =============================================================================
def clear_temp_data():
    """Clear all temporary data files."""
    os.makedirs('./temp_data', exist_ok=True)
    for file in os.listdir('./temp_data'):
        os.remove(os.path.join('./temp_data', file))
    os.rmdir('./temp_data')

# =============================================================================
# DEMO / SCRIPT ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    demo_pexels_api_key = ""
    if not demo_pexels_api_key:
        print("Set the PEXELS_API_KEY environment variable to run the demo.")
    else:
        # Demo: create_pexels_image_with_text (single quote/poster image)
        print("--- Demo: create_pexels_image_with_text ---")
        create_pexels_image_with_text(
            pexels_api_key=demo_pexels_api_key,
            search_query="motivation",
            text="The only way to do great work is to love what you do.",
        )

        # Demo: create_complete_reel (multi-clip video)
        print("\n--- Demo: create_complete_reel ---")
        demo_summary_text = """
        Businesses are changing. Robots are taking over. Earth is in danger.
        """
        demo_lines = [line.strip() for line in demo_summary_text.strip().split('.') if line.strip()]
        demo_items = [{"line": line, "search_query": line.split()[0]} for line in demo_lines]
        create_complete_reel(demo_items, demo_pexels_api_key)