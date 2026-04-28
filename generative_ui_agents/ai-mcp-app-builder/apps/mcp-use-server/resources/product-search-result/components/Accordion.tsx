import React, { useState } from "react";
import { AccordionItem } from "./AccordionItem";

export interface AccordionItemData {
  question: string;
  answer: string;
}

interface AccordionProps {
  items: AccordionItemData[];
}

export const Accordion: React.FC<AccordionProps> = ({ items }) => {
  const [openAccordionIndex, setOpenAccordionIndex] = useState<number | null>(
    null,
  );

  return (
    <div className="p-8 pt-4 border-t border-subtle mt-4">
      <div className="rounded-lg border border-default overflow-hidden">
        {items.map((item, index) => (
          <AccordionItem
            key={index}
            question={item.question}
            answer={item.answer}
            isOpen={openAccordionIndex === index}
            onToggle={() =>
              setOpenAccordionIndex(openAccordionIndex === index ? null : index)
            }
          />
        ))}
      </div>
    </div>
  );
};
