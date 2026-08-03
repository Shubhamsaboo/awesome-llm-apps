"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { chatApi, knowledgeApi, KnowledgeStats, API_BASE_URL } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ bvid: string; title: string; url: string }>;
  trace?: TraceEvent[];
  traceOpen?: boolean;
  traceDone?: boolean;
}

interface TraceEvent {
  type: "status" | "scope" | "retrieval" | "snippet";
  stage?: string;
  message?: string;
  title?: string;
  preview?: string;
  url?: string;
  folder_count?: number;
  video_count?: number;
  vector_count?: number;
  keyword_count?: number;
  final_count?: number;
  elapsed_ms?: number;
}

type StreamEvent =
  | TraceEvent
  | { type: "token"; content: string }
  | { type: "sources"; items: Array<{ bvid: string; title: string; url: string }> }
  | { type: "done" }
  | { type: "error"; message: string };

interface Props {
  statsKey?: number;
  sessionId?: string;
  folderIds?: number[];
}

function ExecutionTrace({
  events,
  open,
  done,
  onToggle,
}: {
  events: TraceEvent[];
  open: boolean;
  done: boolean;
  onToggle: () => void;
}) {
  const snippets = events.filter((event) => event.type === "snippet");
  const steps = events.filter((event) => event.type !== "snippet");
  const latest = steps.at(-1)?.message || (done ? "执行完成" : "正在处理");

  return (
    <div className={`execution-trace ${done ? "done" : "running"}`}>
      <button
        type="button"
        className="execution-trace-head"
        aria-expanded={open}
        onClick={onToggle}
      >
        <span className="execution-trace-signal" aria-hidden="true" />
        <span className="execution-trace-title">{done ? "执行过程" : latest}</span>
        {done && <span className="execution-trace-summary">{steps.length} 个步骤</span>}
        <svg className={open ? "open" : ""} viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="m6 8 4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div className="execution-trace-body">
          <div className="execution-steps">
            {steps.map((event, index) => (
              <div className="execution-step" key={`${event.type}-${event.stage}-${index}`}>
                <span className="execution-step-mark">{index + 1}</span>
                <span>{event.message}</span>
                {event.elapsed_ms != null && (
                  <small>{(event.elapsed_ms / 1000).toFixed(2)}s</small>
                )}
              </div>
            ))}
          </div>

          {snippets.length > 0 && (
            <div className="execution-snippets">
              <div className="execution-snippets-label">召回片段</div>
              {snippets.map((event, index) => (
                <a
                  className="execution-snippet"
                  href={event.url || undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  key={`${event.title}-${index}`}
                >
                  <strong>{event.title}</strong>
                  <span>{event.preview}</span>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ChatPanel({ statsKey, sessionId, folderIds }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    knowledgeApi.getStats().then(setStats).catch(() => { });
  }, [statsKey]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput("");
    const userId = Date.now().toString();
    const assistantId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      { id: userId, role: "user", content: q },
      {
        id: assistantId,
        role: "assistant",
        content: "",
        sources: [],
        trace: [{ type: "status", stage: "connecting", message: "正在连接问答服务" }],
        traceOpen: true,
        traceDone: false,
      },
    ]);
    setLoading(true);

    let receivedEvent = false;
    try {
      const response = await fetch(`${API_BASE_URL}/chat/ask/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: q,
          session_id: sessionId,
          folder_ids: folderIds,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error("流式接口不可用");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let answerBuffer = "";
      let pendingBuffer = "";
      let pendingSources: Array<{ bvid: string; title: string; url: string }> = [];
      let streamCompleted = false;

      const applyEvent = (event: StreamEvent) => {
        receivedEvent = true;
        if (event.type === "token") {
          answerBuffer += event.content;
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantId ? { ...message, content: answerBuffer } : message
            )
          );
          return;
        }
        if (event.type === "sources") {
          pendingSources = event.items;
          return;
        }
        if (event.type === "done") {
          streamCompleted = true;
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantId
                ? { ...message, sources: pendingSources, traceOpen: false, traceDone: true }
                : message
            )
          );
          return;
        }
        if (event.type === "error") {
          streamCompleted = true;
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantId
                ? {
                    ...message,
                    content: answerBuffer || `错误: ${event.message}`,
                    trace: [...(message.trace || []), { type: "status", stage: "error", message: event.message }],
                    traceOpen: true,
                    traceDone: true,
                  }
                : message
            )
          );
          return;
        }
        setMessages((prev) =>
          prev.map((message) =>
            message.id === assistantId
              ? { ...message, trace: [...(message.trace || []), event] }
              : message
          )
        );
      };

      const parseLine = (line: string) => {
        if (!line.trim()) return;
        const event = JSON.parse(line) as StreamEvent;
        applyEvent(event);
      };

      while (true) {
        const { value, done: doneReading } = await reader.read();
        if (value) {
          pendingBuffer += decoder.decode(value, { stream: !doneReading });
          const lines = pendingBuffer.split("\n");
          pendingBuffer = lines.pop() || "";
          for (const line of lines) {
            parseLine(line);
          }
        }
        if (doneReading) break;
      }
      if (pendingBuffer.trim()) {
        parseLine(pendingBuffer);
      }
      if (!streamCompleted) {
        throw new Error("流式响应意外结束");
      }
    } catch (streamError) {
      if (!receivedEvent) {
        try {
          const res = await chatApi.ask(q, sessionId, folderIds);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: res.answer,
                    sources: res.sources,
                    trace: [...(m.trace || []), { type: "status", stage: "fallback", message: "流式过程不可用，已切换普通回答" }],
                    traceOpen: false,
                    traceDone: true,
                  }
                : m
            )
          );
        } catch (err) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: `错误: ${err instanceof Error ? err.message : "请求失败"}`,
                    traceOpen: true,
                    traceDone: true,
                  }
                : m
            )
          );
        }
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: m.content || `错误: ${streamError instanceof Error ? streamError.message : "流式响应失败"}`,
                  trace: [
                    ...(m.trace || []),
                    {
                      type: "status",
                      stage: "error",
                      message: streamError instanceof Error ? streamError.message : "流式响应失败",
                    },
                  ],
                  traceOpen: true,
                  traceDone: true,
                }
              : m
          )
        );
      }
    }
    setLoading(false);
  };

  return (
    <div className="panel-inner">
      <div className="panel-header">
        <div>
          <div className="panel-title">对话工作台</div>
          {stats && stats.total_videos > 0 && (
            <div className="panel-subtitle">已收录 {stats.total_videos} 个视频</div>
          )}
        </div>
        {messages.length > 0 && (
          <button onClick={() => setMessages([])} className="btn btn-ghost" title="清空">
            清空对话
          </button>
        )}
      </div>

      <div className="panel-body">
        <div className="chat-scroll">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div>
                <div className="status-pill">检索就绪</div>
                <p className="text-sm text-[var(--muted)] mt-3">把收藏夹变成可提问的知识库</p>
              </div>
              <div className="prompt-grid">
                {[
                  "总结收藏夹里最有价值的内容",
                  "有哪些适合快速复习的系列？",
                  "列出与某个主题相关的视频并给出关键点",
                  "按主题整理我的收藏夹内容",
                  "用一句话概括每个视频的重点",
                  "推荐3个最适合入门的学习视频",
                ].map((q, i) => (
                  <button key={i} onClick={() => setInput(q)} className="prompt-chip">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="chat-window">
              {messages.map((m) => (
                <div key={m.id} className={`message ${m.role}`}>
                  <div className="message-bubble">
                    {m.trace && m.trace.length > 0 && (
                      <ExecutionTrace
                        events={m.trace}
                        open={m.traceOpen ?? false}
                        done={m.traceDone ?? false}
                        onToggle={() =>
                          setMessages((prev) =>
                            prev.map((message) =>
                              message.id === m.id ? { ...message, traceOpen: !message.traceOpen } : message
                            )
                          )
                        }
                      />
                    )}
                    <ReactMarkdown className="markdown" remarkPlugins={[remarkGfm]}>
                      {m.content}
                    </ReactMarkdown>
                    {m.sources && m.sources.length > 0 && (
                      <div className="source-list">
                        {m.sources.map((s, i) => (
                          <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="source-link">
                            {s.title}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={endRef} />
            </div>
          )}
        </div>
      </div>

      <div className="panel-footer">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="输入问题..."
            className="input"
          />
          <button onClick={send} disabled={!input.trim() || loading} className="btn btn-primary">
            发送
          </button>
        </div>
      </div>
    </div>
  );
}
