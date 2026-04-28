import { useState } from "react";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";
import { CopilotChatInputProps, useAgent, useCopilotKit } from "@copilotkit/react-core/v2";

export function ChatInput(_props: CopilotChatInputProps) {
  const { agent } = useAgent();
  const { copilotkit } = useCopilotKit();
  const [input, setInput] = useState("");

  const handleSend = () => {
    agent.addMessage({ id: crypto.randomUUID(), role: "user", content: input });
    copilotkit.runAgent({ agent });
    setInput("");
  };

  return (
    <div>
      <Textarea onChange={(e) => setInput(e.target.value)} value={input} />
      <Button onClick={handleSend}>Send</Button>
    </div>
  );
}
