import os
import asyncio
import inspect
from typing import AsyncGenerator, Dict, Any

from dotenv import load_dotenv
from google.adk.agents import LlmAgent, LoopAgent
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.events import Event, EventActions
from google.genai import types


# Load environment variables
load_dotenv()


# ------------------------------------------------------------
# Sub-agent 1: LLM refiner that improves the plan each iteration
# ------------------------------------------------------------
plan_refiner = LlmAgent(
    name="plan_refiner",
    model="gemini-3-flash-preview",
    description="Iteratively refines a brief product/launch plan given topic and prior context",
    instruction=(
        "You are an iterative planner. On each turn:\n"
        "- Improve and tighten the current plan for the topic in session state\n"
        "- Keep it concise (5-8 bullets) and avoid repeating prior text verbatim\n"
        "- Incorporate clarity, feasibility, and crisp sequencing\n"
        "- Assume this output will be refined again in subsequent iterations\n\n"
        "Output format:\n"
        "Title line\n"
        "- Bullet 1\n- Bullet 2\n- Bullet 3 ..."
    ),
)


# ------------------------------------------------------------
# Sub-agent 2: Progress tracker increments iteration counter
# ------------------------------------------------------------
class IncrementIteration(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        current_iteration = int(ctx.session.state.get("iteration", 0)) + 1
        ctx.session.state["iteration"] = current_iteration
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        text=f"Iteration advanced to {current_iteration}"
                    )
                ],
            ),
        )


# ------------------------------------------------------------
# Sub-agent 3: Completion check with optional early stop
# - Stops if iteration >= target_iterations OR session flag 'accepted' is True
# ------------------------------------------------------------
class CheckCompletion(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        target_iterations = int(ctx.session.state.get("target_iterations", 3))
        current_iteration = int(ctx.session.state.get("iteration", 0))
        accepted = bool(ctx.session.state.get("accepted", False))

        reached_limit = current_iteration >= target_iterations
        should_stop = accepted or reached_limit

        yield Event(
            author=self.name,
            actions=EventActions(escalate=should_stop),
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        text=(
                            "Stopping criteria met"
                            if should_stop
                            else "Continuing loop"
                        )
                    )
                ],
            ),
        )


increment_iteration = IncrementIteration(name="increment_iteration")
check_completion = CheckCompletion(name="check_completion")


# ------------------------------------------------------------
# LoopAgent: Executes sub-agents sequentially in a loop
# - Termination: max_iterations, or CheckCompletion escalates
# - Context & State: Same InvocationContext across iterations
# ------------------------------------------------------------
spec_refinement_loop = LoopAgent(
    name="spec_refinement_loop",
    description=(
        "Iteratively refines a plan using LLM, tracks iterations, and stops when target iterations "
        "are reached or an 'accepted' flag is set in session state."
    ),
    max_iterations=10,
    sub_agents=[
        plan_refiner,
        increment_iteration,
        check_completion,
    ],
)


# ------------------------------------------------------------
# Runner setup
# ------------------------------------------------------------
session_service = InMemorySessionService()
runner = Runner(
    agent=spec_refinement_loop,
    app_name="loop_refinement_app",
    session_service=session_service,
)


# ------------------------------------------------------------
# Public API: run the loop refinement for a topic
# ------------------------------------------------------------
async def iterate_spec_until_acceptance(
    user_id: str, topic: str, target_iterations: int = 3
) -> Dict[str, Any]:
    """Run the LoopAgent to iteratively refine a plan.

    Returns a dictionary with final plan text and iteration metadata.
    """
    session_id = f"loop_refinement_{user_id}"

    async def _maybe_await(value):
        return await value if inspect.isawaitable(value) else value

    # Create or get session (support both sync/async services)
    session = await _maybe_await(session_service.get_session(
        app_name="loop_refinement_app",
        user_id=user_id,
        session_id=session_id,
    ))
    if not session:
        session = await _maybe_await(session_service.create_session(
            app_name="loop_refinement_app",
            user_id=user_id,
            session_id=session_id,
            state={
                "topic": topic,
                "iteration": 0,
                "target_iterations": int(target_iterations),
                # Optionally, an external process or UI could set this to True to stop early
                "accepted": False,
            },
        ))
    else:
        # Refresh topic/target if user re-runs on UI
        if hasattr(session, "state") and isinstance(session.state, dict):
            session.state["topic"] = topic
            session.state["target_iterations"] = int(target_iterations)

    # Seed message for LLM
    user_content = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Topic: "
                    + topic
                    + "\nPlease produce or refine a concise plan."
                )
            )
        ],
    )

    final_text = ""
    last_plan_text = ""
    stream = runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content)
    # Support both async generators and plain iterables
    if inspect.isasyncgen(stream):
        async for event in stream:
            if event.content and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        # Keep last text from plan_refiner preferentially
                        if getattr(event, "author", "") == plan_refiner.name:
                            last_plan_text = part.text
                        if event.is_final_response():
                            final_text = part.text
    else:
        for event in stream:
            if event.content and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        if getattr(event, "author", "") == plan_refiner.name:
                            last_plan_text = part.text
                        # final events in sync mode
                        final_text = part.text
        if event.content and getattr(event.content, "parts", None):
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    # Keep last text from plan_refiner preferentially
                    if getattr(event, "author", "") == plan_refiner.name:
                        last_plan_text = part.text
                    if event.is_final_response():
                        final_text = part.text

    current_iteration = int(session.state.get("iteration", 0))
    reached = current_iteration >= int(session.state.get("target_iterations", 0))
    accepted = bool(session.state.get("accepted", False))

    return {
        "final_plan": last_plan_text or final_text,
        "iterations": current_iteration,
        "stopped_reason": "accepted" if accepted else ("target_iterations" if reached else "max_iterations_or_other"),
    }


