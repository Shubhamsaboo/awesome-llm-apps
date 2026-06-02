/**
 * Kanban board data layer for the Kanban Board demo.
 * Contains board/column/card types, templates, and CRUD operations.
 */

export type Priority = "low" | "medium" | "high";
export type BoardTemplate = "blank" | "software" | "marketing" | "personal";

export interface Card {
  id: string;
  title: string;
  description?: string;
  priority: Priority;
  tags: string[];
  dueDate?: string;
  createdAt: string;
}

export interface Column {
  id: string;
  name: string;
  color: string;
  cards: Card[];
}

export interface Board {
  id: string;
  name: string;
  columns: Column[];
}

export interface CardOperationResult {
  success: boolean;
  message: string;
  board?: Board;
  card?: Card;
}

const boards: Map<string, Board> = new Map();

function generateId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
}

function now(): string {
  return new Date().toISOString();
}

const TEMPLATES: Record<BoardTemplate, () => Column[]> = {
  blank: () => [
    { id: generateId("col"), name: "To Do", color: "#6366f1", cards: [] },
    { id: generateId("col"), name: "In Progress", color: "#f59e0b", cards: [] },
    { id: generateId("col"), name: "Done", color: "#22c55e", cards: [] },
  ],

  software: () => [
    {
      id: generateId("col"),
      name: "Backlog",
      color: "#6366f1",
      cards: [
        {
          id: generateId("card"),
          title: "Set up CI/CD pipeline",
          description: "Configure GitHub Actions",
          priority: "medium",
          tags: ["devops"],
          createdAt: now(),
        },
        {
          id: generateId("card"),
          title: "Add user authentication",
          description: "Implement OAuth2 login",
          priority: "high",
          tags: ["feature", "security"],
          createdAt: now(),
        },
      ],
    },
    {
      id: generateId("col"),
      name: "In Progress",
      color: "#f59e0b",
      cards: [
        {
          id: generateId("card"),
          title: "Design database schema",
          description: "Create ERD for user data",
          priority: "high",
          tags: ["database"],
          createdAt: now(),
        },
      ],
    },
    {
      id: generateId("col"),
      name: "Code Review",
      color: "#8b5cf6",
      cards: [
        {
          id: generateId("card"),
          title: "Refactor API endpoints",
          description: "Apply REST best practices",
          priority: "low",
          tags: ["refactor"],
          createdAt: now(),
        },
      ],
    },
    {
      id: generateId("col"),
      name: "Done",
      color: "#22c55e",
      cards: [
        {
          id: generateId("card"),
          title: "Project setup",
          description: "Init Next.js + TypeScript",
          priority: "high",
          tags: ["setup"],
          createdAt: now(),
        },
      ],
    },
  ],

  marketing: () => [
    {
      id: generateId("col"),
      name: "Ideas",
      color: "#ec4899",
      cards: [
        {
          id: generateId("card"),
          title: "Influencer partnerships",
          description: "Reach out to tech influencers",
          priority: "medium",
          tags: ["social"],
          createdAt: now(),
        },
        {
          id: generateId("card"),
          title: "Customer testimonials",
          description: "Compile video testimonials",
          priority: "low",
          tags: ["content"],
          createdAt: now(),
        },
      ],
    },
    {
      id: generateId("col"),
      name: "Planning",
      color: "#6366f1",
      cards: [
        {
          id: generateId("card"),
          title: "Q2 campaign strategy",
          description: "Define goals and budget",
          priority: "high",
          tags: ["strategy"],
          dueDate: "2026-04-01",
          createdAt: now(),
        },
      ],
    },
    {
      id: generateId("col"),
      name: "In Progress",
      color: "#f59e0b",
      cards: [
        {
          id: generateId("card"),
          title: "Blog: Industry trends",
          description: "Write 2000 word article",
          priority: "medium",
          tags: ["blog"],
          dueDate: "2026-01-20",
          createdAt: now(),
        },
      ],
    },
    {
      id: generateId("col"),
      name: "Completed",
      color: "#22c55e",
      cards: [
        {
          id: generateId("card"),
          title: "Social media calendar",
          description: "Plan January posts",
          priority: "high",
          tags: ["social"],
          createdAt: now(),
        },
      ],
    },
  ],

  personal: () => [
    {
      id: generateId("col"),
      name: "To Do",
      color: "#6366f1",
      cards: [
        {
          id: generateId("card"),
          title: "Grocery shopping",
          description: "Vegetables, milk, bread",
          priority: "medium",
          tags: ["errands"],
          createdAt: now(),
        },
        {
          id: generateId("card"),
          title: "Call dentist",
          description: "Schedule checkup",
          priority: "low",
          tags: ["health"],
          createdAt: now(),
        },
        {
          id: generateId("card"),
          title: "Read 'Atomic Habits'",
          description: "Finish remaining chapters",
          priority: "low",
          tags: ["reading"],
          createdAt: now(),
        },
      ],
    },
    {
      id: generateId("col"),
      name: "In Progress",
      color: "#f59e0b",
      cards: [
        {
          id: generateId("card"),
          title: "Learn Spanish",
          description: "Duolingo lesson 15",
          priority: "medium",
          tags: ["learning"],
          createdAt: now(),
        },
      ],
    },
    {
      id: generateId("col"),
      name: "Done",
      color: "#22c55e",
      cards: [
        {
          id: generateId("card"),
          title: "Morning workout",
          description: "30 min cardio",
          priority: "high",
          tags: ["fitness"],
          createdAt: now(),
        },
      ],
    },
  ],
};

export function createBoard(
  name: string,
  template: BoardTemplate = "blank",
): Board {
  const id = generateId("board");
  const board: Board = { id, name, columns: TEMPLATES[template]() };
  boards.set(id, board);
  return board;
}

export function getBoard(boardId: string): Board | undefined {
  return boards.get(boardId);
}

export function addCard(
  boardId: string,
  columnId: string,
  card: Omit<Card, "id" | "createdAt">,
): CardOperationResult {
  const board = boards.get(boardId);
  if (!board) return { success: false, message: "Board not found" };
  const column = board.columns.find((c) => c.id === columnId);
  if (!column) return { success: false, message: "Column not found" };
  const newCard: Card = { ...card, id: generateId("card"), createdAt: now() };
  column.cards.push(newCard);
  return {
    success: true,
    message: `Added "${card.title}" to ${column.name}`,
    board,
    card: newCard,
  };
}

export function updateCard(
  boardId: string,
  cardId: string,
  updates: Partial<Omit<Card, "id" | "createdAt">>,
): CardOperationResult {
  const board = boards.get(boardId);
  if (!board) return { success: false, message: "Board not found" };
  for (const column of board.columns) {
    const idx = column.cards.findIndex((c) => c.id === cardId);
    if (idx !== -1) {
      column.cards[idx] = { ...column.cards[idx], ...updates };
      return {
        success: true,
        message: `Updated "${column.cards[idx].title}"`,
        board,
        card: column.cards[idx],
      };
    }
  }
  return { success: false, message: "Card not found" };
}

export function deleteCard(
  boardId: string,
  cardId: string,
): CardOperationResult {
  const board = boards.get(boardId);
  if (!board) return { success: false, message: "Board not found" };
  for (const column of board.columns) {
    const idx = column.cards.findIndex((c) => c.id === cardId);
    if (idx !== -1) {
      const [deleted] = column.cards.splice(idx, 1);
      return {
        success: true,
        message: `Deleted "${deleted.title}"`,
        board,
        card: deleted,
      };
    }
  }
  return { success: false, message: "Card not found" };
}

export function moveCard(
  boardId: string,
  cardId: string,
  targetColumnId: string,
  position?: number,
): CardOperationResult {
  const board = boards.get(boardId);
  if (!board) return { success: false, message: "Board not found" };
  const targetColumn = board.columns.find((c) => c.id === targetColumnId);
  if (!targetColumn)
    return { success: false, message: "Target column not found" };

  let card: Card | undefined;
  for (const column of board.columns) {
    const idx = column.cards.findIndex((c) => c.id === cardId);
    if (idx !== -1) {
      [card] = column.cards.splice(idx, 1);
      break;
    }
  }
  if (!card) return { success: false, message: "Card not found" };

  const pos =
    position !== undefined
      ? Math.min(position, targetColumn.cards.length)
      : targetColumn.cards.length;
  targetColumn.cards.splice(pos, 0, card);
  return {
    success: true,
    message: `Moved "${card.title}" to ${targetColumn.name}`,
    board,
    card,
  };
}
