/**
 * API 客户端
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = "ApiError";
    }
}

// 通用请求函数
async function request<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    // 会话失效时自动清除登录状态并刷新页面
    if (response.status === 401) {
        if (typeof window !== "undefined") {
            localStorage.removeItem("bili_session");
            localStorage.removeItem("bili_user");
            window.location.href = "/";
        }
        throw new Error("会话已过期，请重新登录");
    }

    if (!response.ok) {
        const error = await response.text();
        let message = error || `请求失败: ${response.status}`;
        try {
            message = (JSON.parse(error) as { detail?: string }).detail || message;
        } catch {
            // 保留非 JSON 错误文本。
        }
        throw new ApiError(response.status, message);
    }

    return response.json();
}

async function requestBlob(endpoint: string, options: RequestInit = {}): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (response.status === 401 && typeof window !== "undefined") {
        localStorage.removeItem("bili_session");
        localStorage.removeItem("bili_user");
        window.location.href = "/";
        throw new Error("会话已过期，请重新登录");
    }

    if (!response.ok) {
        const payload = await response.json().catch(() => null) as { detail?: string } | null;
        throw new ApiError(response.status, payload?.detail || `导出失败: ${response.status}`);
    }

    return response.blob();
}

// ==================== 类型定义 ====================

export interface QRCodeResponse {
    qrcode_key: string;
    qrcode_url: string;
    qrcode_image_base64: string;
}

export interface LoginStatusResponse {
    status: "waiting" | "scanned" | "confirmed" | "expired";
    message: string;
    user_info?: UserInfo;
    session_id?: string;
}

export interface UserInfo {
    mid: number;
    uname: string;
    face: string;
    level?: number;
}

export interface FavoriteFolder {
    media_id: number;
    title: string;
    media_count: number;
    is_selected: boolean;
    is_default?: boolean;
}

export interface Video {
    bvid: string;
    title: string;
    cover?: string;
    duration?: number;
    owner?: string;
    play_count?: number;
    intro?: string;
    is_selected: boolean;
}

export interface FavoriteVideosResponse {
    folder_info: Record<string, unknown>;
    videos: Video[];
    has_more: boolean;
    page: number;
    page_size: number;
}

export interface OrganizePreviewItem {
    bvid: string;
    title: string;
    resource_id: number;
    resource_type: number;
    target_folder_id: number | null;
    target_folder_title: string;
    reason?: string;
}

export interface OrganizePreviewResponse {
    default_folder_id: number;
    default_folder_title: string;
    folders: FavoriteFolder[];
    items: OrganizePreviewItem[];
    stats: {
        total: number;
        matched: number;
        unmatched: number;
    };
}

export interface BuildRequest {
    folder_ids: number[];
    exclude_bvids?: string[];
}

export interface BuildStatus {
    task_id: string;
    status: "pending" | "running" | "completed" | "failed";
    progress: number;
    current_step: string;
    total_videos: number;
    processed_videos: number;
    total_folders?: number;
    processed_folders?: number;
    current_folder_id?: number;
    current_folder_title?: string;
    current_video_title?: string;
    message: string;
}

export interface FolderStatus {
    media_id: number;
    indexed_count: number;
    failed_count: number;
    media_count?: number;
    last_sync_at?: string;
}

export interface SyncRequest {
    folder_ids?: number[];
}

export interface SyncResult {
    folder_id: number;
    total: number;
    added: number;
    removed: number;
    indexed: number;
    failed: number;
    message: string;
    last_sync_at: string;
}

export interface KnowledgeStats {
    total_chunks: number;
    total_videos: number;
    collection_name: string;
}

export interface ChatResponse {
    answer: string;
    sources: Array<{
        bvid: string;
        title: string;
        url: string;
    }>;
}

// ==================== API 函数 ====================

// 认证相关
export const authApi = {
    // 获取登录二维码
    getQRCode: () => request<QRCodeResponse>("/auth/qrcode"),

    // 轮询登录状态
    pollQRCode: (qrcodeKey: string) =>
        request<LoginStatusResponse>(`/auth/qrcode/poll/${qrcodeKey}`),

    // 获取会话信息
    getSession: (sessionId: string) =>
        request<{ valid: boolean; user_info: UserInfo }>(`/auth/session/${sessionId}`),

    // 退出登录
    logout: (sessionId: string) =>
        request(`/auth/session/${sessionId}`, { method: "DELETE" }),
};

// 收藏夹相关
export const favoritesApi = {
    // 获取收藏夹列表
    getList: (sessionId: string) =>
        request<FavoriteFolder[]>(`/favorites/list?session_id=${sessionId}`),

    // 获取收藏夹视频（分页）
    getVideos: (mediaId: number, sessionId: string, page = 1) =>
        request<FavoriteVideosResponse>(
            `/favorites/${mediaId}/videos?session_id=${sessionId}&page=${page}`
        ),

    // 获取收藏夹全部视频
    getAllVideos: (mediaId: number, sessionId: string) =>
        request<{ total: number; videos: Video[] }>(
            `/favorites/${mediaId}/all-videos?session_id=${sessionId}`
        ),

    // 预览整理
    organizePreview: (folderId: number, sessionId: string) =>
        request<OrganizePreviewResponse>(
            `/favorites/organize/preview?session_id=${sessionId}`,
            {
                method: "POST",
                body: JSON.stringify({ folder_id: folderId }),
            }
        ),

    // 执行整理
    organizeExecute: (
        data: {
            default_folder_id: number;
            moves: Array<{ resource_id: number; resource_type: number; target_folder_id: number }>;
        },
        sessionId: string
    ) =>
        request<{ message: string; moved: number; groups: number }>(
            `/favorites/organize/execute?session_id=${sessionId}`,
            {
                method: "POST",
                body: JSON.stringify(data),
            }
        ),

    // 清理失效内容
    cleanInvalid: (folderId: number, sessionId: string) =>
        request<{ message: string; data: Record<string, unknown> }>(
            `/favorites/organize/clean-invalid?session_id=${sessionId}`,
            {
                method: "POST",
                body: JSON.stringify({ folder_id: folderId }),
            }
        ),
};

// 知识库相关
export const knowledgeApi = {
    // 获取统计信息
    getStats: () => request<KnowledgeStats>("/knowledge/stats"),

    // 构建知识库
    build: (data: BuildRequest, sessionId: string) =>
        request<{ task_id: string; message: string }>(
            `/knowledge/build?session_id=${sessionId}`,
            {
                method: "POST",
                body: JSON.stringify(data),
            }
        ),

    // 获取构建状态
    getBuildStatus: (taskId: string) =>
        request<BuildStatus>(`/knowledge/build/status/${taskId}`),

    // 获取收藏夹入库状态
    getFolderStatus: (sessionId: string) =>
        request<FolderStatus[]>(`/knowledge/folders/status?session_id=${sessionId}`),

    // 同步收藏夹到向量库
    syncFolders: (data: SyncRequest, sessionId: string) =>
        request<SyncResult[]>(
            `/knowledge/folders/sync?session_id=${sessionId}`,
            {
                method: "POST",
                body: JSON.stringify(data),
            }
        ),

    // 清空知识库
    clear: () =>
        request<{ message: string }>("/knowledge/clear", { method: "DELETE" }),

    // 删除视频
    deleteVideo: (bvid: string) =>
        request<{ message: string }>(`/knowledge/video/${bvid}`, { method: "DELETE" }),

    // 导出视频 Markdown
    exportMarkdown: (
        bvid: string,
        mode: "original" | "ai",
        sessionId: string,
        operationId: string,
        signal?: AbortSignal
    ) =>
        requestBlob(
            `/knowledge/video/${encodeURIComponent(bvid)}/export?session_id=${encodeURIComponent(sessionId)}`,
            {
                method: "POST",
                body: JSON.stringify({ mode, operation_id: operationId }),
                signal,
            }
        ),

    // 单视频入库
    ingestVideo: (
        bvid: string,
        folderId: number,
        sessionId: string,
        operationId: string,
        signal?: AbortSignal
    ) =>
        request<{ bvid: string; title: string; message: string }>(
            `/knowledge/video/${encodeURIComponent(bvid)}/ingest?session_id=${encodeURIComponent(sessionId)}`,
            {
                method: "POST",
                body: JSON.stringify({ folder_id: folderId, operation_id: operationId }),
                signal,
            }
        ),

    // 取消单视频导出或入库
    cancelOperation: (operationId: string, sessionId: string) =>
        request<{ message: string }>(
            `/knowledge/operations/${encodeURIComponent(operationId)}/cancel?session_id=${encodeURIComponent(sessionId)}`,
            { method: "POST" }
        ),
};

// 对话相关
export const chatApi = {
    // 提问
    ask: (question: string, sessionId?: string, folderIds?: number[]) =>
        request<ChatResponse>("/chat/ask", {
            method: "POST",
            body: JSON.stringify({ question, session_id: sessionId, folder_ids: folderIds }),
        }),

    // 搜索
    search: (query: string, k = 5) =>
        request<{ results: Array<{ bvid: string; title: string; url: string; content_preview: string }> }>(
            `/chat/search?query=${encodeURIComponent(query)}&k=${k}`,
            { method: "POST" }
        ),
};
