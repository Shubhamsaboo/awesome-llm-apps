"""
Tic Tac Toe Battle
---------------------------------
This example shows how to build a Tic Tac Toe game where two AI agents play against each other.
The game features a referee agent coordinating between two player agents using different
language models.

Usage Examples:
---------------
1. Quick game with default settings:
   referee_agent = get_tic_tac_toe_referee()
   play_tic_tac_toe()

2. Game with debug mode off:
   referee_agent = get_tic_tac_toe_referee(debug_mode=False)
   play_tic_tac_toe(debug_mode=False)

The game integrates:
  - Multiple AI models (Claude, GPT-4, etc.)
  - Turn-based gameplay coordination
  - Move validation and game state management
"""

import sys
from pathlib import Path
from textwrap import dedent
from typing import Tuple

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)


def get_model_for_provider(provider: str, model_name: str):
    """
    Creates and returns the appropriate model instance based on the provider.

    Args:
        provider: The model provider (e.g., 'openai', 'google', 'anthropic', 'groq')
        model_name: The specific model name/ID

    Returns:
        An instance of the appropriate model class

    Raises:
        ValueError: If the provider is not supported
    """
    if provider == "openai":
        return OpenAIChat(id=model_name)
    elif provider == "google":
        return Gemini(id=model_name)
    elif provider == "anthropic":
        if model_name == "claude-3-5-sonnet":
            return Claude(id="claude-3-5-sonnet-20241022", max_tokens=8192)
        elif model_name == "claude-3-7-sonnet":
            return Claude(
                id="claude-3-7-sonnet-20250219",
                max_tokens=8192,
            )
        elif model_name == "claude-3-7-sonnet-thinking":
            return Claude(
                id="claude-3-7-sonnet-20250219",
                max_tokens=8192,
                thinking={"type": "enabled", "budget_tokens": 4096},
            )
        else:
            return Claude(id=model_name)
    elif provider == "groq":
        return Groq(id=model_name)
    else:
        raise ValueError(f"Unsupported model provider: {provider}")


def get_tic_tac_toe_players(
    model_x: str = "openai:gpt-4o",
    model_o: str = "openai:o3-mini",
    debug_mode: bool = True,
) -> Tuple[Agent, Agent]:
    """
    Returns an instance of the Tic Tac Toe Referee Agent that coordinates the game.

    Args:
        model_x: ModelConfig for player X
        model_o: ModelConfig for player O
        model_referee: ModelConfig for the referee agent
        debug_mode: Enable logging and debug features

    Returns:
        An instance of the configured Referee Agent
    """
    # Parse model provider and name
    provider_x, model_name_x = model_x.split(":")
    provider_o, model_name_o = model_o.split(":")

    # Create model instances using the helper function
    model_x = get_model_for_provider(provider_x, model_name_x)
    model_o = get_model_for_provider(provider_o, model_name_o)

    player_x = Agent(
        name="Player X",
        description=dedent("""\
        You are Player X in a Tic Tac Toe game. Your goal is to win by placing three X's in a row (horizontally, vertically, or diagonally).

        BOARD LAYOUT:
        - The board is a 3x3 grid with coordinates from (0,0) to (2,2)
        - Top-left is (0,0), bottom-right is (2,2)

        RULES:
        - You can only place X in empty spaces (shown as " " on the board)
        - Players take turns placing their marks
        - First to get 3 marks in a row (horizontal, vertical, or diagonal) wins
        - If all spaces are filled with no winner, the game is a draw

        YOUR RESPONSE:
        - Provide ONLY two numbers separated by a space (row column)
        - Example: "1 2" places your X in row 1, column 2
        - Choose only from the valid moves list provided to you

        STRATEGY TIPS:
        - Study the board carefully and make strategic moves
        - Block your opponent's potential winning moves
        - Create opportunities for multiple winning paths
        - Pay attention to the valid moves and avoid illegal moves
        """),
        model=model_x,
        debug_mode=debug_mode,
    )

    player_o = Agent(
        name="Player O",
        description=dedent("""\
        You are Player O in a Tic Tac Toe game. Your goal is to win by placing three O's in a row (horizontally, vertically, or diagonally).

        BOARD LAYOUT:
        - The board is a 3x3 grid with coordinates from (0,0) to (2,2)
        - Top-left is (0,0), bottom-right is (2,2)

        RULES:
        - You can only place X in empty spaces (shown as " " on the board)
        - Players take turns placing their marks
        - First to get 3 marks in a row (horizontal, vertical, or diagonal) wins
        - If all spaces are filled with no winner, the game is a draw

        YOUR RESPONSE:
        - Provide ONLY two numbers separated by a space (row column)
        - Example: "1 2" places your X in row 1, column 2
        - Choose only from the valid moves list provided to you

        STRATEGY TIPS:
        - Study the board carefully and make strategic moves
        - Block your opponent's potential winning moves
        - Create opportunities for multiple winning paths
        - Pay attention to the valid moves and avoid illegal moves
        """),
        model=model_o,
        debug_mode=debug_mode,
    )

    return player_x, player_o
