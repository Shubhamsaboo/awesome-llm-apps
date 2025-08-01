from src.utils.swarm.handoff import create_handoff_tool

handoff_to_reconnaissance = create_handoff_tool(agent_name="Reconnaissance", name="transfer_to_reconnaissance", description="Transfer to Reconnaissance")
handoff_to_planner = create_handoff_tool(agent_name="Planner", name="transfer_to_planner", description="Transfer to Planner")
handoff_to_summary = create_handoff_tool(agent_name="Summary", name="transfer_to_summary", description="Transfer to Summary")
handoff_to_initial_access = create_handoff_tool(agent_name="Initial_Access", name="transfer_to_initial_access", description="Transfer to Initial_Access")

