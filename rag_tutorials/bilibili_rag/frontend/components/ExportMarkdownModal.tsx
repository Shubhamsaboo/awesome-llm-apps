"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, knowledgeApi, Video } from "@/lib/api";

interface Props {
  video: Video | null;
  folderId: number | null;
  sessionId: string;
  onClose: () => void;
  onIngested?: () => void | Promise<void>;
}

type ExportMode = "original" | "ai";

function createOperationId() {
  return typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function ExportMarkdownModal({
  video,
  folderId,
  sessionId,
  onClose,
  onIngested,
}: Props) {
  const [exporting, setExporting] = useState<ExportMode | null>(null);
  const [pendingMode, setPendingMode] = useState<ExportMode | null>(null);
  const [ingesting, setIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeController = useRef<AbortController | null>(null);
  const activeOperationId = useRef<string | null>(null);

  useEffect(() => {
    activeController.current?.abort();
    activeController.current = null;
    activeOperationId.current = null;
    setExporting(null);
    setPendingMode(null);
    setIngesting(false);
    setError(null);
    return () => activeController.current?.abort();
  }, [video, folderId]);

  if (!video) return null;

  const download = async (
    mode: ExportMode,
    promptForIngest = true,
    existingController?: AbortController,
    existingOperationId?: string,
  ) => {
    const controller = existingController || new AbortController();
    const operationId = existingOperationId || createOperationId();
    activeController.current = controller;
    activeOperationId.current = operationId;
    setExporting(mode);
    setError(null);
    try {
      const blob = await knowledgeApi.exportMarkdown(
        video.bvid,
        mode,
        sessionId,
        operationId,
        controller.signal,
      );
      if (controller.signal.aborted) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const safeTitle = video.title.replace(/[\\/:*?"<>|\r\n]+/g, "_").trim().slice(0, 80);
      link.href = url;
      link.download = `${safeTitle || video.bvid}.md`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      onClose();
    } catch (err) {
      if (controller.signal.aborted) return;
      if (
        promptForIngest &&
        err instanceof ApiError &&
        (err.status === 404 || err.status === 409)
      ) {
        setPendingMode(mode);
        return;
      }
      setError(err instanceof Error ? err.message : "导出失败，请稍后重试");
    } finally {
      if (activeController.current === controller) {
        activeController.current = null;
        activeOperationId.current = null;
      }
      setExporting(null);
    }
  };

  const ingestAndDownload = async () => {
    if (!pendingMode || folderId == null) return;
    const mode = pendingMode;
    const controller = new AbortController();
    const operationId = createOperationId();
    activeController.current = controller;
    activeOperationId.current = operationId;
    setIngesting(true);
    setError(null);
    try {
      await knowledgeApi.ingestVideo(
        video.bvid,
        folderId,
        sessionId,
        operationId,
        controller.signal,
      );
      if (controller.signal.aborted) return;
      await onIngested?.();
      if (controller.signal.aborted) return;
      setPendingMode(null);
      await download(mode, false, controller, operationId);
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(err instanceof Error ? err.message : "单视频入库失败，请稍后重试");
    } finally {
      if (activeController.current === controller) {
        activeController.current = null;
        activeOperationId.current = null;
      }
      setIngesting(false);
    }
  };

  const cancel = () => {
    const operationId = activeOperationId.current;
    if (operationId) {
      void knowledgeApi.cancelOperation(operationId, sessionId).catch(() => {});
    }
    activeController.current?.abort();
    activeController.current = null;
    activeOperationId.current = null;
    onClose();
  };

  const busy = Boolean(exporting) || ingesting;

  return (
    <div className="modal-backdrop" onClick={cancel}>
      <div className="modal-card export-modal" onClick={(event) => event.stopPropagation()}>
        <div className="export-kicker">MARKDOWN EXPORT</div>
        <div className="modal-title">导出视频内容</div>
        <div className="modal-subtitle export-video-title" title={video.title}>
          {video.title}
        </div>

        {pendingMode ? (
          <div className="export-ingest-confirm">
            <div className="export-ingest-kicker">需要先入库</div>
            <strong>该视频尚无可导出的本地内容</strong>
            <p>确认后只处理当前视频，完成字幕 / ASR 获取和向量写入后，将自动继续导出。</p>
            <div className="organize-actions">
              <button
                className="btn btn-outline"
                disabled={ingesting}
                onClick={() => setPendingMode(null)}
              >
                返回
              </button>
              <button className="btn btn-primary" disabled={ingesting} onClick={ingestAndDownload}>
                {ingesting ? "单视频入库中..." : "入库并导出"}
              </button>
            </div>
          </div>
        ) : (
          <div className="export-options">
            <button
              className="export-option"
              disabled={busy}
              onClick={() => download("original")}
            >
              <span className="export-option-index">01</span>
              <span>
                <strong>{exporting === "original" ? "正在导出..." : "原始内容"}</strong>
                <small>元信息、视频简介与完整字幕 / ASR 转写</small>
              </span>
              <span className="export-option-arrow">↓</span>
            </button>

            <button
              className="export-option featured"
              disabled={busy}
              onClick={() => download("ai")}
            >
              <span className="export-option-index">02</span>
              <span>
                <strong>{exporting === "ai" ? "AI 正在整理..." : "AI 整理 + 原始内容"}</strong>
                <small>生成摘要、核心观点、提纲和行动建议，并保留原文</small>
              </span>
              <span className="export-option-arrow">✦</span>
            </button>
          </div>
        )}

        <div className="export-note">
          {pendingMode
            ? "单视频入库可能执行 ASR 与 Embedding，并产生对应服务费用。"
            : "AI 整理会调用当前配置的模型并产生费用；已入库视频不会重新执行转写。"}
        </div>
        {error && <div className="export-error">{error}</div>}

        <div className="organize-actions">
          <button className="btn btn-outline" onClick={cancel}>
            取消
          </button>
        </div>
      </div>
    </div>
  );
}
