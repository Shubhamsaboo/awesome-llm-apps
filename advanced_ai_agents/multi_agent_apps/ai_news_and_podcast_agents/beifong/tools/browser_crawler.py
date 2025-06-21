from playwright.sync_api import sync_playwright
import newspaper
import time
from typing import Dict, List
from datetime import datetime


class PlaywrightScraper:
    def __init__(
        self,
        headless: bool = True,
        timeout: int = 20000,
        fresh_context_per_url: bool = False,
    ):
        self.headless = headless
        self.timeout = timeout
        self.fresh_context_per_url = fresh_context_per_url

    def scrape_urls(self, urls: List[str]) -> List[Dict]:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            if self.fresh_context_per_url:
                results = []
                for url in urls:
                    result = self._scrape_single_with_new_context(browser, url)
                    results.append(result)
            else:
                results = self._scrape_with_reused_page(browser, urls)
            browser.close()
            return results

    def _scrape_with_reused_page(self, browser, urls: List[str]) -> List[Dict]:
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.set_extra_http_headers(
            {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }
        )
        results = []
        try:
            for i, url in enumerate(urls):
                print(f"Scraping {i+1}/{len(urls)}")
                result = self._scrape_single_url(page, url)
                results.append(result)
                if i < len(urls) - 1:
                    time.sleep(1)
        finally:
            context.close()
        return results

    def _scrape_single_url(self, page, url: str) -> Dict:
        max_retries = 0
        for attempt in range(max_retries + 1):
            try:
                page.goto(url, wait_until="load", timeout=self.timeout)
                page.wait_for_selector("body", timeout=5000)
                page.wait_for_timeout(2000)
                final_url = page.url
                return self._parse_with_newspaper(url, final_url)
            except Exception as e:
                if attempt < max_retries:
                    print(f"Retry {attempt + 1} for {url}")
                    time.sleep(2**attempt)
                    continue
                else:
                    return {
                        "originalUrl": url,
                        "error": str(e),
                        "success": False,
                        "timestamp": datetime.now().isoformat(),
                    }

    def _scrape_single_with_new_context(self, browser, url: str) -> Dict:
        max_retries = 0
        for attempt in range(max_retries + 1):
            context = None
            try:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                )
                page = context.new_page()
                page.set_extra_http_headers(
                    {
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    }
                )
                page.goto(url, wait_until="load", timeout=self.timeout)
                page.wait_for_selector("body", timeout=5000)
                page.wait_for_timeout(2000)
                final_url = page.url
                return self._parse_with_newspaper(url, final_url)
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2**attempt)
                    continue
                else:
                    return {
                        "originalUrl": url,
                        "error": str(e),
                        "success": False,
                        "timestamp": datetime.now().isoformat(),
                    }
            finally:
                if context:
                    context.close()

    def _parse_with_newspaper(self, original_url: str, final_url: str) -> Dict:
        try:
            article = newspaper.article(final_url)
            return {
                "original_url": original_url,
                "final_url": final_url,
                "title": article.title or "",
                "authors": article.authors or [],
                "published_date": article.publish_date.isoformat() if article.publish_date else None,
                "full_text": article.text or "",
                "success": True,
            }
        except Exception as e:
            return {
                "original_url": original_url,
                "final_url": final_url,
                "error": f"Newspaper4k parsing failed: {str(e)}",
                "success": False,
            }


def create_browser_crawler(headless=True, timeout=20000, fresh_context_per_url=False):
    """Factory function to create a new PlaywrightScraper instance."""
    return PlaywrightScraper(
        headless=headless,
        timeout=timeout,
        fresh_context_per_url=fresh_context_per_url
    )