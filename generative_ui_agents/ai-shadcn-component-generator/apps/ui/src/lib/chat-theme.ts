import { CustomMessageRenderer } from "@/components/custom-message-renderer";
import { CopilotChatProps } from "@copilotkit/react-core/v2";

export const chatTheme: CopilotChatProps = {
  messageView: {
    className:
      "bg-transparent [&::-webkit-scrollbar]:hidden [-ms-overflow-style:'none'] [scrollbar-width:'none']",
    userMessage: {
      className: "bg-transparent",
      messageRenderer: "text-blue-500",
    },
    assistantMessage: CustomMessageRenderer as any,
  },
  className: "bg-transparent",
  input: {
    className: "bg-transparent",
  },
  suggestionView: "bg-transparent",
};
