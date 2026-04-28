import { Animate } from "@openai/apps-sdk-ui/components/Transition";
import React from "react";
import type { AccordionItemProps } from "../types";

export const AccordionItem: React.FC<AccordionItemProps> = ({
  question,
  answer,
  isOpen,
  onToggle,
}) => {
  return (
    <div className="border-b border-subtle last:border-b-0">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-primary-soft-hover transition-colors"
      >
        <span className="font-medium text-default">{question}</span>
        <span className="text-xl text-tertiary transition-transform duration-200">
          {isOpen ? "−" : "+"}
        </span>
      </button>
      <Animate enter={{ y: 0, delay: 150, duration: 450 }} exit={{ y: -8 }}>
        {isOpen && (
          <div key="content" className="pb-4 text-secondary px-4">
            {answer}
          </div>
        )}
      </Animate>
    </div>
  );
};
