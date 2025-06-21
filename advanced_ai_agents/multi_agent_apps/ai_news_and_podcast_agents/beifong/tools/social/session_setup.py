from tools.social.browser import setup_session_multi

target_sites = [
    "https://x.com",
    "https://facebook.com"
]

if __name__ == "__main__":
    setup_session_multi(target_sites)