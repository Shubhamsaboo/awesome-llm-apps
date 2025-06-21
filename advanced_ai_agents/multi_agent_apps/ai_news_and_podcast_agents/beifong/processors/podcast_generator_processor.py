import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.pipeline.search_agent import search_agent_run
from tools.pipeline.scrape_agent import scrape_agent_run
from tools.pipeline.script_agent import script_agent_run
from tools.pipeline.image_generate_agent import image_generation_agent_run
from db.config import get_tracking_db_path, get_podcasts_db_path, get_tasks_db_path
from db.podcast_configs import get_podcast_config, get_all_podcast_configs
from db.agent_config_v2 import AVAILABLE_LANGS
from utils.tts_engine_selector import generate_podcast_audio
from utils.load_api_keys import load_api_key
from tools.session_state_manager import _save_podcast_to_database_sync

PODCAST_ASSETS_DIR = "podcasts"


def get_language_name(language_code: str) -> str:
    language_map = {lang["code"]: lang["name"] for lang in AVAILABLE_LANGS}
    return language_map.get(language_code, "English")


def convert_script_to_audio_format(podcast_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    speaker_map = {"ALEX": 1, "MORGAN": 2}
    dict_entries = []
    for section in podcast_data.get("sections", []):
        for dialog in section.get("dialog", []):
            speaker = dialog.get("speaker", "ALEX")
            text = dialog.get("text", "")
            if text and speaker in speaker_map:
                dict_entries.append({"text": text, "speaker": speaker_map[speaker]})
    return {"entries": dict_entries}


def generate_podcast_from_prompt_v2(
    prompt: str,
    openai_api_key: str,
    tracking_db_path: Optional[str] = None,
    podcasts_db_path: Optional[str] = None,
    output_dir: str = PODCAST_ASSETS_DIR,
    tts_engine: str = "kokoro",
    language_code: str = "en",
    podcast_script_prompt: Optional[str] = None,
    image_prompt: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if podcasts_db_path is None:
        podcasts_db_path = get_podcasts_db_path()
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    print(f"Starting enhanced podcast generation for prompt: {prompt}")
    try:
        search_results = search_agent_run(prompt)
        if not search_results:
            print(f"WARNING: No search results found for prompt: {prompt}")
            return {"error": "No search results found"}
        print(f"Found {len(search_results)} search results")
        if debug:
            print("Search results:", json.dumps(search_results[:2], indent=2))
    except Exception as e:
        print(f"ERROR: Search agent failed: {e}")
        return {"error": f"Search agent failed: {str(e)}"}
    try:
        scraped_results = scrape_agent_run(prompt, search_results)
        if not scraped_results:
            print("WARNING: No content could be scraped")
            return {"error": "No content could be scraped"}
        confirmed_results = []
        for result in scraped_results:
            if result.get("full_text") and len(result["full_text"].strip()) > 100:
                result["confirmed"] = True
                confirmed_results.append(result)
        if not confirmed_results:
            print("WARNING: No high-quality content available after scraping")
            return {"error": "No high-quality content available"}
        print(f"Successfully scraped {len(confirmed_results)} high-quality articles")
        if debug:
            print("Sample scraped content:", confirmed_results[0].get("full_text", "")[:200])
    except Exception as e:
        print(f"ERROR: Scrape agent failed: {e}")
        return {"error": f"Scrape agent failed: {str(e)}"}
    try:
        language_name = get_language_name(language_code)
        podcast_data = script_agent_run(query=prompt, search_results=confirmed_results, language_name=language_name)
        if not podcast_data or not isinstance(podcast_data, dict):
            print("ERROR: Failed to generate podcast script")
            return {"error": "Failed to generate podcast script"}
        if not podcast_data.get("sections"):
            print("ERROR: Generated podcast script is missing required sections")
            return {"error": "Invalid podcast script structure"}
        print(f"Generated script with {len(podcast_data['sections'])} sections")
        if debug:
            print("Script title:", podcast_data.get("title", "No title"))
    except Exception as e:
        print(f"ERROR: Script agent failed: {e}")
        return {"error": f"Script agent failed: {str(e)}"}
    banner_filenames = []
    banner_url = None
    try:
        image_query = image_prompt if image_prompt else prompt
        image_result = image_generation_agent_run(image_query, podcast_data)
        if image_result and image_result.get("banner_images"):
            banner_filenames = image_result["banner_images"]
            banner_url = image_result.get("banner_url")
            print(f"Generated {len(banner_filenames)} banner images")
        else:
            print("WARNING: No images were generated")
    except Exception as e:
        print(f"ERROR: Image generation failed: {e}")
    audio_filename = None
    full_audio_path = None
    try:
        audio_format = convert_script_to_audio_format(podcast_data)
        audio_filename = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        audio_path = os.path.join(output_dir, "audio", audio_filename)

        class DictPodcastScript:
            def __init__(self, entries):
                self.entries = entries

            def __iter__(self):
                return iter(self.entries)

        script_obj = DictPodcastScript(audio_format["entries"])
        full_audio_path = generate_podcast_audio(
            script=script_obj,
            output_path=audio_path,
            tts_engine=tts_engine,
            language_code=language_code,
        )
        if full_audio_path:
            print(f"Generated podcast audio: {full_audio_path}")
        else:
            print("ERROR: Failed to generate audio")
            audio_filename = None
    except Exception as e:
        print(f"ERROR: Error generating audio: {e}")
        import traceback

        traceback.print_exc()
        audio_filename = None
    try:
        session_state = {
            "generated_script": podcast_data,
            "banner_url": banner_url,
            "banner_images": banner_filenames,
            "audio_url": full_audio_path,
            "tts_engine": tts_engine,
            "selected_language": {"code": language_code, "name": get_language_name(language_code)},
            "podcast_info": {"topic": prompt},
        }
        success, message, podcast_id = _save_podcast_to_database_sync(session_state)
        if success:
            print(f"Stored podcast data with ID: {podcast_id}")
        else:
            print(f"ERROR: Failed to save to database: {message}")
            podcast_id = 0
    except Exception as e:
        print(f"ERROR: Error storing podcast data: {e}")
        podcast_id = 0
    if audio_filename:
        frontend_audio_path = os.path.join(output_dir, audio_filename).replace("\\", "/")
    else:
        frontend_audio_path = None
    if banner_url:
        frontend_banner_path = banner_url.replace("\\", "/")
    else:
        frontend_banner_path = None
    return {
        "podcast_id": podcast_id,
        "title": podcast_data.get("title", "Podcast"),
        "audio_path": frontend_audio_path,
        "banner_path": frontend_banner_path,
        "banner_images": banner_filenames,
        "script": podcast_data,
        "tts_engine": tts_engine,
        "language": language_code,
        "sources_count": len(confirmed_results),
        "processing_stats": {
            "search_results": len(search_results),
            "scraped_results": len(scraped_results),
            "confirmed_results": len(confirmed_results),
            "images_generated": len(banner_filenames),
            "audio_generated": bool(audio_filename),
        },
    }


def generate_podcast_from_config_v2(
    config_id: int,
    openai_api_key: str,
    tracking_db_path: Optional[str] = None,
    podcasts_db_path: Optional[str] = None,
    tasks_db_path: Optional[str] = None,
    output_dir: str = PODCAST_ASSETS_DIR,
    debug: bool = False,
) -> Dict[str, Any]:
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if podcasts_db_path is None:
        podcasts_db_path = get_podcasts_db_path()
    if tasks_db_path is None:
        tasks_db_path = get_tasks_db_path()
    config = get_podcast_config(tasks_db_path, config_id)
    if not config:
        print(f"ERROR: Podcast configuration not found: {config_id}")
        return {"error": f"Podcast configuration not found: {config_id}"}
    prompt = config.get("prompt", "")
    time_range_hours = config.get("time_range_hours", 24)
    limit_articles = config.get("limit_articles", 20)
    tts_engine = config.get("tts_engine", "elevenlabs")
    language_code = config.get("language_code", "en")
    podcast_script_prompt = config.get("podcast_script_prompt")
    image_prompt = config.get("image_prompt")
    print(f"Generating podcast with enhanced config: {config.get('name', 'Unnamed')}")
    print(f"Prompt: {prompt}")
    print(f"Time range: {time_range_hours} hours")
    print(f"Limit: {limit_articles} articles")
    print(f"TTS Engine: {tts_engine}")
    print(f"Language: {language_code}")
    return generate_podcast_from_prompt_v2(
        prompt=prompt,
        openai_api_key=openai_api_key,
        tracking_db_path=tracking_db_path,
        podcasts_db_path=podcasts_db_path,
        output_dir=output_dir,
        tts_engine=tts_engine,
        language_code=language_code,
        podcast_script_prompt=podcast_script_prompt,
        image_prompt=image_prompt,
        debug=debug,
    )


def process_all_active_configs_v2(
    openai_api_key: str,
    tracking_db_path: Optional[str] = None,
    podcasts_db_path: Optional[str] = None,
    tasks_db_path: Optional[str] = None,
    output_dir: str = PODCAST_ASSETS_DIR,
    debug: bool = False,
) -> List[Dict[str, Any]]:
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if podcasts_db_path is None:
        podcasts_db_path = get_podcasts_db_path()
    if tasks_db_path is None:
        tasks_db_path = get_tasks_db_path()
    configs = get_all_podcast_configs(tasks_db_path, active_only=True)
    if not configs:
        print("WARNING: No active podcast configurations found")
        return [{"error": "No active podcast configurations found"}]
    results = []
    total_configs = len(configs)
    print(f"Processing {total_configs} active podcast configurations with enhanced pipeline...")
    for i, config in enumerate(configs, 1):
        config_id = config["id"]
        config_name = config["name"]
        print(f"\n[{i}/{total_configs}] Processing podcast configuration {config_id}: {config_name}")
        try:
            result = generate_podcast_from_config_v2(
                config_id=config_id,
                openai_api_key=openai_api_key,
                tracking_db_path=tracking_db_path,
                podcasts_db_path=podcasts_db_path,
                tasks_db_path=tasks_db_path,
                output_dir=output_dir,
                debug=debug,
            )
            result["config_id"] = config_id
            result["config_name"] = config_name
            results.append(result)
            if "error" not in result:
                stats = result.get("processing_stats", {})
                print(f"Success - Podcast ID: {result.get('podcast_id', 'Unknown')}")
                print(f"Sources: {stats.get('confirmed_results', 0)} articles processed")
                print(f"Images: {stats.get('images_generated', 0)} generated")
                print(f"Audio: {'Yes' if stats.get('audio_generated') else 'No'}")
            else:
                print(f"Failed: {result['error']}")
        except Exception as e:
            print(f"ERROR: Error generating podcast for config {config_id}: {e}")
            results.append({"config_id": config_id, "config_name": config_name, "error": str(e)})
    return results


def main():
    openai_api_key = load_api_key()
    tasks_db_path = get_tasks_db_path()
    if not openai_api_key:
        print("ERROR: No OpenAI API key provided. Please set OPENAI_API_KEY environment variable.")
        return 1
    output_dir = PODCAST_ASSETS_DIR
    debug = False
    print("Starting Enhanced Agent-Based Podcast Generation System")
    print("=" * 60)
    results = process_all_active_configs_v2(
        openai_api_key=openai_api_key,
        tasks_db_path=tasks_db_path,
        output_dir=output_dir,
        debug=debug,
    )
    print("\n" + "=" * 60)
    print("PODCAST GENERATION RESULTS SUMMARY")
    print("=" * 60)
    successful = 0
    failed = 0
    for result in results:
        config_id = result.get("config_id", "Unknown")
        config_name = result.get("config_name", "Unknown")
        if "error" in result:
            print(f"Config {config_id} ({config_name}): {result['error']}")
            failed += 1
        else:
            podcast_id = result.get("podcast_id", "Unknown")
            stats = result.get("processing_stats", {})
            print(f"Config {config_id} ({config_name}): Success")
            print(f"Podcast ID: {podcast_id}")
            print(f"Sources: {stats.get('confirmed_results', 0)} articles")
            print(f"Images: {stats.get('images_generated', 0)} generated")
            successful += 1
    print("=" * 60)
    print(f"FINAL STATS: {successful} successful, {failed} failed out of {len(results)} total")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
