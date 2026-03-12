"use client";

import { useState, useRef, useEffect, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8890";

interface Video {
  video_id: string;
  filename: string;
  duration: number;
  total_frames: number;
  fps: number;
  video_url?: string;
}

interface Moment {
  timestamp: number;
  frame_num: number;
  video_filename: string;
  video_id: string;
  frame_url: string;
  score: number;
  time_formatted: string;
  description?: string;
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function ScoreIndicator({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    score > 0.85 ? "text-emerald-400" :
    score > 0.7 ? "text-purple-400" :
    score > 0.5 ? "text-amber-400" : "text-zinc-500";
  const bg =
    score > 0.85 ? "bg-emerald-500" :
    score > 0.7 ? "bg-purple-500" :
    score > 0.5 ? "bg-amber-500" : "bg-zinc-600";

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${bg}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-mono ${color}`}>{pct}%</span>
    </div>
  );
}

export default function Home() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [moments, setMoments] = useState<Moment[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [searchMode, setSearchMode] = useState<"image" | "text">("image");
  const [textQuery, setTextQuery] = useState("");
  const [queryImage, setQueryImage] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null);
  const [videoTimestamp, setVideoTimestamp] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);

  const fetchVideos = async () => {
    try {
      const res = await fetch(`${API}/videos`);
      const data = await res.json();
      setVideos(data.videos);
    } catch {}
  };

  useEffect(() => { fetchVideos(); }, []);

  const handleVideoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    const file = e.target.files[0];
    setUploading(true);
    setUploadProgress("Extracting frames and building visual index...");

    const form = new FormData();
    form.append("file", file);
    form.append("fps", "1");

    try {
      const res = await fetch(`${API}/upload-video`, { method: "POST", body: form });
      const data = await res.json();
      setUploadProgress(`Indexed ${data.frames_extracted} frames from ${formatDuration(data.duration)}`);
      await fetchVideos();
      setSelectedVideo(data.video_id);
    } catch {
      setUploadProgress("Upload failed. Check connection.");
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(""), 5000);
    }
  };

  const runImageSearch = async (file: File) => {
    const reader = new FileReader();
    reader.onload = (ev) => setQueryImage(ev.target?.result as string);
    reader.readAsDataURL(file);

    setLoading(true);
    setMoments([]);
    const t0 = Date.now();

    const form = new FormData();
    form.append("image", file);
    if (selectedVideo) form.append("video_id", selectedVideo);
    form.append("top_k", "5");

    try {
      const res = await fetch(`${API}/find-moment`, { method: "POST", body: form });
      const data = await res.json();
      setMoments(data.moments || []);
      setElapsed((Date.now() - t0) / 1000);
    } catch {
      setMoments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleImageSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    runImageSearch(e.target.files[0]);
  };

  const handleTextSearch = async () => {
    if (!textQuery.trim()) return;
    setLoading(true);
    setMoments([]);
    setQueryImage(null);
    const t0 = Date.now();

    try {
      const body: any = { query: textQuery, top_k: 5 };
      if (selectedVideo) body.video_id = selectedVideo;
      const res = await fetch(`${API}/find-moment-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setMoments(data.moments || []);
      setElapsed((Date.now() - t0) / 1000);
    } catch {
      setMoments([]);
    } finally {
      setLoading(false);
    }
  };

  const jumpToMoment = (moment: Moment) => {
    setVideoTimestamp(moment.timestamp);
    setSelectedVideo(moment.video_id);
    setTimeout(() => {
      if (videoRef.current) {
        videoRef.current.currentTime = moment.timestamp;
        videoRef.current.play();
      }
    }, 100);
  };

  // Drag and drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith("image/")) {
      runImageSearch(file);
    }
  }, [selectedVideo]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setIsDragging(false), []);

  const activeVideo = videos.find((v) => v.video_id === selectedVideo) || videos[0];
  const totalFrames = videos.reduce((a, v) => a + v.total_frames, 0);

  return (
    <div className="flex flex-col h-screen bg-[#09090b]">
      {/* Header */}
      <header className="glass border-b border-zinc-800/60 px-6 py-3.5 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-purple-400">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          </div>
          <div>
            <h1 className="text-base font-semibold text-zinc-100 tracking-tight">Multimodal Video Moment Finder</h1>
            <p className="text-[11px] text-zinc-500 tracking-wide">
              Gemini Embedding 2 &middot; Visual Matching &middot; Zero Transcription
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {totalFrames > 0 && (
            <div className="flex items-center gap-3 text-[11px] text-zinc-500">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                {videos.length} video{videos.length !== 1 ? "s" : ""}
              </span>
              <span>{totalFrames.toLocaleString()} frames</span>
            </div>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Video + Controls */}
        <div className="w-[55%] border-r border-zinc-800/40 flex flex-col">
          {/* Video Player */}
          <div className="flex-1 bg-black/40 flex items-center justify-center relative">
            {activeVideo ? (
              <video
                ref={videoRef}
                src={`${API}${activeVideo.video_url}`}
                controls
                className="max-w-full max-h-full"
              />
            ) : (
              <div className="text-center px-8">
                <div className="w-16 h-16 rounded-2xl bg-zinc-800/50 border border-zinc-700/50 flex items-center justify-center mx-auto mb-4">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-zinc-600">
                    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
                    <line x1="7" y1="2" x2="7" y2="22" />
                    <line x1="17" y1="2" x2="17" y2="22" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <line x1="2" y1="7" x2="7" y2="7" />
                    <line x1="2" y1="17" x2="7" y2="17" />
                    <line x1="17" y1="7" x2="22" y2="7" />
                    <line x1="17" y1="17" x2="22" y2="17" />
                  </svg>
                </div>
                <p className="text-sm text-zinc-500 mb-1">No videos yet</p>
                <p className="text-xs text-zinc-600">Upload a video to start finding moments</p>
              </div>
            )}
            {videoTimestamp !== null && (
              <div className="absolute top-3 right-3 bg-purple-600/90 backdrop-blur text-white text-xs px-2.5 py-1 rounded-full font-medium">
                {formatDuration(videoTimestamp)}
              </div>
            )}
          </div>

          {/* Bottom: Upload + Video List */}
          <div className="p-4 border-t border-zinc-800/40 bg-zinc-950/60">
            <div className="flex items-center gap-3 mb-3">
              <button
                onClick={() => videoInputRef.current?.click()}
                disabled={uploading}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${uploading
                    ? "bg-zinc-800 text-zinc-500 cursor-wait"
                    : "bg-purple-600 hover:bg-purple-500 active:bg-purple-700 text-white shadow-lg shadow-purple-500/10"}
                `}
              >
                <input
                  ref={videoInputRef}
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={handleVideoUpload}
                  disabled={uploading}
                />
                {uploading ? (
                  <span className="flex items-center gap-2">
                    <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-20" />
                      <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                    </svg>
                    Processing...
                  </span>
                ) : "Upload Video"}
              </button>
              {uploadProgress && (
                <span className="text-xs text-zinc-400 animate-fade-up">{uploadProgress}</span>
              )}
            </div>

            {videos.length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-1">
                {videos.map((v) => {
                  const isActive = selectedVideo === v.video_id || (!selectedVideo && v === videos[0]);
                  return (
                    <button
                      key={v.video_id}
                      onClick={() => setSelectedVideo(v.video_id)}
                      className={`
                        shrink-0 px-3 py-2 rounded-lg text-xs transition-all
                        ${isActive
                          ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                          : "bg-zinc-900/60 text-zinc-500 border border-zinc-800 hover:border-zinc-600 hover:text-zinc-300"}
                      `}
                    >
                      <span className="font-medium">{v.filename}</span>
                      <span className="text-zinc-600 ml-1.5">
                        {formatDuration(v.duration)} &middot; {v.total_frames}f
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: Search + Results */}
        <div className="w-[45%] flex flex-col bg-zinc-950/30">
          {/* Search Controls */}
          <div className="p-4 border-b border-zinc-800/40">
            {/* Mode Tabs */}
            <div className="flex gap-1 mb-3 bg-zinc-900/50 p-1 rounded-lg w-fit">
              <button
                onClick={() => setSearchMode("image")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  searchMode === "image"
                    ? "bg-purple-600 text-white shadow-sm"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Image Search
              </button>
              <button
                onClick={() => setSearchMode("text")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  searchMode === "text"
                    ? "bg-purple-600 text-white shadow-sm"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Text Search
              </button>
            </div>

            {/* Search Input */}
            {searchMode === "image" ? (
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => imageInputRef.current?.click()}
                className={`
                  relative rounded-xl cursor-pointer transition-all overflow-hidden
                  ${isDragging
                    ? "border-2 border-purple-500 bg-purple-500/5 drop-zone-active"
                    : "border-2 border-dashed border-zinc-800 hover:border-zinc-600"}
                  ${queryImage ? "p-2" : "p-8"}
                `}
              >
                <input
                  ref={imageInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleImageSearch}
                />
                {queryImage ? (
                  <div className="relative">
                    <img src={queryImage} alt="Query" className="max-h-36 mx-auto rounded-lg" />
                    <button
                      onClick={(e) => { e.stopPropagation(); setQueryImage(null); setMoments([]); }}
                      className="absolute top-1 right-1 w-6 h-6 bg-black/70 rounded-full flex items-center justify-center text-zinc-400 hover:text-white text-xs"
                    >
                      &times;
                    </button>
                  </div>
                ) : (
                  <div className="text-center">
                    <div className="w-10 h-10 rounded-xl bg-zinc-800/50 border border-zinc-700/50 flex items-center justify-center mx-auto mb-3">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-zinc-500">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                        <circle cx="8.5" cy="8.5" r="1.5" />
                        <polyline points="21 15 16 10 5 21" />
                      </svg>
                    </div>
                    <p className="text-sm text-zinc-400 mb-1">Drop an image or click to browse</p>
                    <p className="text-[11px] text-zinc-600">Find the exact moment this image appears in the video</p>
                  </div>
                )}
              </div>
            ) : (
              <form onSubmit={(e) => { e.preventDefault(); handleTextSearch(); }} className="flex gap-2">
                <input
                  value={textQuery}
                  onChange={(e) => setTextQuery(e.target.value)}
                  placeholder='Describe a scene: "person on stage", "aerial view"...'
                  className="flex-1 bg-zinc-900/60 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 focus:border-purple-500/50 transition-colors"
                />
                <button
                  type="submit"
                  disabled={!textQuery.trim() || loading}
                  className="px-5 py-3 bg-purple-600 hover:bg-purple-500 disabled:opacity-30 disabled:hover:bg-purple-600 rounded-xl text-sm font-medium transition-all shadow-lg shadow-purple-500/10"
                >
                  Find
                </button>
              </form>
            )}
          </div>

          {/* Results */}
          <div className="flex-1 overflow-y-auto p-4">
            {/* Loading */}
            {loading && (
              <div className="space-y-3">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="glass rounded-xl p-3 animate-fade-up" style={{ animationDelay: `${i * 100}ms` }}>
                    <div className="flex gap-3">
                      <div className="w-36 h-20 bg-zinc-800/50 rounded-lg shimmer" />
                      <div className="flex-1 space-y-2 py-1">
                        <div className="w-20 h-3 bg-zinc-800/50 rounded shimmer" />
                        <div className="w-32 h-2 bg-zinc-800/30 rounded shimmer" />
                        <div className="w-24 h-2 bg-zinc-800/30 rounded shimmer" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {!loading && moments.length === 0 && !queryImage && (
              <div className="flex flex-col items-center justify-center h-full text-center px-8">
                <div className="w-14 h-14 rounded-2xl bg-zinc-800/30 border border-zinc-800/50 flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-zinc-600">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </div>
                <h3 className="text-sm font-medium text-zinc-400 mb-1.5">Search for any moment</h3>
                <p className="text-xs text-zinc-600 max-w-xs leading-relaxed">
                  Drop a screenshot to find where it appears, or describe a scene in words.
                  Gemini Embedding 2 matches visual content directly across modalities.
                </p>
              </div>
            )}

            {/* Results List */}
            {!loading && moments.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-zinc-400">
                    {moments.length} moment{moments.length !== 1 ? "s" : ""} found
                  </span>
                  {elapsed !== null && (
                    <span className="text-[11px] text-zinc-600">{elapsed.toFixed(1)}s</span>
                  )}
                </div>

                <div className="space-y-2">
                  {moments.map((m, i) => (
                    <button
                      key={`${m.video_id}-${m.frame_num}`}
                      onClick={() => jumpToMoment(m)}
                      className="result-card w-full text-left glass rounded-xl p-3 group animate-fade-up"
                      style={{ animationDelay: `${i * 60}ms` }}
                    >
                      <div className="flex gap-3">
                        {/* Thumbnail */}
                        <div className="relative shrink-0">
                          <img
                            src={`${API}${m.frame_url}`}
                            alt={`Frame at ${m.time_formatted}`}
                            className="w-36 h-20 object-cover rounded-lg"
                            loading="lazy"
                          />
                          <div className="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] font-mono px-1.5 py-0.5 rounded">
                            {m.time_formatted}
                          </div>
                          {i === 0 && (
                            <div className="absolute top-1 left-1 bg-emerald-500/90 text-white text-[10px] font-medium px-1.5 py-0.5 rounded">
                              Best
                            </div>
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0 py-0.5">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-sm font-medium text-zinc-200">
                              {m.time_formatted}
                            </span>
                            <ScoreIndicator score={m.score} />
                          </div>

                          {m.description && (
                            <p className="text-[11px] text-zinc-500 leading-relaxed line-clamp-2 mb-1">
                              {m.description}
                            </p>
                          )}

                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-zinc-600">
                              {m.video_filename}
                            </span>
                            <span className="text-[10px] text-zinc-700">&middot;</span>
                            <span className="text-[10px] text-zinc-600">
                              Frame {m.frame_num}
                            </span>
                          </div>
                        </div>

                        {/* Play indicator */}
                        <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="w-8 h-8 rounded-full bg-purple-600/20 flex items-center justify-center">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" className="text-purple-400 ml-0.5">
                              <polygon points="5 3 19 12 5 21 5 3" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
