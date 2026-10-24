"""Run with pytest; model replies are supplied locally without API calls."""

from pathlib import Path
from types import SimpleNamespace

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from utils import EMPTY, TicTacToeBoard


class PausingPlayer:
    def __init__(self, content):
        self.content = content

    def run(self, *args, **kwargs):
        # Stop after this turn so Streamlit's rerun cannot start another move.
        st.session_state.game_paused = True
        return SimpleNamespace(content=self.content)


def play_one_turn(content, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "unused-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "unused-test-key")
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")))
    app.session_state.game_started = True
    app.session_state.game_paused = False
    app.session_state.move_history = []
    app.session_state.game_board = TicTacToeBoard()
    app.session_state.player_x = PausingPlayer(content)
    app.session_state.player_o = PausingPlayer(content)
    app.run(timeout=30)
    assert not app.exception
    return app.session_state


@pytest.mark.parametrize("content", ["-1 2", "1 -2", "-1 -2", "-10 0"])
def test_negative_coordinates_do_not_place_a_different_move(content, monkeypatch):
    state = play_one_turn(content, monkeypatch)
    assert state.game_board.board == [[EMPTY] * 3 for _ in range(3)]
    assert state.game_board.current_player == "X"
    assert state.move_history == []


@pytest.mark.parametrize("content", ["1 2", "1, 2", "(1, 2)"])
def test_valid_coordinates_still_place_the_requested_move(content, monkeypatch):
    state = play_one_turn(content, monkeypatch)
    assert state.game_board.board[1][2] == "X"
    assert state.game_board.current_player == "O"
    assert len(state.move_history) == 1
    assert state.move_history[0]["move"] == "1,2"
