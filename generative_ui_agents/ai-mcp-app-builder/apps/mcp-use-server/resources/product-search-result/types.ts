import { z } from "zod";

export const propSchema = z.object({
  query: z.string().describe("The search query"),
  results: z.array(
    z.object({
      fruit: z.string().describe("Fruit name"),
      color: z.string().describe("Tailwind background color class"),
    }),
  ),
});

export type ProductSearchResultProps = z.infer<typeof propSchema>;

export type AccordionItemProps = {
  question: string;
  answer: string;
  isOpen: boolean;
  onToggle: () => void;
};
