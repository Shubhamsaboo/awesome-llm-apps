from langgraph.graph import START, MessagesState, StateGraph
from langgraph.pregel import Pregel
from typing_extensions import Any, Literal, Optional, Type, TypeVar, Union, get_args, get_origin

from src.utils.swarm.handoff import get_handoff_destinations


class SwarmState(MessagesState):
    """State schema for the multi-agent swarm."""

    # NOTE: this state field is optional and is not expected to be provided by the user.
    # If a user does provide it, the graph will start from the specified active agent.
    # If active agent is typed as a `str`, we turn it into enum of all active agent names.
    active_agent: Optional[str]


StateSchema = TypeVar("StateSchema", bound=SwarmState)
StateSchemaType = Type[StateSchema]


def _update_state_schema_agent_names(
    state_schema: StateSchemaType, agent_names: list[str]
) -> StateSchemaType:
    """Update the state schema to use Literal with agent names for 'active_agent'."""

    active_agent_annotation = state_schema.__annotations__["active_agent"]

    # Check if the annotation is str or Optional[str]
    is_str_type = active_agent_annotation is str
    is_optional_str = (
        get_origin(active_agent_annotation) is Union and get_args(active_agent_annotation)[0] is str
    )

    # We only update if the 'active_agent' is a str or Optional[str]
    if not (is_str_type or is_optional_str):
        return state_schema

    updated_schema = type(
        f"{state_schema.__name__}",
        (state_schema,),
        {"__annotations__": {**state_schema.__annotations__}},
    )

    # Create the Literal type with agent names
    literal_type = Literal.__getitem__(tuple(agent_names))

    # If it was Optional[str], make it Optional[Literal[...]]
    if is_optional_str:
        updated_schema.__annotations__["active_agent"] = Optional[literal_type]
    else:
        updated_schema.__annotations__["active_agent"] = literal_type

    return updated_schema


def add_active_agent_router(
    builder: StateGraph,
    *,
    route_to: list[str],
    default_active_agent: str,
) -> StateGraph:
    """Add a router to the currently active agent to the StateGraph.

    Args:
        builder: The graph builder (StateGraph) to add the router to.
        route_to: A list of agent (node) names to route to.
        default_active_agent: Name of the agent to route to by default (if no agents are currently active).

    Returns:
        StateGraph with the router added.

    Example:
        ```python
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.prebuilt import create_react_agent
        from langgraph.graph import StateGraph
        from langgraph_swarm import SwarmState, create_handoff_tool, add_active_agent_router

        def add(a: int, b: int) -> int:
            '''Add two numbers'''
            return a + b

        alice = create_react_agent(
            "openai:gpt-4o",
            [add, create_handoff_tool(agent_name="Bob")],
            prompt="You are Alice, an addition expert.",
            name="Alice",
        )

        bob = create_react_agent(
            "openai:gpt-4o",
            [create_handoff_tool(agent_name="Alice", description="Transfer to Alice, she can help with math")],
            prompt="You are Bob, you speak like a pirate.",
            name="Bob",
        )

        checkpointer = InMemorySaver()
        workflow = (
            StateGraph(SwarmState)
            .add_node(alice, destinations=("Bob",))
            .add_node(bob, destinations=("Alice",))
        )
        # this is the router that enables us to keep track of the last active agent
        workflow = add_active_agent_router(
            builder=workflow,
            route_to=["Alice", "Bob"],
            default_active_agent="Alice",
        )

        # compile the workflow
        app = workflow.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "1"}}
        turn_1 = app.invoke(
            {"messages": [{"role": "user", "content": "i'd like to speak to Bob"}]},
            config,
        )
        turn_2 = app.invoke(
            {"messages": [{"role": "user", "content": "what's 5 + 7?"}]},
            config,
        )
        ```
    """
    channels = builder.schemas[builder.schema]
    if "active_agent" not in channels:
        raise ValueError("Missing required key 'active_agent' in in builder's state_schema")

    if default_active_agent not in route_to:
        raise ValueError(
            f"Default active agent '{default_active_agent}' not found in routes {route_to}"
        )

    def route_to_active_agent(state: dict):
        return state.get("active_agent", default_active_agent)

    builder.add_conditional_edges(START, route_to_active_agent, path_map=route_to)
    return builder


def create_swarm(
    agents: list[Pregel],
    *,
    default_active_agent: str,
    state_schema: StateSchemaType = SwarmState,
    config_schema: Type[Any] | None = None,
) -> StateGraph:
    """Create a multi-agent swarm.

    Args:
        agents: List of agents to add to the swarm
            An agent can be a LangGraph [CompiledStateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.CompiledStateGraph),
            a functional API [workflow](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint),
            or any other [Pregel](https://langchain-ai.github.io/langgraph/reference/pregel/#langgraph.pregel.Pregel) object.
        default_active_agent: Name of the agent to route to by default (if no agents are currently active).
        state_schema: State schema to use for the multi-agent graph.
        config_schema: An optional schema for configuration.
            Use this to expose configurable parameters via `swarm.config_specs`.

    Returns:
        A multi-agent swarm StateGraph.

    Example:
        ```python
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.prebuilt import create_react_agent
        from langgraph_swarm import create_handoff_tool, create_swarm

        def add(a: int, b: int) -> int:
            '''Add two numbers'''
            return a + b

        alice = create_react_agent(
            "openai:gpt-4o",
            [add, create_handoff_tool(agent_name="Bob")],
            prompt="You are Alice, an addition expert.",
            name="Alice",
        )

        bob = create_react_agent(
            "openai:gpt-4o",
            [create_handoff_tool(agent_name="Alice", description="Transfer to Alice, she can help with math")],
            prompt="You are Bob, you speak like a pirate.",
            name="Bob",
        )

        checkpointer = InMemorySaver()
        workflow = create_swarm(
            [alice, bob],
            default_active_agent="Alice"
        )
        app = workflow.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "1"}}
        turn_1 = app.invoke(
            {"messages": [{"role": "user", "content": "i'd like to speak to Bob"}]},
            config,
        )
        turn_2 = app.invoke(
            {"messages": [{"role": "user", "content": "what's 5 + 7?"}]},
            config,
        )
        ```
    """
    active_agent_annotation = state_schema.__annotations__.get("active_agent")
    if active_agent_annotation is None:
        raise ValueError("Missing required key 'active_agent' in state_schema")

    agent_names = [agent.name for agent in agents]
    state_schema = _update_state_schema_agent_names(state_schema, agent_names)
    builder = StateGraph(state_schema, config_schema)
    add_active_agent_router(
        builder,
        route_to=agent_names,
        default_active_agent=default_active_agent,
    )
    for agent in agents:
        builder.add_node(
            agent.name,
            agent,
            destinations=tuple(get_handoff_destinations(agent)),
        )

    return builder