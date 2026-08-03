"use client";

import { useEffect, useMemo, useState } from "react";
import {
  OrganizePreviewResponse,
  OrganizePreviewItem,
  favoritesApi,
} from "@/lib/api";

interface Props {
  open: boolean;
  sessionId: string;
  preview: OrganizePreviewResponse | null;
  loading?: boolean;
  errorMessage?: string | null;
  onClose: () => void;
  onApplied?: () => void;
}

export default function OrganizePreviewModal({
  open,
  sessionId,
  preview,
  loading = false,
  errorMessage = null,
  onClose,
  onApplied,
}: Props) {
  const [items, setItems] = useState<OrganizePreviewItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setItems(preview?.items ?? []);
    setMessage(null);
  }, [preview]);

  const folders = preview?.folders ?? [];
  const defaultFolderTitle = preview?.default_folder_title ?? "默认收藏夹";
  const stats = useMemo(() => {
    const matched = items.filter((item) => item.target_folder_id).length;
    return {
      total: items.length,
      matched,
      unmatched: items.length - matched,
    };
  }, [items]);

  const updateTarget = (bvid: string, targetId: string) => {
    const next = targetId ? Number(targetId) : null;
    setItems((prev) =>
      prev.map((item) =>
        item.bvid === bvid ? { ...item, target_folder_id: next } : item
      )
    );
  };

  const handleExecute = async () => {
    if (!preview || !sessionId) return;
    setSubmitting(true);
    setMessage(null);
    try {
      const moves = items
        .filter((item) => item.target_folder_id)
        .map((item) => ({
          resource_id: item.resource_id,
          resource_type: item.resource_type,
          target_folder_id: item.target_folder_id as number,
        }));

      const res = await favoritesApi.organizeExecute(
        {
          default_folder_id: preview.default_folder_id,
          moves,
        },
        sessionId
      );
      setMessage(`已移动 ${res.moved} 条内容`);
      onApplied?.();
      onClose();
    } catch {
      setMessage("执行失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  };

  const handleClean = async () => {
    if (!preview || !sessionId) return;
    setCleaning(true);
    setMessage(null);
    try {
      await favoritesApi.cleanInvalid(preview.default_folder_id, sessionId);
      setMessage("已清理失效内容");
      onApplied?.();
    } catch {
      setMessage("清理失败，请稍后重试");
    } finally {
      setCleaning(false);
    }
  };

  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card organize-modal" onClick={(e) => e.stopPropagation()}>
        <div className="organize-header">
          <div>
            <div className="modal-title">一键整理预览</div>
            <div className="modal-subtitle">
              默认收藏夹：{defaultFolderTitle}
            </div>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleClean}
            disabled={cleaning || loading || !preview}
          >
            {cleaning ? "清理中..." : "清理失效"}
          </button>
        </div>

        {preview && (
          <div className="organize-stats">
            <span>总计 {stats.total}</span>
            <span>已匹配 {stats.matched}</span>
            <span>未匹配 {stats.unmatched}</span>
          </div>
        )}

        <div className="organize-list">
          {loading ? (
            <div className="organize-empty">正在生成预览...</div>
          ) : preview ? (
            items.map((item) => (
              <div key={item.bvid} className="organize-item">
                <div className="organize-info">
                  <div className="organize-title" title={item.title}>
                    {item.title}
                  </div>
                  <div className="organize-meta">
                    <span>{item.bvid}</span>
                    {item.reason && <span>· {item.reason}</span>}
                  </div>
                </div>
                <div className="organize-select">
                  <select
                    value={item.target_folder_id ?? ""}
                    onChange={(e) => updateTarget(item.bvid, e.target.value)}
                  >
                    <option value="">
                      留在 {defaultFolderTitle}
                    </option>
                    {folders.map((folder) => (
                      <option key={folder.media_id} value={folder.media_id}>
                        {folder.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ))
          ) : (
            <div className="organize-empty">预览失败，请重试</div>
          )}
        </div>

        {(errorMessage || message) && (
          <div className="organize-message">{errorMessage || message}</div>
        )}

        <div className="organize-actions">
          <button className="btn btn-outline" onClick={onClose}>
            取消
          </button>
          <button
            className="btn btn-primary"
            onClick={handleExecute}
            disabled={submitting || loading || !preview}
          >
            {submitting ? "移动中..." : "确认移动"}
          </button>
        </div>
      </div>
    </div>
  );
}
