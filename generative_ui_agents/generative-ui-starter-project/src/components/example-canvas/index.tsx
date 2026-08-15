"use client";

import { useAgent } from "@copilotkit/react-core/v2";
import { TodoList } from "./todo-list";

export function ExampleCanvas() {
  const { agent } = useAgent();

  return (
    <div className="h-full overflow-y-auto bg-[--background]">
      <div className="max-w-4xl mx-auto px-8 py-10 h-full">
        <TodoList
          todos={agent.state?.todos || []}
          onUpdate={(updatedTodos) => agent.setState({ todos: updatedTodos })}
          isAgentRunning={agent.isRunning}
        />
      </div>
    </div>
  );
}
