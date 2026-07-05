"use client";

import { useState, useEffect, useRef, useCallback, useMemo, useSyncExternalStore } from "react";
import LoginModal from "@/components/LoginModal";
import DemoFlowModal from "@/components/DemoFlowModal";
import SourcesPanel from "@/components/SourcesPanel";
import ChatPanel from "@/components/ChatPanel";
import { UserInfo, authApi } from "@/lib/api";

const AUTH_CHANGE_EVENT = "bili-auth-change";

function readStoredAuth() {
  if (typeof window === "undefined") return "";
  const session = localStorage.getItem("bili_session");
  const user = localStorage.getItem("bili_user");
  return session && user ? JSON.stringify({ session, user }) : "";
}

function subscribeStoredAuth(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("storage", callback);
  window.addEventListener(AUTH_CHANGE_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(AUTH_CHANGE_EVENT, callback);
  };
}

function notifyAuthChanged() {
  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
}

export default function Home() {
  const authSnapshot = useSyncExternalStore(subscribeStoredAuth, readStoredAuth, () => "");
  const auth = useMemo(() => {
    if (!authSnapshot) return null;
    try {
      return JSON.parse(authSnapshot) as { session: string; user: string };
    } catch {
      return null;
    }
  }, [authSnapshot]);
  const [showLogin, setShowLogin] = useState(false);
  const [showDemo, setShowDemo] = useState(false);
  const [statsKey, setStatsKey] = useState(0);
  const [selectedFolderIds, setSelectedFolderIds] = useState<number[]>([]);

  // 拖拽调整宽度
  const [leftWidth, setLeftWidth] = useState(320);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLElement>(null);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging || !containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const newWidth = e.clientX - containerRect.left;
    // 限制最小 200px，最大 50% 容器宽度
    const min = 200;
    const max = containerRect.width * 0.5;
    setLeftWidth(Math.max(min, Math.min(max, newWidth)));
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    } else {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const onLogin = (sid: string, info: UserInfo) => {
    setShowLogin(false);
    localStorage.setItem("bili_session", sid);
    localStorage.setItem("bili_user", info.uname);
    notifyAuthChanged();
  };

  const onLogout = () => {
    if (auth?.session) authApi.logout(auth.session).catch(() => { });
    localStorage.removeItem("bili_session");
    localStorage.removeItem("bili_user");
    notifyAuthChanged();
  };

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <div className="brand">
          <div className="brand-mark">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
              <path d="M4 6h16M4 12h16M4 18h10" />
            </svg>
          </div>
          <div>
            <span className="brand-title">BiliMind·收藏夹知识库</span>
            <span className="brand-subtitle">Save • Learn • Ask</span>
          </div>
        </div>

        <div className="topbar-actions">
          {auth?.user ? (
            <>
              <span className="user-chip">
                <span>已登录</span>
                <strong>{auth.user}</strong>
              </span>
              <button onClick={onLogout} className="btn-icon" title="退出">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </>
          ) : (
            <button onClick={() => setShowLogin(true)} className="btn btn-primary">
              扫码登录
            </button>
          )}
        </div>
      </header>

      <main className="app-main">
        {!auth?.session ? (
          <section className="hero">
            <div className="hero-content">
              <span className="hero-kicker">让你的B站收藏夹不再吃灰</span>
              <h1 className="hero-title">把“收藏”变成真正可用的知识</h1>
              <p className="hero-desc">
                很多人收藏了大量学习视频，却迟迟没看、没整理、也找不到重点。<br />
                这里把碎片化内容接入 AI：自动提炼、语义检索、对话式回顾，让收藏真正提升效率。
              </p>

              <div className="hero-actions">
                <button className="btn btn-primary btn-lg" onClick={() => setShowLogin(true)}>
                  扫码登录开始构建
                </button>
                <button className="btn btn-outline" onClick={() => setShowDemo(true)}>
                  体验检索流程
                </button>
              </div>
            </div>

            <div className="hero-features">
              <div className="pipeline-row">
                {[
                  { icon: "1", title: "同步", desc: "接入收藏夹" },
                  { icon: "2", title: "提炼", desc: "整理要点" },
                  { icon: "3", title: "检索", desc: "语义查找" },
                  { icon: "4", title: "回顾", desc: "对话复习" },
                ].map((item, i) => (
                  <div key={i} className="pipeline-card">
                    <span className="pipeline-icon">{item.icon}</span>
                    <div className="pipeline-text">
                      <strong>{item.title}</strong>
                      <span>{item.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        ) : (
          <section className="workspace" ref={containerRef}>
            <aside className="panel panel-sources" style={{ width: leftWidth, flexShrink: 0 }}>
              <SourcesPanel
                sessionId={auth.session}
                onBuildDone={() => setStatsKey((v) => v + 1)}
                onSelectionChange={setSelectedFolderIds}
              />
            </aside>

            {/* 拖拽分隔条 */}
            <div
              className="resizer"
              onMouseDown={handleMouseDown}
              style={{ cursor: "col-resize" }}
            />

            <section className="panel panel-chat" style={{ flex: 1 }}>
              <ChatPanel
                statsKey={statsKey}
                sessionId={auth.session}
                folderIds={selectedFolderIds}
              />
            </section>
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>BiliMind © 2026 · 基于 Bilibili API 构建 · 由 AI 驱动</p>
      </footer>

      <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} onSuccess={onLogin} />
      <DemoFlowModal isOpen={showDemo} onClose={() => setShowDemo(false)} />
    </div>
  );
}
