"use client";

import { TodoColumn } from "./todo-column";
import { Button } from "@/components/ui/button";

interface Todo {
  id: string;
  title: string;
  description: string;
  emoji: string;
  status: "pending" | "completed";
}

interface TodoListProps {
  todos: Todo[];
  onUpdate: (todos: Todo[]) => void;
  isAgentRunning: boolean;
}

export function TodoList({ todos, onUpdate, isAgentRunning }: TodoListProps) {
  const pendingTodos = todos.filter((t) => t.status === "pending");
  const completedTodos = todos.filter((t) => t.status === "completed");

  const toggleStatus = (todo: Todo) => {
    const updated = todos.map((t) =>
      t.id === todo.id
        ? {
            ...t,
            status: (t.status === "completed" ? "pending" : "completed") as
              | "pending"
              | "completed",
          }
        : t,
    );
    onUpdate(updated);
  };

  const deleteTodo = (todo: Todo) => {
    onUpdate(todos.filter((t) => t.id !== todo.id));
  };

  const updateTitle = (todoId: string, title: string) => {
    const updated = todos.map((t) => (t.id === todoId ? { ...t, title } : t));
    onUpdate(updated);
  };

  const updateDescription = (todoId: string, description: string) => {
    const updated = todos.map((t) =>
      t.id === todoId ? { ...t, description } : t,
    );
    onUpdate(updated);
  };

  const updateEmoji = (todoId: string, emoji: string) => {
    const updated = todos.map((t) => (t.id === todoId ? { ...t, emoji } : t));
    onUpdate(updated);
  };

  const addTodo = () => {
    const newTodo: Todo = {
      id: crypto.randomUUID(),
      title: "New Todo",
      description: "Add a description",
      emoji: "🎯",
      status: "pending",
    };
    onUpdate([...todos, newTodo]);
  };

  if (!todos || todos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <div className="text-5xl">✏️</div>
        <p className="text-base font-semibold text-[--foreground]">
          No todos yet
        </p>
        <p className="text-sm text-[--muted-foreground]">
          Create your first task to get started
        </p>
        <Button onClick={addTodo} disabled={isAgentRunning} className="mt-2">
          Add a task
        </Button>
      </div>
    );
  }

  return (
    <div className="flex gap-8 h-full">
      <TodoColumn
        title="To Do"
        todos={pendingTodos}
        emptyMessage="No pending todos"
        showAddButton
        onAddTodo={addTodo}
        onToggleStatus={toggleStatus}
        onDelete={deleteTodo}
        onUpdateTitle={updateTitle}
        onUpdateDescription={updateDescription}
        onUpdateEmoji={updateEmoji}
        isAgentRunning={isAgentRunning}
      />
      <TodoColumn
        title="Done"
        todos={completedTodos}
        emptyMessage="No completed todos yet"
        onToggleStatus={toggleStatus}
        onDelete={deleteTodo}
        onUpdateTitle={updateTitle}
        onUpdateDescription={updateDescription}
        onUpdateEmoji={updateEmoji}
        isAgentRunning={isAgentRunning}
      />
    </div>
  );
}
