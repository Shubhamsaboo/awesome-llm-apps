import json
import os
import requests

try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


CONFIG_FILE = "config.json"


# ------------------ UTILS ------------------ #

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def get_api_key(config, key_name):
    key = config.get(key_name)
    if not key:
        key = input(f"Enter {key_name}: ").strip()
    return key


# ------------------ TESTERS ------------------ #

def test_openai(api_key):
    if not openai:
        print("❌ openai package not installed")
        return

    try:
        openai.api_key = api_key
        openai.models.list()
        print("✅ OpenAI API Key is VALID")
    except Exception as e:
        print("❌ OpenAI API FAILED")
        print(e)


def test_gemini(api_key):
    if not genai:
        print("❌ google-generativeai not installed")
        return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")
        model.generate_content("Ping")
        print("✅ Gemini API Key is VALID")
    except Exception as e:
        print("❌ Gemini API FAILED")
        print(e)


def test_groq(api_key):
    """
    Groq uses OpenAI-compatible API
    Docs: https://console.groq.com/docs
    """
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 1
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Groq API Key is VALID")
        else:
            print("❌ Groq API FAILED")
            print(response.text)

    except Exception as e:
        print("❌ Groq API Error")
        print(e)


def test_groq(api_key):
    """
    Groq API test (console.groq.com)
    Uses a currently supported model.
    """
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Groq API Key is VALID")
        else:
            print("❌ Groq API FAILED")
            print(response.text)

    except Exception as e:
        print("❌ Groq API Error")
        print(e)



def test_cloud_api(api_key):
    """
    Generic bearer-token cloud API test
    """
    try:
        response = requests.get(
            "https://httpbin.org/bearer",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Cloud API Key looks VALID")
        else:
            print("❌ Cloud API FAILED")
            print(response.text)

    except Exception as e:
        print("❌ Cloud API Error")
        print(e)


# ------------------ MENU ------------------ #

def menu():
    print("\n🔑 API KEY TESTER")
    print("1. Test OpenAI API")
    print("2. Test Gemini API")
    print("3. Test Groq API (console.groq.com)")
    print("4. Test Grok API (xAI)")
    print("5. Test Generic Cloud API")
    print("6. Exit")
    return input("Select option: ").strip()


def main():
    config = load_config()

    while True:
        choice = menu()

        if choice == "1":
            test_openai(get_api_key(config, "OPENAI_API_KEY"))

        elif choice == "2":
            test_gemini(get_api_key(config, "GEMINI_API_KEY"))

        elif choice == "3":
            test_groq(get_api_key(config, "GROQ_API_KEY"))

        elif choice == "4":
            test_grok(get_api_key(config, "GROK_API_KEY"))

        elif choice == "5":
            test_cloud_api(get_api_key(config, "CLOUD_API_KEY"))

        elif choice == "6":
            print("👋 Exiting")
            break

        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
