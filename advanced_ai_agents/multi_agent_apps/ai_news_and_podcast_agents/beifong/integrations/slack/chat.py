import os
import re
import sqlite3
import asyncio
import aiohttp
import json
from concurrent.futures import ThreadPoolExecutor
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from typing import Dict, List
from datetime import datetime
from db.config import get_slack_sessions_db_path

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])
# local url works but banner images won't work in slack unless it's https with proper domain
# you can use ngrok to port forward local url to https and replace this local url with ngrok url
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:7000")
executor = ThreadPoolExecutor(max_workers=10)
active_sessions: Dict[str, Dict] = {}
DB_PATH = get_slack_sessions_db_path()


def send_error_message(thread_key: str, error_message: str):
    print(f"Error for {thread_key}: {error_message}")
    asyncio.create_task(send_slack_message(thread_key, f"❌ {error_message}"))


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thread_sessions (
            thread_key TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_state (
            session_id TEXT PRIMARY KEY,
            state_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_session_mapping(thread_key: str, session_id: str, channel_id: str, user_id: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO thread_sessions (thread_key, session_id, channel_id, user_id, updated_at) VALUES (?, ?, ?, ?, ?)",
        (thread_key, session_id, channel_id, user_id, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_session_info(thread_key: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT session_id, channel_id, user_id FROM thread_sessions WHERE thread_key = ?",
        (thread_key,),
    )
    result = cursor.fetchone()
    conn.close()
    return result if result else None


def save_session_state(session_id: str, state_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if isinstance(state_data, str):
        json_data = state_data
    else:
        json_data = json.dumps(state_data)
    cursor.execute(
        "INSERT OR REPLACE INTO session_state (session_id, state_data, updated_at) VALUES (?, ?, ?)",
        (session_id, json_data, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_session_state(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT state_data FROM session_state WHERE session_id = ?", (session_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        try:
            return json.loads(result[0])
        except:
            return {}
    return {}


class PodcastAgentClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def create_session(self, session_id=None):
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {"session_id": session_id} if session_id else {}
                async with session.post(f"{self.base_url}/api/podcast-agent/session", json=payload) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            print(f"API create_session error: {e}")
            raise

    async def chat(self, session_id: str, message: str):
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {"session_id": session_id, "message": message}
                async with session.post(f"{self.base_url}/api/podcast-agent/chat", json=payload) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            print(f"API chat error: {e}")
            raise

    async def check_status(self, session_id: str, task_id=None):
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {"session_id": session_id}
                if task_id:
                    payload["task_id"] = task_id
                async with session.post(f"{self.base_url}/api/podcast-agent/status", json=payload) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            print(f"API check_status error: {e}")
            raise


api_client = PodcastAgentClient(API_BASE_URL)


def get_thread_key(message, is_dm=False):
    if is_dm:
        return f"dm_{message['channel']}_{message['user']}"
    else:
        return message.get("thread_ts", message["ts"])


async def get_or_create_session(thread_key: str, channel_id: str, user_id: str = None):
    session_info = get_session_info(thread_key)
    if not session_info:
        response = await api_client.create_session(thread_key)
        session_id = response["session_id"]
        save_session_mapping(thread_key, session_id, channel_id, user_id)
        print(f"Created new session: {session_id} for thread: {thread_key}")
        return session_id
    else:
        return session_info[0]


def run_async_in_thread(coro):
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    future = executor.submit(run)
    return future


async def poll_for_completion(session_id: str, thread_key: str, task_id=None):
    print(f"Starting polling for session: {session_id}, task: {task_id}")
    max_polls = 60
    poll_count = 0
    active_sessions[session_id] = {
        "thread_key": thread_key,
        "task_id": task_id,
        "start_time": datetime.now(),
    }
    try:
        while poll_count < max_polls:
            try:
                status_response = await api_client.check_status(session_id, task_id)
                if status_response.get("session_state"):
                    save_session_state(session_id, status_response.get("session_state"))
                if not status_response.get("is_processing", True):
                    await send_completion_message(thread_key, status_response)
                    break
                if poll_count % 10 == 0 and poll_count > 0:
                    process_type = status_response.get("process_type", "request")
                    await send_slack_message(
                        thread_key,
                        f"🔄 Still processing {process_type}... ({poll_count * 3}s elapsed)",
                    )
                await asyncio.sleep(3)
                poll_count += 1
            except Exception as e:
                print(f"Polling error: {e}")
                await send_slack_message(
                    thread_key,
                    "❌ Something went wrong while processing your request. Please try again.",
                )
                break
    finally:
        if session_id in active_sessions:
            del active_sessions[session_id]


def start_background_polling(session_id: str, thread_key: str, task_id=None):
    if session_id in active_sessions:
        print(f"Replacing existing poll for session: {session_id}")
    future = run_async_in_thread(poll_for_completion(session_id, thread_key, task_id))
    active_sessions[session_id] = {
        "thread_key": thread_key,
        "task_id": task_id,
        "future": future,
        "start_time": datetime.now(),
    }


async def send_completion_message(thread_key: str, status_response):
    response_text = status_response.get("response", "Task completed!")
    session_state = status_response.get("session_state")
    if session_state:
        try:
            state_data = json.loads(session_state) if isinstance(session_state, str) else session_state
            if state_data.get("show_sources_for_selection") and state_data.get("search_results"):
                await send_source_selection_blocks(thread_key, state_data, response_text)
            elif state_data.get("show_script_for_confirmation") and state_data.get("generated_script"):
                await send_script_confirmation_blocks(thread_key, state_data, response_text)
            elif state_data.get("show_banner_for_confirmation") and state_data.get("banner_url"):
                await send_banner_confirmation_blocks(thread_key, state_data, response_text)
            elif state_data.get("show_audio_for_confirmation") and state_data.get("audio_url"):
                await send_audio_confirmation_blocks(thread_key, state_data, response_text)
            elif state_data.get("podcast_generated"):
                await send_final_presentation_blocks(thread_key, state_data, response_text)
            else:
                await send_slack_message(thread_key, response_text)
        except Exception as e:
            print(f"Error parsing session state: {e}")
            await send_slack_message(thread_key, response_text)
    else:
        await send_slack_message(thread_key, response_text)


async def send_source_selection_blocks(thread_key: str, state_data: dict, response_text: str):
    sources = state_data.get("search_results", [])
    languages = state_data.get("available_languages", [{"code": "en", "name": "English"}])
    session_info = get_session_info(thread_key)
    if session_info:
        save_session_state(session_info[0], state_data)
    source_options = []
    for i, source in enumerate(sources[:10]):
        title = source.get("title", f"Source {i + 1}")
        if len(title) > 70:
            title = title[:67] + "..."
        source_options.append(
            {
                "text": {"type": "plain_text", "text": f"{i + 1}. {title}"},
                "value": str(i),
            }
        )
    language_options = []
    for lang in languages:
        language_options.append(
            {
                "text": {"type": "plain_text", "text": lang["name"]},
                "value": lang["code"],
            }
        )
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📋 Source Selection*\n{response_text}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Found *{len(sources)}* sources. Select the ones you'd like to use for your podcast:",
            },
        },
    ]
    if source_options:
        blocks.append(
            {
                "type": "section",
                "block_id": "source_selection_block",
                "text": {"type": "mrkdwn", "text": "*Select Sources:*"},
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "source_selection",
                    "options": source_options,
                    "initial_options": source_options,
                },
            }
        )
    if len(sources) > 10:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Showing first 10 sources. {len(sources) - 10} more available._",
                    }
                ],
            }
        )
    blocks.extend(
        [
            {
                "type": "section",
                "block_id": "language_selection_block",
                "text": {"type": "mrkdwn", "text": "*Select Language:*"},
                "accessory": {
                    "type": "static_select",
                    "action_id": "language_selection",
                    "placeholder": {"type": "plain_text", "text": "Choose language"},
                    "options": language_options,
                    "initial_option": language_options[0] if language_options else None,
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Confirm Selection"},
                        "style": "primary",
                        "action_id": "confirm_sources",
                        "value": thread_key,
                    }
                ],
            },
        ]
    )
    await send_slack_blocks(thread_key, blocks, "📋 Source Selection")


def format_script_for_slack_snippet(script_data) -> str:
    if isinstance(script_data, dict):
        lines = []
        title = script_data.get("title", "Podcast Script")
        lines.append(f"PODCAST: {title}")
        lines.append("=" * (len(title) + 10))
        lines.append("")
        sections = script_data.get("sections", [])
        for i, section in enumerate(sections):
            section_type = section.get("type", "Unknown").upper()
            section_title = section.get("title", "")
            if section_title:
                lines.append(f"SECTION [{section_type}] {section_title}")
            else:
                lines.append(f"SECTION [{section_type}]")
            lines.append("-" * 50)
            lines.append("")
            if section.get("dialog"):
                for j, dialog in enumerate(section["dialog"]):
                    speaker = dialog.get("speaker", "SPEAKER")
                    text = dialog.get("text", "")
                    lines.append(f"SPEAKER {speaker}:")
                    if len(text) > 70:
                        words = text.split()
                        current_line = "   "
                        for word in words:
                            if len(current_line + word) > 70:
                                lines.append(current_line)
                                current_line = "   " + word
                            else:
                                current_line += " " + word if current_line != "   " else word
                        if current_line.strip():
                            lines.append(current_line)
                    else:
                        lines.append(f"   {text}")
                    lines.append("")
            if i < len(sections) - 1:
                lines.append("")
        return "\n".join(lines)
    return str(script_data) if script_data else "Script content not available"


async def send_script_confirmation_blocks(thread_key: str, state_data: dict, response_text: str):
    script = state_data.get("generated_script", {})
    title = script.get("title", "Podcast Script") if isinstance(script, dict) else "Podcast Script"
    full_script_text = format_script_for_slack_snippet(script)
    if len(full_script_text) > 2500:
        full_script_text = full_script_text[:2400] + "\n\n... (script continues)\n\nFull script will be available after approval."
    section_count = len(script.get("sections", [])) if isinstance(script, dict) else 0
    dialog_count = 0
    if isinstance(script, dict) and script.get("sections"):
        for section in script["sections"]:
            dialog_count += len(section.get("dialog", []))
    header_text = f"*📝 Script Review*\n{response_text}\n\n*{title}*\nGenerated {section_count} sections with {dialog_count} dialogue exchanges"
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": header_text},
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"```{full_script_text}```"}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✅ Approve Script"},
                    "style": "primary",
                    "action_id": "approve_script",
                    "value": thread_key,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔄 Request Changes"},
                    "action_id": "request_script_changes",
                    "value": thread_key,
                },
            ],
        },
    ]
    await send_slack_blocks(thread_key, blocks, "📝 Script Review")


async def send_banner_confirmation_blocks(thread_key: str, state_data: dict, response_text: str):
    banner_url = state_data.get("banner_url")
    banner_images = state_data.get("banner_images", [])
    image_url = None
    if banner_images:
        image_url = f"{API_BASE_URL}/podcast_img/{banner_images[0]}"
    elif banner_url:
        image_url = f"{API_BASE_URL}/podcast_img/{banner_url}"
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🎨 Banner Review*\n{response_text}"},
        }
    ]
    if image_url:
        blocks.append({"type": "image", "image_url": image_url, "alt_text": "Podcast Banner"})
        if len(banner_images) > 1:
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Showing 1 of {len(banner_images)} generated banners_",
                        }
                    ],
                }
            )
    blocks.append(
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✅ Approve Banner"},
                    "style": "primary",
                    "action_id": "approve_banner",
                    "value": thread_key,
                }
            ],
        }
    )
    await send_slack_blocks(thread_key, blocks, "🎨 Banner Review")


async def send_audio_confirmation_blocks(thread_key: str, state_data: dict, response_text: str):
    audio_url = state_data.get("audio_url")
    full_audio_url = f"{API_BASE_URL}/audio/{audio_url}" if audio_url else None
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🎵 Audio Review*\n{response_text}"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Your podcast audio has been generated! 🎧\n\n_Note: Click the download link to listen to your podcast audio._",
            },
        },
    ]
    action_elements = []
    if full_audio_url:
        action_elements.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "⬇️ Download Audio"},
                "url": full_audio_url,
                "action_id": "download_audio",
            }
        )
    action_elements.append(
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "✅ Sounds Great!"},
            "style": "primary",
            "action_id": "approve_audio",
            "value": thread_key,
        }
    )
    blocks.append({"type": "actions", "elements": action_elements})
    await send_slack_blocks(thread_key, blocks, f"🎵 Audio Review")


async def send_final_presentation_blocks(thread_key: str, state_data: dict, response_text: str):
    script = state_data.get("generated_script", {})
    podcast_title = script.get("title") if isinstance(script, dict) else None
    if not podcast_title:
        podcast_title = state_data.get("podcast_info", {}).get("topic", "Your Podcast")
    audio_url = state_data.get("audio_url")
    banner_url = state_data.get("banner_url")
    banner_images = state_data.get("banner_images", [])
    full_audio_url = f"{API_BASE_URL}/audio/{audio_url}" if audio_url else None
    full_banner_url = None
    if banner_images:
        full_banner_url = f"{API_BASE_URL}/podcast_img/{banner_images[0]}"
    elif banner_url:
        full_banner_url = f"{API_BASE_URL}/podcast_img/{banner_url}"
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🎉 Podcast Complete!*\n{response_text}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{podcast_title}*\n\nYour podcast has been successfully created with all assets! 🎊",
            },
        },
    ]
    if full_banner_url:
        blocks.append(
            {
                "type": "image",
                "image_url": full_banner_url,
                "alt_text": f"Banner for {podcast_title}",
            }
        )
    action_elements = []
    if full_audio_url:
        action_elements.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "🎵 Download Audio"},
                "url": full_audio_url,
                "action_id": "download_final_audio",
            }
        )
    action_elements.append(
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "🎙️ Create New Podcast"},
            "style": "primary",
            "action_id": "new_podcast",
            "value": thread_key,
        }
    )
    blocks.append({"type": "actions", "elements": action_elements})
    await send_slack_blocks(thread_key, blocks, "🎉 Podcast Complete!")


async def send_slack_blocks(thread_key: str, blocks: list, fallback_text: str = "Interactive elements loaded"):
    try:
        session_info = get_session_info(thread_key)
        if not session_info:
            print(f"No session info found for thread: {thread_key}")
            return
        session_id, channel_id, user_id = session_info
        if thread_key.startswith("dm_"):
            app.client.chat_postMessage(channel=channel_id, blocks=blocks, text=fallback_text)
        else:
            app.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text=fallback_text,
                thread_ts=thread_key,
            )
        print(f"Sent interactive blocks to {thread_key}")
    except Exception as e:
        print(f"Error sending Slack blocks: {e}")
        await send_slack_message(
            thread_key,
            "Interactive elements failed to load. Please continue with text responses.",
        )


async def send_slack_message(thread_key: str, text: str):
    try:
        session_info = get_session_info(thread_key)
        if not session_info:
            print(f"No session info found for thread: {thread_key}")
            return
        session_id, channel_id, user_id = session_info
        if len(text) > 3800:
            chunks = [text[i : i + 3800] for i in range(0, len(text), 3800)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    if thread_key.startswith("dm_"):
                        app.client.chat_postMessage(channel=channel_id, text=chunk)
                    else:
                        app.client.chat_postMessage(channel=channel_id, text=chunk, thread_ts=thread_key)
                else:
                    if thread_key.startswith("dm_"):
                        app.client.chat_postMessage(channel=channel_id, text=f"...continued:\n{chunk}")
                    else:
                        app.client.chat_postMessage(
                            channel=channel_id,
                            text=f"...continued:\n{chunk}",
                            thread_ts=thread_key,
                        )
        else:
            if thread_key.startswith("dm_"):
                app.client.chat_postMessage(channel=channel_id, text=text)
            else:
                app.client.chat_postMessage(channel=channel_id, text=text, thread_ts=thread_key)
        print(f"Sent message to {thread_key}: {text[:50]}...")
    except Exception as e:
        print(f"Error sending Slack message: {e}")


def clean_text(text, bot_id):
    text = re.sub(f"<@{bot_id}>", "", text).strip()
    return text


def format_script_for_slack(script_data) -> List[str]:
    if isinstance(script_data, dict):
        chunks = []
        current_chunk = ""
        title = script_data.get("title", "Podcast Script")
        current_chunk += f"*{title}*\n\n"
        sections = script_data.get("sections", [])
        for i, section in enumerate(sections):
            section_text = f"*Section {i + 1}: {section.get('type', 'Unknown').title()}*"
            if section.get("title"):
                section_text += f" - {section['title']}"
            section_text += "\n\n"
            if section.get("dialog"):
                for dialog in section["dialog"]:
                    speaker = dialog.get("speaker", "Speaker")
                    text = dialog.get("text", "")
                    dialog_text = f"*{speaker}:* {text}\n\n"
                    if len(current_chunk + section_text + dialog_text) > 3500:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = section_text + dialog_text
                    else:
                        current_chunk += section_text + dialog_text
                    section_text = ""
            else:
                current_chunk += section_text
            current_chunk += "\n---\n\n"
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks if chunks else ["Script content could not be formatted."]
    elif isinstance(script_data, str):
        try:
            parsed_data = json.loads(script_data)
            if isinstance(parsed_data, dict):
                return format_script_for_slack(parsed_data)
        except (json.JSONDecodeError, TypeError):
            pass
        text = script_data
        if len(text) <= 3500:
            return [text]
        else:
            return [text[i : i + 3500] for i in range(0, len(text), 3500)]
    else:
        try:
            text = str(script_data)
            if len(text) <= 3500:
                return [text]
            else:
                return [text[i : i + 3500] for i in range(0, len(text), 3500)]
        except Exception as e:
            print(f"Error converting script data to string: {e}")
            return ["Error: Could not format script data for display."]


@app.action("source_selection")
def handle_source_selection(ack, body, logger):
    ack()


@app.action("language_selection")
def handle_language_selection(ack, body, logger):
    ack()


@app.action("confirm_sources")
def handle_confirm_sources(ack, body, client):
    ack()

    def process_confirmation():
        try:
            thread_key = body["actions"][0]["value"]
            user_id = body["user"]["id"]
            selected_sources = []
            selected_language = "en"
            if "state" in body and "values" in body["state"]:
                values = body["state"]["values"]
                if "source_selection_block" in values and "source_selection" in values["source_selection_block"]:
                    source_data = values["source_selection_block"]["source_selection"]
                    if "selected_options" in source_data and source_data["selected_options"]:
                        selected_sources = [int(opt["value"]) for opt in source_data["selected_options"]]
                if "language_selection_block" in values and "language_selection" in values["language_selection_block"]:
                    lang_data = values["language_selection_block"]["language_selection"]
                    if "selected_option" in lang_data and lang_data["selected_option"]:
                        selected_language = lang_data["selected_option"]["value"]
            session_info = get_session_info(thread_key)
            if not session_info:
                client.chat_postMessage(
                    channel=body["channel"]["id"],
                    thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                    text="❌ Session not found. Please start a new conversation.",
                )
                return
            session_id = session_info[0]
            state_data = get_session_state(session_id)
            languages = state_data.get("available_languages", [{"code": "en", "name": "English"}])
            language_name = next(
                (lang["name"] for lang in languages if lang["code"] == selected_language),
                "English",
            )
            sources = state_data.get("search_results", [])
            if selected_sources:
                source_indices = [str(i + 1) for i in selected_sources]
                selected_source_titles = [sources[i].get("title", f"Source {i + 1}") for i in selected_sources if i < len(sources)]
                message = f"I've selected sources {', '.join(source_indices)} and I want the podcast in {language_name}."
            else:
                source_indices = [str(i + 1) for i in range(len(sources))]
                selected_source_titles = [source.get("title", f"Source {i + 1}") for i, source in enumerate(sources)]
                message = f"I want the podcast in {language_name} using all available sources."
            try:
                confirmation_blocks = create_confirmation_blocks(
                    selected_sources,
                    selected_source_titles,
                    language_name,
                    len(sources),
                )
                client.chat_update(
                    channel=body["channel"]["id"],
                    ts=body["message"]["ts"],
                    blocks=confirmation_blocks,
                    text="✅ Selection Confirmed",
                )
                print(f"Updated interactive message to confirmation state for {thread_key}")
            except Exception as e:
                print(f"Error updating message: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                text=f"🔄 Processing your selection: {message}\n\n_Generating podcast script..._",
            )
            asyncio.run(process_source_confirmation(thread_key, message))
        except Exception as e:
            print(f"Error in confirm_sources: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                text="❌ Error processing your selection. Please try again.",
            )

    executor.submit(process_confirmation)


def create_confirmation_blocks(selected_sources, selected_source_titles, language_name, total_sources):
    if selected_sources:
        source_text = ""
        for i, (idx, title) in enumerate(zip(selected_sources, selected_source_titles)):
            if i < 3:
                short_title = title[:50] + "..." if len(title) > 50 else title
                source_text += f"• *{idx}.* {short_title}\n"
            elif i == 3:
                remaining = len(selected_sources) - 3
                source_text += f"• _...and {remaining} more sources_\n"
                break
        source_summary = f"*Selected {len(selected_sources)} of {total_sources} sources:*\n{source_text}"
    else:
        source_summary = f"*Selected all {total_sources} sources*"
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*✅ Selection Confirmed*\n_Your preferences have been saved and processing has started._",
            },
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": source_summary}},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Language:* {language_name} 🌐"},
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_Confirmed at {datetime.now().strftime('%H:%M')} • Processing script generation..._",
                }
            ],
        },
    ]
    return blocks


async def process_source_confirmation(thread_key: str, message: str):
    try:
        session_info = get_session_info(thread_key)
        if not session_info:
            return
        session_id = session_info[0]
        chat_response = await api_client.chat(session_id, message)
        if chat_response.get("is_processing"):
            task_id = chat_response.get("task_id")
            start_background_polling(session_id, thread_key, task_id)
        else:
            response_text = chat_response.get("response", "Selection processed!")
            await send_slack_message(thread_key, response_text)
    except Exception as e:
        print(f"Error processing source confirmation: {e}")
        await send_slack_message(thread_key, "❌ Error processing your selection. Please try again.")


@app.action("request_script_changes")
def handle_request_script_changes(ack, body, client):
    ack()

    def process_request():
        try:
            thread_key = body["actions"][0]["value"]
            change_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🔄 Changes Requested*\n_Please describe what changes you'd like to make to the script._",
                    },
                }
            ]
            try:
                client.chat_update(
                    channel=body["channel"]["id"],
                    ts=body["message"]["ts"],
                    blocks=change_blocks,
                    text="Changes Requested",
                )
            except Exception as e:
                print(f"Error updating script message: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                text="What specific changes would you like me to make to the script? For example:\n• Adjust the tone or style\n• Add more detail on certain topics\n• Change the dialogue flow\n• Modify the structure",
            )
        except Exception as e:
            print(f"Error in request_script_changes: {e}")

    executor.submit(process_request)


@app.action("approve_script")
def handle_approve_script(ack, body, client):
    ack()

    def process_approval():
        try:
            thread_key = body["actions"][0]["value"]
            approval_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*✅ Script Approved*\n_Script has been approved and banner generation is starting._",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Approved at {datetime.now().strftime('%H:%M')} • Processing banner generation..._",
                        }
                    ],
                },
            ]
            try:
                client.chat_update(
                    channel=body["channel"]["id"],
                    ts=body["message"]["ts"],
                    blocks=approval_blocks,
                    text="✅ Script Approved",
                )
            except Exception as e:
                print(f"Error updating script message: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                text="🔄 Script approved! Generating banner images...",
            )
            asyncio.run(process_approval_action(body, "I approve this script. It looks good!"))
        except Exception as e:
            print(f"Error in approve_script: {e}")

    executor.submit(process_approval)


@app.action("approve_banner")
def handle_approve_banner(ack, body, client):
    ack()

    def process_approval():
        try:
            thread_key = body["actions"][0]["value"]
            approval_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*✅ Banner Approved*\n_Banner has been approved and audio generation is starting._",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Approved at {datetime.now().strftime('%H:%M')} • Processing audio generation..._",
                        }
                    ],
                },
            ]
            try:
                client.chat_update(
                    channel=body["channel"]["id"],
                    ts=body["message"]["ts"],
                    blocks=approval_blocks,
                    text="✅ Banner Approved",
                )
            except Exception as e:
                print(f"Error updating banner message: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                text="🔄 Banner approved! Generating podcast audio...",
            )
            asyncio.run(process_approval_action(body, "I approve this banner. It looks good!"))
        except Exception as e:
            print(f"Error in approve_banner: {e}")

    executor.submit(process_approval)


@app.action("approve_audio")
def handle_approve_audio(ack, body, client):
    ack()

    def process_approval():
        try:
            thread_key = body["actions"][0]["value"]
            approval_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*✅ Audio Approved*\n_Audio has been approved and your podcast is being finalized._",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Approved at {datetime.now().strftime('%H:%M')} • Finalizing podcast..._",
                        }
                    ],
                },
            ]
            try:
                client.chat_update(
                    channel=body["channel"]["id"],
                    ts=body["message"]["ts"],
                    blocks=approval_blocks,
                    text="✅ Audio Approved",
                )
            except Exception as e:
                print(f"Error updating audio message: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                text="🔄 Audio approved! Finalizing your podcast...",
            )
            asyncio.run(process_approval_action(body, "The audio sounds great! I'm happy with the final podcast."))
        except Exception as e:
            print(f"Error in approve_audio: {e}")

    executor.submit(process_approval)


@app.action("new_podcast")
def handle_new_podcast(ack, body, client):
    ack()

    def start_new():
        try:
            old_thread_key = body["actions"][0]["value"]
            channel_id = body["channel"]["id"]
            user_id = body["user"]["id"]
            import time

            new_thread_key = f"new_{channel_id}_{user_id}_{int(time.time())}"
            client.chat_postMessage(
                channel=channel_id,
                text="🎙️ *Welcome to AI Podcast Studio!*\n\nI'll help you create a professional podcast from your trusted sources. What topic would you like to create a podcast about?",
            )
            print(f"Started new podcast conversation: {new_thread_key}")
        except Exception as e:
            print(f"Error starting new podcast: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                text="❌ Error starting new podcast. Please try sending a new message.",
            )

    executor.submit(start_new)


async def process_approval_action(body, approval_message: str):
    try:
        thread_key = body["actions"][0]["value"]
        app.client.chat_postMessage(
            channel=body["channel"]["id"],
            thread_ts=thread_key if not thread_key.startswith("dm_") else None,
            text=f"✅ {approval_message}\n🔄 Processing next step...",
        )
        session_info = get_session_info(thread_key)
        if not session_info:
            await send_slack_message(thread_key, "❌ Session not found.")
            return
        session_id = session_info[0]
        chat_response = await api_client.chat(session_id, approval_message)
        if chat_response.get("is_processing"):
            task_id = chat_response.get("task_id")
            start_background_polling(session_id, thread_key, task_id)
        else:
            response_text = chat_response.get("response", "Approved! Processing next step...")
            await send_slack_message(thread_key, response_text)
    except Exception as e:
        print(f"Error processing approval: {e}")
        await send_slack_message(thread_key, "❌ Error processing approval. Please try again.")


@app.event("app_mention")
def handle_app_mention(event, say, client):
    bot_info = client.auth_test()
    bot_id = bot_info["user_id"]
    user_input = clean_text(event["text"], bot_id)
    thread_key = event["ts"]
    channel_id = event["channel"]
    user_id = event["user"]

    def handle_async():
        asyncio.run(handle_user_message(thread_key, user_input, say, channel_id, user_id, is_mention=True))

    executor.submit(handle_async)


@app.message("")
def handle_message(message, say, client):
    if message.get("bot_id"):
        return
    if message.get("text", "").startswith("<@"):
        return
    user_input = message["text"]
    channel_type = message.get("channel_type", "")
    is_dm = channel_type == "im"
    channel_id = message["channel"]
    user_id = message["user"]
    thread_key = get_thread_key(message, is_dm)

    def handle_async():
        asyncio.run(handle_user_message(thread_key, user_input, say, channel_id, user_id, is_dm=is_dm))

    executor.submit(handle_async)


async def handle_user_message(
    thread_key: str,
    user_input: str,
    say,
    channel_id: str,
    user_id: str,
    is_mention=False,
    is_dm=False,
):
    try:
        session_id = await get_or_create_session(thread_key, channel_id, user_id)
        session_state = get_session_state(session_id)
        if session_state.get("podcast_generated") and session_state.get("stage") == "complete":
            script = session_state.get("generated_script", {})
            podcast_title = script.get("title") if isinstance(script, dict) else "Your Podcast"
            podcast_id = session_state.get("podcast_id", "")
            completion_queries = ["download", "script", "audio", "banner", "share", "link", "asset", "file"]
            is_asset_query = any(query in user_input.lower() for query in completion_queries)
            if is_asset_query:
                completion_message = (
                    f"🎉 *'{podcast_title}' is complete!*\n\n"
                    "💡 *Looking for your podcast assets?*\n"
                    "All download links and assets were provided in the completion message above. "
                    "Please scroll up to find:\n"
                    "• Audio download link\n"
                    "• Banner images\n"
                    "• Complete script\n"
                    f"• Podcast ID: `{podcast_id}`\n\n"
                    "To create a **new podcast**, please start a fresh chat with me. 🎙️"
                )
            else:
                completion_message = (
                    f"🎉 *'{podcast_title}' is complete!*\n\n"
                    "This podcast session has finished successfully. To create a new podcast:\n\n"
                    "• **Start a new chat** with me\n"
                    "• Each podcast needs a fresh conversation\n"
                    "• Your completed podcast assets remain available above\n\n"
                    "Ready to create another amazing podcast? 🎙️✨"
                )
            if not is_dm and not is_mention:
                say(text=completion_message, thread_ts=thread_key)
            else:
                say(text=completion_message)
            print(f"Session {session_id} is complete - prevented API call for: {user_input[:50]}...")
            return
        if session_id in active_sessions:
            active_session = active_sessions[session_id]
            start_time = active_session.get("start_time", datetime.now())
            elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
            current_stage = session_state.get("stage", "unknown")
            process_type = active_session.get("process_type", "your request")
            stage_messages = {
                "search": "🔍 Searching for relevant sources",
                "scraping": "📰 Gathering full content from sources",
                "script": "📝 Generating podcast script",
                "banner": "🎨 Creating banner images",
                "image": "🎨 Creating banner images",
                "audio": "🎵 Generating podcast audio",
            }
            stage_message = stage_messages.get(current_stage, f"🔄 Processing {process_type}")
            progress_message = (
                f"⏳ *Still working on your podcast...*\n\n"
                f"{stage_message}\n"
                f"⏱️ Running for {elapsed_minutes:.1f} minutes\n\n"
                f"_Please wait while I complete this step. This can take several minutes for high-quality results._"
            )
            if current_stage == "search":
                progress_message += "\n\n💡 *Currently:* Finding the best sources across multiple platforms"
            elif current_stage == "script":
                progress_message += "\n\n💡 *Currently:* Crafting engaging dialogue and content structure"
            elif current_stage in ["banner", "image"]:
                progress_message += "\n\n💡 *Currently:* Generating professional banner designs"
            elif current_stage == "audio":
                progress_message += "\n\n💡 *Currently:* Creating high-quality voice narration"
            if not is_dm and not is_mention:
                say(text=progress_message, thread_ts=thread_key)
            else:
                say(text=progress_message)
            print(f"Session {session_id} already processing ({current_stage}) - prevented API call for: {user_input[:50]}...")
            return
        print(f"Processing message for session {session_id}: {user_input[:50]}...")
        chat_response = await api_client.chat(session_id, user_input)
        if chat_response.get("response"):
            response_text = chat_response["response"]
            if not is_dm and not is_mention:
                say(text=response_text, thread_ts=thread_key)
            else:
                say(text=response_text)
        if chat_response.get("is_processing"):
            task_id = chat_response.get("task_id")
            start_background_polling(session_id, thread_key, task_id)
            processing_msg = "🔄 Processing your request... This may take a moment."
            if not is_dm and not is_mention:
                say(text=processing_msg, thread_ts=thread_key)
            else:
                say(text=processing_msg)
        else:
            await send_completion_message(thread_key, chat_response)
    except Exception as e:
        print(f"Error handling message: {e}")
        if "timeout" in str(e).lower():
            error_msg = "⏱️ Request timed out. The system might be busy. Please try again in a moment."
        elif "connection" in str(e).lower():
            error_msg = "🔌 Connection issue. Please check your connection and try again."
        else:
            error_msg = "❌ Sorry, I encountered an error processing your request. Please try again."
        if not is_dm and not is_mention:
            say(text=error_msg, thread_ts=thread_key)
        else:
            say(text=error_msg)


init_db()

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    print("⚡️ Podcast Bot is running! Press Ctrl+C to stop.")
    print(f"🎙️ Connected to API at: {API_BASE_URL}")
    handler.start()