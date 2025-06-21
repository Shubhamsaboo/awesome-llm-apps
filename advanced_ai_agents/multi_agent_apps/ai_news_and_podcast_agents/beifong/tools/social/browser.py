import os
from playwright.sync_api import sync_playwright
from tools.social.config import USER_DATA_DIR
from contextlib import contextmanager


def setup_session(TARGET_SITE):
    print("🔐 SESSION SETUP MODE")
    print(f"Opening browser with persistent profile at: {USER_DATA_DIR}")
    print(f"Please log in {TARGET_SITE} manually to establish your session")
    with sync_playwright() as playwright:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        browser_context = playwright.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        try:
            if browser_context.pages:
                page = browser_context.pages[0]
            else:
                page = browser_context.new_page()
            page.goto(TARGET_SITE)
            print("\n✅ Browser is now open. Please:")
            print("1. Log in to your account manually")
            print("2. Navigate through the site as needed")
            print("3. Press Ctrl+C in this terminal when you're done\n")
            try:
                while True:
                    page.wait_for_timeout(1000)
            except KeyboardInterrupt:
                print("\n🔑 Session saved! You can now run monitoring tasks with this session.")
        finally:
            browser_context.close()


def setup_session_multi(TARGET_SITES):
    print("🔐 MULTI-SITE SESSION SETUP MODE")
    print(f"Opening browser with persistent profile at: {USER_DATA_DIR}")
    print(f"Setting up sessions for {len(TARGET_SITES)} sites:")
    for i, site in enumerate(TARGET_SITES, 1):
        print(f"  {i}. {site}")
    with sync_playwright() as playwright:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        browser_context = playwright.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        try:
            pages = []
            for i, site in enumerate(TARGET_SITES):
                if i == 0 and browser_context.pages:
                    page = browser_context.pages[0]
                else:
                    page = browser_context.new_page()
                print(f"📂 Opening: {site}")
                page.goto(site)
                pages.append(page)

            print("\n✅ All sites opened in separate tabs. Please:")
            print("1. Log in to your accounts manually in each tab")
            print("2. Navigate through the sites as needed")
            print("3. Press Ctrl+C in this terminal when you're done\n")
            print("💡 Tip: Use Ctrl+Tab to switch between tabs")
            try:
                while True:
                    pages[0].wait_for_timeout(1000)
            except KeyboardInterrupt:
                print(f"\n🔑 Sessions saved for all {len(TARGET_SITES)} sites! " "You can now run monitoring tasks with these sessions.")
        finally:
            browser_context.close()


@contextmanager
def create_browser_context():
    with sync_playwright() as playwright:
        browser_context = playwright.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        try:
            if browser_context.pages:
                page = browser_context.pages[0]
            else:
                page = browser_context.new_page()
            yield browser_context, page
        finally:
            browser_context.close()