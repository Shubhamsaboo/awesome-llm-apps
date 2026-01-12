#!/usr/bin/env python3
"""
Environment Validation Script for Awesome LLM Apps

This script checks if required dependencies are installed and API keys are
properly configured for each LLM provider. Run this to quickly identify
setup issues before running any of the example projects.

Usage:
    python scripts/validate_env.py
    python scripts/validate_env.py --provider openai
    python scripts/validate_env.py --check-packages
    python scripts/validate_env.py --verbose
"""

import os
import sys
import argparse
import importlib.util
from typing import Optional


# ANSI color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def colored(text: str, color: str) -> str:
    """Return colored text if terminal supports it."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.END}"
    return text


# LLM Provider configurations
LLM_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "env_vars": ["OPENAI_API_KEY"],
        "package": "openai",
        "docs_url": "https://platform.openai.com/api-keys",
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "env_vars": ["ANTHROPIC_API_KEY"],
        "package": "anthropic",
        "docs_url": "https://console.anthropic.com/settings/keys",
    },
    "google": {
        "name": "Google (Gemini)",
        "env_vars": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "package": "google-generativeai",
        "docs_url": "https://aistudio.google.com/apikey",
    },
    "groq": {
        "name": "Groq",
        "env_vars": ["GROQ_API_KEY"],
        "package": "groq",
        "docs_url": "https://console.groq.com/keys",
    },
    "cohere": {
        "name": "Cohere",
        "env_vars": ["COHERE_API_KEY"],
        "package": "cohere",
        "docs_url": "https://dashboard.cohere.com/api-keys",
    },
    "openrouter": {
        "name": "OpenRouter",
        "env_vars": ["OPENROUTER_API_KEY"],
        "package": None,
        "docs_url": "https://openrouter.ai/keys",
    },
    "together": {
        "name": "Together AI",
        "env_vars": ["TOGETHER_API_KEY", "TOGETHERAI_API_KEY"],
        "package": "together",
        "docs_url": "https://api.together.xyz/settings/api-keys",
    },
    "perplexity": {
        "name": "Perplexity",
        "env_vars": ["PERPLEXITY_API_KEY"],
        "package": None,
        "docs_url": "https://www.perplexity.ai/settings/api",
    },
    "mistral": {
        "name": "Mistral AI",
        "env_vars": ["MISTRAL_API_KEY"],
        "package": "mistralai",
        "docs_url": "https://console.mistral.ai/api-keys/",
    },
}

# Common supporting services used across projects
SUPPORTING_SERVICES = {
    "tavily": {
        "name": "Tavily (Web Search)",
        "env_vars": ["TAVILY_API_KEY"],
        "docs_url": "https://tavily.com/#api",
    },
    "serper": {
        "name": "Serper (Google Search)",
        "env_vars": ["SERPER_API_KEY"],
        "docs_url": "https://serper.dev/",
    },
    "exa": {
        "name": "Exa (Semantic Search)",
        "env_vars": ["EXA_API_KEY"],
        "docs_url": "https://exa.ai/",
    },
    "firecrawl": {
        "name": "Firecrawl (Web Scraping)",
        "env_vars": ["FIRECRAWL_API_KEY"],
        "docs_url": "https://firecrawl.dev/",
    },
    "elevenlabs": {
        "name": "ElevenLabs (Text-to-Speech)",
        "env_vars": ["ELEVENLABS_API_KEY"],
        "docs_url": "https://elevenlabs.io/",
    },
    "qdrant": {
        "name": "Qdrant (Vector Database)",
        "env_vars": ["QDRANT_API_KEY", "QDRANT_URL"],
        "docs_url": "https://qdrant.tech/",
    },
}

# Core packages commonly used across projects
CORE_PACKAGES = [
    ("python-dotenv", "dotenv"),
    ("streamlit", "streamlit"),
    ("requests", "requests"),
    ("pydantic", "pydantic"),
]


def check_package_installed(
    package_name: str, import_name: Optional[str] = None
) -> bool:
    """Check if a Python package is installed."""
    name_to_check = import_name or package_name.replace("-", "_")
    spec = importlib.util.find_spec(name_to_check)
    return spec is not None


def check_env_var(var_name: str) -> tuple[bool, Optional[str]]:
    """Check if an environment variable is set and return its value (masked)."""
    value = os.environ.get(var_name)
    if value:
        # Mask the value for security
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
        return True, masked
    return False, None


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{colored(text, Colors.BOLD)}")
    print("=" * 50)


def validate_provider(
    provider_key: str, provider_info: dict, verbose: bool = False
) -> bool:
    """Validate a single LLM provider's configuration."""
    name = provider_info["name"]
    env_vars = provider_info["env_vars"]
    package = provider_info.get("package")
    docs_url = provider_info.get("docs_url", "")

    # Check environment variables
    env_status = False
    for var in env_vars:
        is_set, masked_value = check_env_var(var)
        if is_set:
            env_status = True
            if verbose:
                print(f"  {colored('✓', Colors.GREEN)} {var}: {masked_value}")
            break

    if not env_status:
        print(f"  {colored('✗', Colors.RED)} API Key: Not configured")
        print(f"    Set one of: {', '.join(env_vars)}")
        if docs_url:
            print(f"    Get key at: {colored(docs_url, Colors.BLUE)}")

    # Check package installation
    pkg_status = True
    if package:
        pkg_status = check_package_installed(package)
        if verbose or not pkg_status:
            status = (
                colored("✓", Colors.GREEN) if pkg_status else colored("✗", Colors.RED)
            )
            print(
                f"  {status} Package '{package}': {'Installed' if pkg_status else 'Not installed'}"
            )
            if not pkg_status:
                print(f"    Install with: pip install {package}")

    return env_status


def validate_all_providers(verbose: bool = False) -> dict:
    """Validate all LLM providers and return results."""
    results = {"configured": [], "not_configured": []}

    print_header("LLM Provider Status")

    for key, info in LLM_PROVIDERS.items():
        name = info["name"]
        print(f"\n{colored(name, Colors.BOLD)}:")

        if validate_provider(key, info, verbose):
            results["configured"].append(name)
            if not verbose:
                print(f"  {colored('✓', Colors.GREEN)} Ready to use")
        else:
            results["not_configured"].append(name)

    return results


def validate_supporting_services(verbose: bool = False) -> dict:
    """Validate supporting services configuration."""
    results = {"configured": [], "not_configured": []}

    print_header("Supporting Services Status")

    for key, info in SUPPORTING_SERVICES.items():
        name = info["name"]
        env_vars = info["env_vars"]

        configured = False
        for var in env_vars:
            is_set, masked_value = check_env_var(var)
            if is_set:
                configured = True
                if verbose:
                    print(
                        f"{colored(name, Colors.BOLD)}: {colored('✓', Colors.GREEN)} {var}"
                    )
                break

        if configured:
            results["configured"].append(name)
        else:
            results["not_configured"].append(name)
            if verbose:
                print(
                    f"{colored(name, Colors.BOLD)}: {colored('✗', Colors.YELLOW)} Not configured (optional)"
                )

    if not verbose:
        if results["configured"]:
            print(
                f"\n{colored('Configured:', Colors.GREEN)} {', '.join(results['configured'])}"
            )
        if results["not_configured"]:
            print(
                f"{colored('Not configured (optional):', Colors.YELLOW)} {', '.join(results['not_configured'])}"
            )

    return results


def validate_core_packages() -> bool:
    """Validate core packages are installed."""
    print_header("Core Package Status")

    all_installed = True
    for package_name, import_name in CORE_PACKAGES:
        installed = check_package_installed(package_name, import_name)
        status = colored("✓", Colors.GREEN) if installed else colored("✗", Colors.RED)
        print(f"  {status} {package_name}")
        if not installed:
            all_installed = False
            print(f"    Install with: pip install {package_name}")

    return all_installed


def check_dotenv_file() -> bool:
    """Check if .env file exists in the current directory."""
    env_file = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_file):
        print(f"\n{colored('✓', Colors.GREEN)} .env file found in current directory")
        return True
    else:
        print(
            f"\n{colored('!', Colors.YELLOW)} No .env file found in current directory"
        )
        print(
            "  Tip: Create a .env file with your API keys or export them as environment variables"
        )
        return False


def print_summary(provider_results: dict, service_results: dict) -> None:
    """Print a summary of the validation results."""
    print_header("Summary")

    configured_providers = len(provider_results["configured"])
    total_providers = len(LLM_PROVIDERS)

    print(f"\nLLM Providers: {configured_providers}/{total_providers} configured")

    if provider_results["configured"]:
        print(
            f"  {colored('Ready:', Colors.GREEN)} {', '.join(provider_results['configured'])}"
        )

    if configured_providers == 0:
        print(f"\n{colored('⚠ No LLM providers configured!', Colors.RED)}")
        print("  You need at least one provider to run the example projects.")
        print("  Start by getting an API key from one of the providers listed above.")
    elif configured_providers < 3:
        print(
            f"\n{colored('Tip:', Colors.BLUE)} Configure more providers to try different examples."
        )
    else:
        print(
            f"\n{colored('✓ Great!', Colors.GREEN)} You have multiple providers configured."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Validate environment setup for Awesome LLM Apps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_env.py              # Run full validation
  python scripts/validate_env.py --provider openai  # Check specific provider
  python scripts/validate_env.py --check-packages   # Only check packages
  python scripts/validate_env.py --verbose          # Show detailed output
        """,
    )
    parser.add_argument(
        "--provider",
        "-p",
        choices=list(LLM_PROVIDERS.keys()),
        help="Check a specific LLM provider only",
    )
    parser.add_argument(
        "--check-packages",
        action="store_true",
        help="Only check if core packages are installed",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output including masked API key values",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    args = parser.parse_args()

    # Disable colors if requested
    if args.no_color:
        Colors.GREEN = Colors.YELLOW = Colors.RED = Colors.BLUE = Colors.BOLD = (
            Colors.END
        ) = ""

    print(colored("\n🔍 Awesome LLM Apps - Environment Validator\n", Colors.BOLD))

    # Try to load .env file if python-dotenv is available
    try:
        from dotenv import load_dotenv

        load_dotenv()
        if args.verbose:
            print(
                f"{colored('✓', Colors.GREEN)} Loaded environment variables from .env file\n"
            )
    except ImportError:
        if args.verbose:
            print(
                f"{colored('!', Colors.YELLOW)} python-dotenv not installed, using system environment only\n"
            )

    # Check-packages mode
    if args.check_packages:
        validate_core_packages()
        return

    # Single provider mode
    if args.provider:
        provider_info = LLM_PROVIDERS[args.provider]
        print(f"Checking {provider_info['name']}...")
        validate_provider(args.provider, provider_info, verbose=True)
        return

    # Full validation
    check_dotenv_file()
    provider_results = validate_all_providers(args.verbose)
    service_results = validate_supporting_services(args.verbose)
    validate_core_packages()
    print_summary(provider_results, service_results)

    print(
        f"\n{colored('For more information, visit:', Colors.BLUE)} https://github.com/Shubhamsaboo/awesome-llm-apps\n"
    )


if __name__ == "__main__":
    main()
