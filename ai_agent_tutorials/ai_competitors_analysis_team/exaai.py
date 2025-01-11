from exa_py import Exa

# Initialize Exa with your API key
exa = Exa(api_key="EXA_API_KEY")

def get_competitor_urls(url=None, description=None):
    if url:
        # Use the URL-based API call
        result = exa.find_similar(
            url=url,
            num_results=5,
            exclude_source_domain=True,
            category="company"
        )
    elif description:
        # Use the description-based API call
        result = exa.search(
            description,
            type="neural",
            category="company",
            use_autoprompt=True,
            num_results=5
        )
    else:
        raise ValueError("Please provide either a URL or a description.")
    
    # Extracting and return only the competitor URLs
    competitor_urls = [item.url for item in result.results]
    return competitor_urls
    # return result

print(get_competitor_urls(description="Competitors of a company that works on AI Neuro Health Tech"))