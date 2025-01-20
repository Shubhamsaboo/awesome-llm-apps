import re
import typing as t
from pathlib import Path
from composio import Action, ComposioToolSet


InputType = t.TypeVar("InputType")


def read_user_input(
    prompt: str,
    metavar: str,
    validator: t.Callable[[str], InputType],
) -> InputType:
    """Read user input."""
    while True:
        value = input(f"{prompt} > ")
        try:
            return validator(value)
        except Exception as e:
            print(f"Invalid value for `{metavar}` error parsing `{value}`; {e}")


def _github_repository_name_validator(name: str) -> t.Tuple[str, str]:
    """Validate github repository name."""
    if " " in name:
        raise ValueError()
    owner, name = name.split("/")
    return owner, name


def _create_github_issue_validator(owner: str, name: str) -> t.Callable[[str], str]:
    """Create a github issue validator."""

    def _github_issue_validator(value: str) -> str:
        """Validate github issue."""
        # Check if it's a file path
        if Path(value).resolve().exists():
            return Path(value).read_text(encoding="utf-8")

        if re.match(r"^\d+$", value):
            response_data = ComposioToolSet().execute_action(
                action=Action.GITHUB_GET_AN_ISSUE,
                params={
                    "owner": owner,
                    "repo": name,
                    "issue_number": int(value),
                },
            ).get("response_data")
            if response_data:
                return response_data["body"]
            else:
                raise ValueError("No issue found with the given issue number")

        # If neither a file nor issue ID, treat as direct description text
        return value

    return _github_issue_validator


def from_github() -> t.Tuple[str, str]:
    """Take input from github."""
    owner, name = read_user_input(
        prompt="Enter github repository name",
        metavar="github repository name",
        validator=_github_repository_name_validator,
    )
    return (
        f"{owner}/{name}",
        read_user_input(
            prompt="Enter github issue ID or description or path to the file containing description",
            metavar="github issue",
            validator=_create_github_issue_validator(
                owner=owner,
                name=name,
            ),
        ),
    )
