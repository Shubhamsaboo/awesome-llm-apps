"use client";

import { TodoCard } from "./todo-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

interface Todo {
  id: string;
  title: string;
  description: string;
  emoji: string;
  status: "pending" | "completed";
}

interface TodoColumnProps {
  title: string;
  todos: Todo[];
  emptyMessage: string;
  showAddButton?: boolean;
  onAddTodo?: () => void;
  onToggleStatus: (todo: Todo) => void;
  onDelete: (todo: Todo) => void;
  onUpdateTitle: (todoId: string, title: string) => void;
  onUpdateDescription: (todoId: string, description: string) => void;
  onUpdateEmoji: (todoId: string, emoji: string) => void;
  isAgentRunning: boolean;
}

export function TodoColumn({
  title,
  todos,
  emptyMessage,
  showAddButton = false,
  onAddTodo,
  onToggleStatus,
  onDelete,
  onUpdateTitle,
  onUpdateDescription,
  onUpdateEmoji,
  isAgentRunning,
}: TodoColumnProps) {
  return (
    <section aria-label={`${title} column`} className="flex-1 min-w-0">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold tracking-tight text-[var(--foreground)]">
            {title}
          </h2>
          <Badge variant="secondary">{todos.length}</Badge>
        </div>
        {showAddButton && onAddTodo && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onAddTodo}
            disabled={isAgentRunning}
            aria-label="Add new todo"
          >
            <Plus className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Cards */}
      <div className="space-y-3">
        {todos.length === 0 ? (
          <div className="text-center text-sm rounded-[var(--radius)] border-2 border-dashed border-[var(--border)] p-5 min-h-[151px] flex items-center justify-center text-[var(--muted-foreground)]">
            {emptyMessage}
          </div>
        ) : (
          todos.map((todo) => (
            <TodoCard
              key={todo.id}
              todo={todo}
              onToggleStatus={onToggleStatus}
              onDelete={onDelete}
              onUpdateTitle={onUpdateTitle}
              onUpdateDescription={onUpdateDescription}
              onUpdateEmoji={onUpdateEmoji}
            />
          ))
        )}
      </div>
    </section>
  );
}
