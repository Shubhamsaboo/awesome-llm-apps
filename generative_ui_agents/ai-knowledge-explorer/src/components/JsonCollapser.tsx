"use client";

import { useEffect } from "react";

export function JsonCollapser() {
  useEffect(() => {
    const tag = () => {
      const chatArea = document.querySelector("[data-copilotkit]");
      if (!chatArea) return;
      const elements = chatArea.querySelectorAll("p, span, div");
      for (const el of elements) {
        if (el.getAttribute("data-json-hidden") !== null) continue;
        if (el.closest("[data-json-hidden]")) continue;
        if (el.children.length > 2) continue;

        const text = (el.textContent || "").trim();
        if (text.length < 80) continue;

        const looksLikeJson =
          (text.startsWith("{") && text.includes('"')) ||
          (text.startsWith("[") && text.includes('"')) ||
          (text.includes('"nodes"') && text.includes('"label"')) ||
          (text.includes('"label"') &&
            text.includes('"type"') &&
            text.includes('"description"'));

        if (!looksLikeJson) continue;

        el.setAttribute("data-json-hidden", "true");
        el.addEventListener("click", () => {
          el.classList.toggle("json-expanded");
        });
      }
    };

    const observer = new MutationObserver(tag);
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    return () => observer.disconnect();
  }, []);

  return null;
}
