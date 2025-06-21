from agno.agent import Agent
from dotenv import load_dotenv
from db.agent_config_v2 import TOGGLE_UI_STATES

load_dotenv()


def ui_manager_run(
    agent: Agent,
    state_type: str,
    active: bool,
) -> str:
    """
    UI Manager that takes the state_type and active as input and updates the sessions UI state.
    Args:
        agent: The agent instance
        state_type: The state type to update
        active: The active state
    Returns:
        Response status
    """
    from services.internal_session_service import SessionService

    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    current_state = session["state"]
    current_state[state_type] = active
    all_ui_states = TOGGLE_UI_STATES
    for ui_state in all_ui_states:
        if ui_state != state_type:
            current_state[ui_state] = False
    SessionService.save_session(session_id, current_state)
    return f"Updated {state_type} to {active}{' and all other UI states to False' if all_ui_states else ''}."