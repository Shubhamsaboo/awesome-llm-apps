# Widget Interactivity

Widgets interact with the outside world using hooks from `mcp-use/react`. `useCallTool()` provides tool calling with built-in state management. `sendFollowUpMessage` from `useWidget()` triggers LLM conversation turns.

**Use `useCallTool()` for:** Creating items, updating data, triggering actions, submitting forms
**Use `sendFollowUpMessage` for:** Asking the AI to analyze, compare, summarize, or respond based on widget context

---

## useCallTool() Basics

`useCallTool()` provides a TanStack Query-like state machine for calling MCP tools:

```tsx
import { useCallTool } from "mcp-use/react";

const { callTool, callToolAsync, isPending, isSuccess, isError, data, error } =
  useCallTool("tool-name");

// Fire-and-forget with optional callbacks
callTool(
  { param: "value" },
  {
    onSuccess: (result) => console.log(result.structuredContent),
    onError: (err) => console.error(err),
    onSettled: () => hideSpinner(),
  },
);

// Or async/await
const result = await callToolAsync({ param: "value" });
```

**State flags:**

| Property        | Description                                                           |
| --------------- | --------------------------------------------------------------------- |
| `isPending`     | Tool is executing                                                     |
| `isSuccess`     | Succeeded — `data` is available                                       |
| `isError`       | Failed — `error` is available                                         |
| `isIdle`        | No call made yet                                                      |
| `callTool`      | Fire-and-forget; optional `onSuccess`/`onError`/`onSettled` callbacks |
| `callToolAsync` | Returns `Promise<CallToolResult>`                                     |

**Type inference:** When using `mcp-use dev`, types for tool names, inputs, and outputs are auto-generated to `.mcp-use/tool-registry.d.ts`. The hook is fully typed with autocomplete.

---

## Simple Button Action

```tsx
import {
  McpUseProvider,
  useWidget,
  useCallTool,
  type WidgetMetadata,
} from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Todo list with actions",
  props: z.object({
    todos: z.array(
      z.object({
        id: z.string(),
        title: z.string(),
        completed: z.boolean(),
      }),
    ),
  }),
  exposeAsTool: false,
};

export default function TodoList() {
  const { props, isPending: isLoading } = useWidget();
  const { callTool, isPending } = useCallTool("toggle-todo");

  if (isLoading) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div>
        {props.todos.map((todo) => (
          <div key={todo.id} style={{ display: "flex", gap: 8, padding: 8 }}>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() =>
                callTool({ id: todo.id, completed: !todo.completed })
              }
              disabled={isPending}
            />
            <span
              style={{
                textDecoration: todo.completed ? "line-through" : "none",
              }}
            >
              {todo.title}
            </span>
          </div>
        ))}
      </div>
    </McpUseProvider>
  );
}
```

**Corresponding tool:**

```typescript
server.tool(
  {
    name: "toggle-todo",
    description: "Toggle todo completion status",
    schema: z.object({
      id: z.string(),
      completed: z.boolean(),
    }),
  },
  async ({ id, completed }) => {
    await updateTodo(id, { completed });
    return text(`Todo ${completed ? "completed" : "uncompleted"}`);
  },
);
```

---

## Form Submission

`isPending` from `useCallTool` replaces manual `submitting` state:

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

export default function CreateItemWidget() {
  const { props, isPending: isLoading } = useWidget();
  const { callTool, isPending } = useCallTool("create-todo");
  const [title, setTitle] = useState("");

  if (isLoading) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    callTool(
      { title },
      {
        onSuccess: () => setTitle(""),
        onError: () => alert("Failed to create todo"),
      },
    );
  };

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="New todo..."
            disabled={isPending}
            style={{ padding: 8, width: 300, marginRight: 8 }}
          />
          <button type="submit" disabled={isPending}>
            {isPending ? "Creating..." : "Add Todo"}
          </button>
        </form>

        <div style={{ marginTop: 16 }}>
          {props.todos.map((todo) => (
            <div key={todo.id}>{todo.title}</div>
          ))}
        </div>
      </div>
    </McpUseProvider>
  );
}
```

**Corresponding tool:**

```typescript
server.tool(
  {
    name: "create-todo",
    schema: z.object({
      title: z.string().describe("Todo title"),
    }),
  },
  async ({ title }) => {
    const todo = await createTodo(title);
    return text(`Created todo: ${todo.title}`);
  },
);
```

---

## Delete Action

```tsx
const { callTool: deleteTodo, isPending: isDeleting } =
  useCallTool("delete-todo");

const handleDelete = (id: string) => {
  if (!confirm("Are you sure you want to delete this item?")) return;

  deleteTodo(
    { id },
    {
      onError: () => alert("Failed to delete item"),
    },
  );
};

return (
  <McpUseProvider autoSize>
    <div>
      {props.todos.map((todo) => (
        <div
          key={todo.id}
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: 8,
          }}
        >
          <span>{todo.title}</span>
          <button onClick={() => handleDelete(todo.id)} disabled={isDeleting}>
            Delete
          </button>
        </div>
      ))}
    </div>
  </McpUseProvider>
);
```

---

## Optimistic Updates

Update UI immediately, then call tool:

```tsx
import { useState, useEffect } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

interface Todo {
  id: string;
  title: string;
  completed: boolean;
}

export default function OptimisticWidget() {
  const { props, isPending: isLoading } = useWidget<{ todos: Todo[] }>();
  const { callToolAsync } = useCallTool("toggle-todo");
  const [todos, setTodos] = useState<Todo[]>([]);

  useEffect(() => {
    if (!isLoading && props.todos) {
      setTodos(props.todos);
    }
  }, [isLoading, props.todos]);

  const handleToggle = async (id: string) => {
    // Optimistic update
    setTodos((prev) =>
      prev.map((todo) =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo,
      ),
    );

    try {
      await callToolAsync({ id });
    } catch {
      // Revert on failure
      setTodos(props.todos);
      alert("Failed to update todo");
    }
  };

  if (isLoading) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div>
        {todos.map((todo) => (
          <div key={todo.id}>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => handleToggle(todo.id)}
            />
            {todo.title}
          </div>
        ))}
      </div>
    </McpUseProvider>
  );
}
```

---

## Action Buttons

Multiple actions per item — declare a hook for each tool:

```tsx
const { callTool: editItem } = useCallTool("edit-item");
const { callTool: duplicateItem } = useCallTool("duplicate-item");
const { callTool: archiveItem } = useCallTool("archive-item");
const { callTool: deleteItem } = useCallTool("delete-item");

return (
  <McpUseProvider autoSize>
    <div>
      {props.items.map((item) => (
        <div
          key={item.id}
          style={{ padding: 12, border: "1px solid #ddd", marginBottom: 8 }}
        >
          <h3>{item.title}</h3>
          <p>{item.description}</p>

          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => editItem({ id: item.id })}>Edit</button>
            <button onClick={() => duplicateItem({ id: item.id })}>
              Duplicate
            </button>
            <button onClick={() => archiveItem({ id: item.id })}>
              Archive
            </button>
            <button
              onClick={() => deleteItem({ id: item.id })}
              style={{ color: "red" }}
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  </McpUseProvider>
);
```

---

## Inline Editing

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

export default function EditableList() {
  const { props, isPending: isLoading } = useWidget();
  const { callToolAsync, isPending: isSaving } = useCallTool("update-item");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const startEdit = (id: string, currentValue: string) => {
    setEditingId(id);
    setEditValue(currentValue);
  };

  const saveEdit = async (id: string) => {
    try {
      await callToolAsync({ id, title: editValue });
      setEditingId(null);
    } catch {
      alert("Failed to save");
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  if (isLoading) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div>
        {props.items.map((item) => (
          <div key={item.id} style={{ padding: 8, display: "flex", gap: 8 }}>
            {editingId === item.id ? (
              <>
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  autoFocus
                />
                <button onClick={() => saveEdit(item.id)} disabled={isSaving}>
                  Save
                </button>
                <button onClick={cancelEdit}>Cancel</button>
              </>
            ) : (
              <>
                <span>{item.title}</span>
                <button onClick={() => startEdit(item.id, item.title)}>
                  Edit
                </button>
              </>
            )}
          </div>
        ))}
      </div>
    </McpUseProvider>
  );
}
```

---

## Batch Actions

Select multiple items and act on them:

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

export default function BatchActions() {
  const { props, isPending: isLoading } = useWidget();
  const { callTool: archiveItems, isPending: isArchiving } =
    useCallTool("archive-items");
  const { callTool: deleteItems, isPending: isDeleting } =
    useCallTool("delete-items");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const processing = isArchiving || isDeleting;

  const toggleSelection = (id: string) => {
    const newSelection = new Set(selectedIds);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedIds(newSelection);
  };

  const handleBatchArchive = () => {
    archiveItems(
      { ids: Array.from(selectedIds) },
      {
        onSuccess: () => setSelectedIds(new Set()),
        onError: () => alert("Failed to archive items"),
      },
    );
  };

  const handleBatchDelete = () => {
    deleteItems(
      { ids: Array.from(selectedIds) },
      {
        onSuccess: () => setSelectedIds(new Set()),
        onError: () => alert("Failed to delete items"),
      },
    );
  };

  if (isLoading) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div>
        {selectedIds.size > 0 && (
          <div
            style={{
              padding: 12,
              backgroundColor: "#f5f5f5",
              marginBottom: 16,
            }}
          >
            <span>{selectedIds.size} selected</span>
            <button
              onClick={handleBatchArchive}
              disabled={processing}
              style={{ marginLeft: 8 }}
            >
              Archive
            </button>
            <button
              onClick={handleBatchDelete}
              disabled={processing}
              style={{ marginLeft: 8 }}
            >
              Delete
            </button>
          </div>
        )}

        {props.items.map((item) => (
          <div key={item.id} style={{ padding: 8, display: "flex", gap: 8 }}>
            <input
              type="checkbox"
              checked={selectedIds.has(item.id)}
              onChange={() => toggleSelection(item.id)}
            />
            <span>{item.title}</span>
          </div>
        ))}
      </div>
    </McpUseProvider>
  );
}
```

**Corresponding tool:**

```typescript
server.tool(
  {
    name: "delete-items",
    schema: z.object({
      ids: z.array(z.string()).describe("Item IDs to delete"),
    }),
  },
  async ({ ids }) => {
    await Promise.all(ids.map((id) => deleteItem(id)));
    return text(`Deleted ${ids.length} items`);
  },
);
```

---

## Handling Tool Errors

Use `isError` and `error` from the hook instead of manual error state:

```tsx
const { callTool, isError, error, isPending } = useCallTool("some-tool");

return (
  <McpUseProvider autoSize>
    <div>
      {isError && (
        <div
          style={{
            padding: 12,
            backgroundColor: "#ffebee",
            color: "#c62828",
            marginBottom: 16,
          }}
        >
          {error instanceof Error ? error.message : "Action failed"}
        </div>
      )}

      <button
        onClick={() =>
          callTool({
            /* params */
          })
        }
        disabled={isPending}
      >
        Perform Action
      </button>
    </div>
  </McpUseProvider>
);
```

---

## Per-Item Loading States

For per-item loading when sharing one hook instance, track the active ID separately:

```tsx
const { callToolAsync } = useCallTool("process-item");
const [loadingId, setLoadingId] = useState<string | null>(null);

const handleAction = async (id: string) => {
  setLoadingId(id);
  try {
    await callToolAsync({ id });
  } catch {
    alert("Failed");
  } finally {
    setLoadingId(null);
  }
};

return (
  <McpUseProvider autoSize>
    <div>
      {props.items.map((item) => (
        <div key={item.id}>
          <span>{item.title}</span>
          <button
            onClick={() => handleAction(item.id)}
            disabled={loadingId === item.id}
          >
            {loadingId === item.id ? "Processing..." : "Process"}
          </button>
        </div>
      ))}
    </div>
  </McpUseProvider>
);
```

---

## Confirmation Dialogs

```tsx
const { callTool: deleteItem } = useCallTool("delete-item");

const handleDelete = (id: string, title: string) => {
  if (!confirm(`Are you sure you want to delete "${title}"?`)) return;

  deleteItem(
    { id },
    {
      onError: () => alert("Failed to delete"),
    },
  );
};
```

Or with a custom dialog:

```tsx
import { useState } from "react";
import { useCallTool } from "mcp-use/react";

const { callToolAsync } = useCallTool("delete-item");
const [confirmDialog, setConfirmDialog] = useState<{
  id: string;
  title: string;
} | null>(null);

const handleDeleteClick = (id: string, title: string) => {
  setConfirmDialog({ id, title });
};

const handleConfirmDelete = async () => {
  if (!confirmDialog) return;

  try {
    await callToolAsync({ id: confirmDialog.id });
    setConfirmDialog(null);
  } catch {
    alert("Failed to delete");
  }
};

return (
  <McpUseProvider autoSize>
    <div>
      {props.items.map((item) => (
        <div key={item.id}>
          <span>{item.title}</span>
          <button onClick={() => handleDeleteClick(item.id, item.title)}>
            Delete
          </button>
        </div>
      ))}

      {confirmDialog && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{ backgroundColor: "white", padding: 24, borderRadius: 8 }}
          >
            <h3>Confirm Delete</h3>
            <p>Delete "{confirmDialog.title}"?</p>
            <button onClick={handleConfirmDelete}>Delete</button>
            <button onClick={() => setConfirmDialog(null)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  </McpUseProvider>
);
```

---

## Triggering LLM Responses: `sendFollowUpMessage`

`sendFollowUpMessage` from `useWidget()` sends a message to the conversation and triggers a new LLM turn — as if the user typed it. Use this to let widget interactions drive the conversation.

```tsx
import { McpUseProvider, useWidget } from "mcp-use/react";

export default function AnalysisWidget() {
  const { props, isPending, sendFollowUpMessage } = useWidget();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <h2>Results for "{props.query}"</h2>
        {props.items.map((item) => (
          <div
            key={item.id}
            style={{ padding: 8, borderBottom: "1px solid #ddd" }}
          >
            <strong>{item.name}</strong> — ${item.price}
          </div>
        ))}

        <button
          onClick={() =>
            sendFollowUpMessage(
              `Compare the top 3 results for "${props.query}" and recommend the best one.`,
            )
          }
          style={{ marginTop: 16, padding: "8px 16px" }}
        >
          Ask AI to Compare
        </button>
      </div>
    </McpUseProvider>
  );
}
```

### Combining with `useCallTool`

A widget can use both — `useCallTool` for data mutations and `sendFollowUpMessage` for triggering LLM reasoning:

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

export default function TodoWidget() {
  const { props, isPending, state, setState, sendFollowUpMessage } =
    useWidget();
  const { callTool: toggleTodo } = useCallTool("toggle-todo");

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  const tasks = state?.tasks || props.tasks || [];
  const remaining = tasks.filter((t) => !t.completed).length;

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        {tasks.map((t) => (
          <div key={t.id} style={{ display: "flex", gap: 8, padding: 8 }}>
            <input
              type="checkbox"
              checked={t.completed}
              onChange={() => toggleTodo({ id: t.id, completed: !t.completed })}
            />
            {t.title}
          </div>
        ))}

        <button
          onClick={() =>
            sendFollowUpMessage(
              `I have ${remaining} tasks left. Help me prioritize them.`,
            )
          }
          style={{ marginTop: 16, padding: "8px 16px" }}
        >
          Ask AI to Prioritize
        </button>
      </div>
    </McpUseProvider>
  );
}
```

---

## Complete Example

```tsx
import { useState } from "react";
import {
  McpUseProvider,
  useWidget,
  useCallTool,
  type WidgetMetadata,
} from "mcp-use/react";
import { z } from "zod";

const propsSchema = z.object({
  todos: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      completed: z.boolean(),
    }),
  ),
});

type Props = z.infer<typeof propsSchema>;

export const widgetMetadata: WidgetMetadata = {
  description: "Interactive todo list",
  props: propsSchema,
  exposeAsTool: false,
};

export default function InteractiveTodoList() {
  const { props, isPending: isLoading } = useWidget<Props>();
  const { callTool: createTodo, isPending: isCreating } =
    useCallTool("create-todo");
  const { callTool: toggleTodo } = useCallTool("toggle-todo");
  const { callTool: deleteTodo } = useCallTool("delete-todo");
  const [newTodo, setNewTodo] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <McpUseProvider autoSize>
        <div>Loading todos...</div>
      </McpUseProvider>
    );
  }

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTodo.trim()) return;

    createTodo(
      { title: newTodo },
      {
        onSuccess: () => setNewTodo(""),
        onError: () => alert("Failed to create todo"),
      },
    );
  };

  const handleToggle = (id: string, completed: boolean) => {
    toggleTodo({ id, completed: !completed });
  };

  const handleDelete = (id: string) => {
    setDeletingId(id);
    deleteTodo(
      { id },
      {
        onError: () => alert("Failed to delete"),
        onSettled: () => setDeletingId(null),
      },
    );
  };

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <h2>Todos ({props.todos.length})</h2>

        <form onSubmit={handleCreate} style={{ marginBottom: 16 }}>
          <input
            type="text"
            value={newTodo}
            onChange={(e) => setNewTodo(e.target.value)}
            placeholder="New todo..."
            disabled={isCreating}
            style={{ padding: 8, width: 300, marginRight: 8 }}
          />
          <button type="submit" disabled={isCreating}>
            {isCreating ? "Adding..." : "Add"}
          </button>
        </form>

        <div>
          {props.todos.map((todo) => (
            <div
              key={todo.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: 8,
                borderBottom: "1px solid #eee",
              }}
            >
              <input
                type="checkbox"
                checked={todo.completed}
                onChange={() => handleToggle(todo.id, todo.completed)}
              />
              <span
                style={{
                  flex: 1,
                  textDecoration: todo.completed ? "line-through" : "none",
                  color: todo.completed ? "#999" : "inherit",
                }}
              >
                {todo.title}
              </span>
              <button
                onClick={() => handleDelete(todo.id)}
                disabled={deletingId === todo.id}
                style={{ color: "red" }}
              >
                {deletingId === todo.id ? "Deleting..." : "Delete"}
              </button>
            </div>
          ))}
        </div>

        {props.todos.length === 0 && (
          <p style={{ color: "#999", textAlign: "center" }}>No todos yet</p>
        )}
      </div>
    </McpUseProvider>
  );
}
```

---

## Best Practices

1. **Use `useCallTool` for built-in state management** - No need for manual `isPending`/`error` state
2. **Declare hooks at the top level** - One hook per tool name; React rules apply
3. **Use `callTool` for fire-and-forget** - Handle success/error via callbacks
4. **Use `callToolAsync` for sequential operations** - When you need to await results or chain calls
5. **Use `isError`/`error` from the hook** - Instead of manual error state for single-tool widgets
6. **Optimistic updates** - Update local state before the call, revert on error
7. **Confirm destructive actions** - Use confirm() for deletes
8. **Use `sendFollowUpMessage` for LLM reasoning** - When you want the AI to analyze, compare, or respond based on widget context rather than mutating data

---

## Next Steps

- **Style widgets** → [ui-guidelines.md](ui-guidelines.md)
- **Advanced patterns** → [advanced.md](advanced.md)
- **See examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)
