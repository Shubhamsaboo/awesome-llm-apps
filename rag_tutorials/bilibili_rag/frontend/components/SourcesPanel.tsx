"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  FavoriteFolder,
  Video,
  favoritesApi,
  knowledgeApi,
  BuildStatus,
  FolderStatus,
  OrganizePreviewResponse,
} from "@/lib/api";
import OrganizePreviewModal from "@/components/OrganizePreviewModal";
import ExportMarkdownModal from "@/components/ExportMarkdownModal";

interface Props {
  sessionId: string;
  onBuildDone?: () => void;
  onSelectionChange?: (folderIds: number[]) => void;
}

interface ExportTarget {
  video: Video;
  folderId: number;
}

export default function SourcesPanel({ sessionId, onBuildDone, onSelectionChange }: Props) {
  const [folders, setFolders] = useState<(FavoriteFolder & { videos?: Video[]; expanded?: boolean; loading?: boolean; count_source?: "bili" | "filtered" | "db" })[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  const [progress, setProgress] = useState<BuildStatus | null>(null);
  const [statusMap, setStatusMap] = useState<Record<number, FolderStatus>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [organizeOpen, setOrganizeOpen] = useState(false);
  const [organizeLoading, setOrganizeLoading] = useState(false);
  const [organizePreview, setOrganizePreview] = useState<OrganizePreviewResponse | null>(null);
  const [organizeMessage, setOrganizeMessage] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [exportTarget, setExportTarget] = useState<ExportTarget | null>(null);

  // 加载收藏夹列表（从B站获取）
  const loadFolders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await favoritesApi.getList(sessionId);
      setFolders(data.map((f) => ({ ...f, count_source: "bili" })));
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  }, [sessionId]);

  // 加载入库状态（从本地数据库）
  const loadStatuses = useCallback(async () => {
    try {
      const data = await knowledgeApi.getFolderStatus(sessionId);
      const map: Record<number, FolderStatus> = {};
      data.forEach((item) => {
        map[item.media_id] = item;
      });
      setStatusMap(map);
      setFolders((prev) =>
        prev.map((f) => {
          const s = map[f.media_id];
          if (!s?.media_count) return f;
          if (f.count_source === "filtered") return f;
          return { ...f, count_source: "bili" };
        })
      );
    } catch (error) {
      console.error(error);
    }
  }, [sessionId]);

  useEffect(() => {
    void loadFolders().then(loadStatuses);
  }, [loadFolders, loadStatuses]);

  // 刷新
  const refresh = useCallback(async () => {
    setMessage(null);
    await loadFolders();
    await loadStatuses();
  }, [loadFolders, loadStatuses]);

  const openOrganizePreview = async (folderId: number) => {
    setOrganizeMessage(null);
    setOrganizePreview(null);
    setOrganizeOpen(true);
    setOrganizeLoading(true);
    try {
      const res = await favoritesApi.organizePreview(folderId, sessionId);
      setOrganizePreview(res);
    } catch {
      setOrganizeMessage("预览失败，请稍后重试");
    } finally {
      setOrganizeLoading(false);
    }
  };

  // 展开收藏夹查看视频
  const toggleExpand = async (id: number) => {
    setFolders((prev) =>
      prev.map((f) => {
        if (f.media_id !== id) return f;
        if (f.expanded) return { ...f, expanded: false };
        if (f.videos) return { ...f, expanded: true };
        return { ...f, expanded: true, loading: true };
      })
    );

    const folder = folders.find((f) => f.media_id === id);
    if (!folder?.videos) {
      try {
        const res = await favoritesApi.getAllVideos(id, sessionId);
        setFolders((prev) =>
          prev.map((f) =>
            f.media_id === id ? { ...f, videos: res.videos, loading: false, media_count: res.total, count_source: "filtered" } : f
          )
        );
      } catch {
        setFolders((prev) =>
          prev.map((f) => (f.media_id === id ? { ...f, loading: false } : f))
        );
      }
    }
  };

  // 选择收藏夹
  const toggleSelect = (id: number) => {
    const s = new Set(selected);
    if (s.has(id)) {
      s.delete(id);
    } else {
      s.add(id);
    }
    setSelected(s);
    onSelectionChange?.(Array.from(s));
  };

  const selectedFolders = useMemo(
    () => folders.filter((folder) => selected.has(folder.media_id)),
    [folders, selected]
  );

  const selectedVideoCount = selectedFolders.reduce((sum, folder) => {
    const status = statusMap[folder.media_id];
    return sum + (status?.media_count ?? folder.media_count ?? 0);
  }, 0);

  const openBuildConfirm = () => {
    if (selected.size === 0 || building) return;
    setConfirmOpen(true);
  };

  // 构建/更新知识库（统一操作）
  const startBuildKnowledge = async () => {
    if (selected.size === 0) return;
    setConfirmOpen(false);
    setBuilding(true);
    setMessage(null);
    setProgress(null);

    try {
      const res = await knowledgeApi.build({ folder_ids: Array.from(selected) }, sessionId);

      const poll = async () => {
        const s = await knowledgeApi.getBuildStatus(res.task_id);
        setProgress(s);

        if (s.status === "running" || s.status === "pending") {
          setTimeout(poll, 1000);
        } else {
          setBuilding(false);
          if (s.status === "completed") {
            setMessage(s.message || "构建完成");
            await loadStatuses();
            onBuildDone?.();
          } else if (s.status === "failed") {
            setMessage(`构建失败: ${s.message}`);
          }
        }
      };
      poll();
    } catch {
      setBuilding(false);
      setMessage("构建失败，请重试");
    }
  };

  // 格式化时间
  const formatTime = (value?: string) => {
    if (!value) return null;
    try {
      let dateStr = value;
      if (!value.includes('T') && !value.includes('Z')) {
        dateStr = value.replace(' ', 'T') + 'Z';
      }
      const date = new Date(dateStr);
      if (Number.isNaN(date.getTime())) return null;

      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hour = String(date.getHours()).padStart(2, '0');
      const minute = String(date.getMinutes()).padStart(2, '0');
      return `${month}/${day} ${hour}:${minute}`;
    } catch {
      return null;
    }
  };

  // 获取收藏夹状态
  const getFolderStatus = (mediaId: number, totalInBilibili: number) => {
    const status = statusMap[mediaId];
    const indexedCount = status?.indexed_count ?? 0;
    const failedCount = status?.failed_count ?? 0;
    const lastSync = status?.last_sync_at;
    const folder = folders.find((f) => f.media_id === mediaId);
    const countSource = folder?.count_source ?? "bili";
    let totalCount = totalInBilibili;
    if (countSource === "filtered") {
      totalCount = folder?.media_count ?? totalInBilibili;
    } else if (status?.media_count != null) {
      totalCount = status.media_count;
    }

    // 未入库：从未同步过
    if (!lastSync) {
      return { label: "未入库", className: "empty", indexedCount };
    }

    if (failedCount > 0) {
      const label = indexedCount > 0 ? "部分入库失败" : "入库失败";
      return { label, className: "partial", indexedCount, totalCount };
    }

    // 已入库：有同步时间
    if (indexedCount >= totalCount) {
      return { label: "已入库", className: "ok", indexedCount, totalCount };
    }

    // 有更新：B站收藏夹比本地多
    if (indexedCount < totalCount && indexedCount > 0) {
      return { label: "有更新", className: "partial", indexedCount, totalCount };
    }

    if (totalCount > 0 && indexedCount === 0) {
      return { label: "入库失败", className: "partial", indexedCount, totalCount };
    }

    // 空收藏夹已完成同步
    return { label: "已入库", className: "ok", indexedCount, totalCount };
  };

  // 计算按钮文字
  const getButtonText = () => {
    if (building) return progress?.current_step || "处理中...";
    if (selected.size === 0) return "选择收藏夹";

    // 检查选中的是否有未入库的
    const hasUnindexed = Array.from(selected).some((id) => {
      const folder = folders.find((f) => f.media_id === id);
      if (!folder) return false;
      return !statusMap[id]?.last_sync_at;
    });

    if (hasUnindexed) {
      return `入库 (${selected.size})`;
    }
    return `更新 (${selected.size})`;
  };

  return (
    <div className="panel-inner">
      <div className="panel-header">
        <div>
          <div className="panel-title">收藏夹</div>
          <div className="panel-subtitle">{folders.length} 个</div>
        </div>
        <div className="panel-actions">
          <button
            onClick={() => {
              const def = folders.find((f) => f.is_default || f.title === "默认收藏夹");
              if (def) {
                openOrganizePreview(def.media_id);
              } else {
                setOrganizeMessage("未找到默认收藏夹");
              }
            }}
            className="btn btn-ghost"
            disabled={loading || organizeLoading}
          >
            {organizeLoading ? "整理中..." : "快速整理默认收藏夹"}
          </button>
          <button onClick={refresh} className="btn btn-ghost" disabled={loading}>
            {loading ? "加载中..." : "刷新"}
          </button>
        </div>
      </div>

      <div className="panel-body">
        <div className="sources-scroll">
          {loading ? (
            <div className="text-center text-sm text-[var(--muted)] py-6">加载中...</div>
          ) : folders.length === 0 ? (
            <div className="text-center text-sm text-[var(--muted)] py-6">暂无收藏夹</div>
          ) : (
            <div className="space-y-2">
              {folders.map((f) => {
                const status = getFolderStatus(f.media_id, f.media_count);
                const lastSync = formatTime(statusMap[f.media_id]?.last_sync_at);

                return (
                  <div key={f.media_id} className={`folder-card ${selected.has(f.media_id) ? "selected" : ""}`}>
                    <div className="folder-head" onClick={() => toggleExpand(f.media_id)}>
                      <input
                        type="checkbox"
                        checked={selected.has(f.media_id)}
                        onChange={() => toggleSelect(f.media_id)}
                        onClick={(e) => e.stopPropagation()}
                        className="w-4 h-4 accent-[var(--accent)]"
                      />
                      <div className="folder-meta">
                        <div className="folder-title" title={f.title}>{f.title}</div>
                      <div className="folder-count">
                        {status.indexedCount}/{status.totalCount ?? f.media_count} 个视频
                        {lastSync && ` · ${lastSync}`}
                      </div>
                      </div>
                      <span className={`status-pill ${status.className}`}>{status.label}</span>
                      <div className="folder-toggle">
                        <svg className={`w-4 h-4 transition-transform ${f.expanded ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>

                    {f.expanded && (
                      <div className="folder-list">
                        {f.loading ? (
                          <div className="text-xs text-[var(--muted)]">加载中...</div>
                        ) : f.videos?.length === 0 ? (
                          <div className="text-xs text-[var(--muted)]">暂无视频</div>
                        ) : (
                          f.videos?.map((v) => (
                            <div key={v.bvid} className="video-item">
                              <button
                                className="video-export-button"
                                onClick={() => setExportTarget({ video: v, folderId: f.media_id })}
                                title="导出 Markdown"
                                aria-label={`导出 ${v.title}`}
                              >
                                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                  <path d="M12 3v11m0 0 4-4m-4 4-4-4M5 17v3h14v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                              </button>
                              <a
                                className="video-title-link"
                                href={`https://www.bilibili.com/video/${v.bvid}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                title={`${v.title} · 打开原视频`}
                              >
                                {v.title}
                              </a>
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="panel-footer">
        {/* 进度条 */}
        {progress && building && (
          <div className="mb-4">
            <div className="flex justify-between text-xs mb-2">
              <span className="text-[var(--muted)] truncate">{progress.current_step}</span>
              <span className="text-[var(--accent)]">{progress.progress}%</span>
            </div>
            <div className="build-progress-meta">
              {progress.total_folders ? (
                <span>
                  收藏夹 {progress.processed_folders ?? 0}/{progress.total_folders}
                </span>
              ) : null}
              {progress.total_videos ? (
                <span>
                  视频 {progress.processed_videos}/{progress.total_videos}
                </span>
              ) : null}
            </div>
            {progress.current_video_title && (
              <div className="build-current-title" title={progress.current_video_title}>
                当前：{progress.current_video_title}
              </div>
            )}
            <div className="progress">
              <div className="progress-bar" style={{ width: `${progress.progress}%` }} />
            </div>
          </div>
        )}

        {/* 消息 */}
        {message && <div className="text-xs text-[var(--muted)] mb-3">{message}</div>}
        {organizeMessage && <div className="text-xs text-[var(--muted)] mb-3">{organizeMessage}</div>}

        {/* 主按钮 */}
        <button
          onClick={openBuildConfirm}
          disabled={selected.size === 0 || building}
          className="btn btn-primary w-full"
        >
          {getButtonText()}
        </button>

        <p className="text-xs text-[var(--muted)] text-center mt-2">
          入库后可在右侧进行问答
        </p>
      </div>

      <OrganizePreviewModal
        open={organizeOpen}
        sessionId={sessionId}
        preview={organizePreview}
        loading={organizeLoading}
        errorMessage={organizeMessage}
        onClose={() => setOrganizeOpen(false)}
        onApplied={refresh}
      />

      <ExportMarkdownModal
        video={exportTarget?.video ?? null}
        folderId={exportTarget?.folderId ?? null}
        sessionId={sessionId}
        onClose={() => setExportTarget(null)}
        onIngested={async () => {
          await loadStatuses();
          onBuildDone?.();
        }}
      />

      {confirmOpen && (
        <div className="modal-backdrop" onClick={() => setConfirmOpen(false)}>
          <div className="modal-card build-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">确认入库</div>
            <div className="modal-subtitle">
              将处理 {selectedFolders.length} 个收藏夹，约 {selectedVideoCount} 个视频
            </div>

            <div className="build-confirm-list">
              {selectedFolders.map((folder) => {
                const status = getFolderStatus(folder.media_id, folder.media_count);
                return (
                  <div key={folder.media_id} className="build-confirm-item">
                    <div>
                      <div className="build-confirm-title" title={folder.title}>
                        {folder.title}
                      </div>
                      <div className="build-confirm-meta">
                        {status.indexedCount}/{status.totalCount ?? folder.media_count} 个视频
                      </div>
                    </div>
                    <span className={`status-pill ${status.className}`}>{status.label}</span>
                  </div>
                );
              })}
            </div>

            {selectedVideoCount >= 50 && (
              <div className="build-confirm-warning">
                本次视频较多，可能触发较长 ASR/Embedding 处理，也会产生模型调用费用。建议首次使用先小批量验证。
              </div>
            )}

            <div className="organize-actions">
              <button className="btn btn-outline" onClick={() => setConfirmOpen(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={startBuildKnowledge}>
                确认开始
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
