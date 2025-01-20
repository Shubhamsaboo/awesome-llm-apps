from composio import action
import requests
import os

@action(toolname="github")
def create_pr(owner: str, repo: str, head: str, base: str, title: str) -> dict:
    """
    Create a GitHub pull request using the REST API.

    :param owner: Owner of the repository
    :param repo: Name of the repository
    :param head: Branch containing the changes
    :param base: Branch to merge into
    :param title: Title of the pull request

    :return response: Response from GitHub API containing PR details
    """
    # Get GitHub token from environment
    github_token = os.getenv('GITHUB_ACCESS_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_ACCESS_TOKEN environment variable not set")

    # API endpoint for creating a PR
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

    # Headers for authentication and API version
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # PR data
    data = {
        "title": title,
        "head": head,
        "base": base
    }

    # Make the API request
    response = requests.post(url, headers=headers, json=data)
    
    # Check if request was successful
    response.raise_for_status()
    
    return response.json()
