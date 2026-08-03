"use client";

import { useEffect, useMemo, useState } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

type Step = "idle" | "typing" | "searching" | "answering" | "done";

export default function DemoFlowModal({ isOpen, onClose }: Props) {
  const [runId, setRunId] = useState(0);
  if (!isOpen) return null;

  return (
    <DemoFlowContent
      key={runId}
      onClose={onClose}
      onReplay={() => setRunId((value) => value + 1)}
    />
  );
}

function DemoFlowContent({ onClose, onReplay }: { onClose: () => void; onReplay: () => void }) {
  const question = "这个收藏夹里有哪些适合快速入门的 AI 视频？";
  const answer =
    "我从收藏夹中找到了 3 个适合入门的内容：\n\n" +
    "1) 《AI 入门路线 30 分钟速览》\n" +
    "2) 《从零理解大模型》\n" +
    "3) 《提示词工程的 10 个关键技巧》\n\n" +
    "你可以从第 1 个开始，搭建整体框架，然后再深入细节。";
  const sources = useMemo(
    () => [
      { title: "AI 入门路线 30 分钟速览", url: "#" },
      { title: "从零理解大模型", url: "#" },
      { title: "提示词工程的 10 个关键技巧", url: "#" },
    ],
    []
  );

  const [step, setStep] = useState<Step>("typing");
  const [typed, setTyped] = useState("");
  const [answerTyped, setAnswerTyped] = useState("");

  useEffect(() => {
    let typingTimer: number | null = null;
    let searchTimer: number | null = null;
    let answerTimer: number | null = null;

    let i = 0;
    typingTimer = window.setInterval(() => {
      i += 1;
      setTyped(question.slice(0, i));
      if (i >= question.length) {
        if (typingTimer) window.clearInterval(typingTimer);
        setStep("searching");
        searchTimer = window.setTimeout(() => {
          setStep("answering");
          let j = 0;
          answerTimer = window.setInterval(() => {
            j += 2;
            setAnswerTyped(answer.slice(0, j));
            if (j >= answer.length) {
              if (answerTimer) window.clearInterval(answerTimer);
              setStep("done");
            }
          }, 18);
        }, 1400);
      }
    }, 60);

    return () => {
      if (typingTimer) window.clearInterval(typingTimer);
      if (searchTimer) window.clearTimeout(searchTimer);
      if (answerTimer) window.clearInterval(answerTimer);
    };
  }, [question, answer]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card demo-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-title">检索流程演示</div>
        <div className="modal-subtitle">慢速演示：理解“提问 → 检索 → 回答”</div>

        <div className="demo-grid mt-4 text-sm">
          <div className="demo-preview">
            <div>
              <div className="text-[var(--muted)] text-xs mb-1">提问</div>
              <div className="input">{typed || "..."}</div>
            </div>

            <div className="flex items-center justify-between mt-3">
              <div className="text-xs text-[var(--muted)]">
                {step === "searching" && "系统正在检索你的收藏夹内容..."}
                {step === "answering" && "系统正在生成结构化答案..."}
                {step === "done" && "演示完成，可继续追问"}
                {(step === "typing" || step === "idle") && "等待输入..."}
              </div>
              <span className={`status-pill ${step === "done" ? "ok" : "partial"}`}>
                {step === "done" ? "完成" : "处理中"}
              </span>
            </div>

            <div className="mt-3">
              <div className="text-[var(--muted)] text-xs mb-1">回答</div>
              <div className="message-bubble message assistant demo-answer">
                <div className="markdown whitespace-pre-line">
                  {answerTyped || " "}
                </div>
              </div>
            </div>

            {step === "done" && (
              <div className="demo-sources">
                <div className="text-[var(--muted)] text-xs mb-1">来源</div>
                <div className="source-list">
                  {sources.map((s, i) => (
                    <span key={i} className="source-link">
                      {s.title}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="demo-actions">
              <button onClick={onReplay} className="btn btn-ghost">
                重新播放
              </button>
              <button onClick={onClose} className="btn btn-outline">
                我知道了
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
