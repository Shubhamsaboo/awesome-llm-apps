
from podcast_utils import fetch_url_with_curl, extract_text_from_html

url = "https://www.linkedin.com/posts/michaelmansard_monetization-subscriptionbusiness-outcome-share-7470739017278394369-RLTF/?utm_source=share&utm_medium=member_desktop&rcm=ACoAAAukpLsBCcIP7ycPgCOqjUJ-_u7JUkYEDaY"

try:
    print(f"Fetching URL: {url}")
    html = fetch_url_with_curl(url)
    print(f"HTML length: {len(html)}")
    
    text = extract_text_from_html(html)
    print(f"Extracted text (first 500 chars):\n{text[:500]}")
    
    if len(text) < 100:
        print("\nWARNING: Extracted text is very short. Scraper might have been blocked or content is dynamic.")
except Exception as e:
    print(f"Error: {e}")
