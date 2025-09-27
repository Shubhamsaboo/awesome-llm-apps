import React, { useState, useRef, useEffect } from 'react';
import {
   Image,
   Video,
   FileText,
   Volume2,
   ChevronLeft,
   ChevronRight,
   Play,
   X,
   Users,
   Calendar,
   Sparkles,
   Globe,
   ExternalLink,
} from 'lucide-react';
import api from '../services/api';

const SourceIcon = ({ url }) => {
   const [iconUrl, setIconUrl] = useState(null);
   const [isIconReady, setIsIconReady] = useState(false);
   const defaultIconSvg = (
      <ExternalLink className="w-3 h-3 text-emerald-400 transition-transform duration-200 group-hover:scale-110" />
   );

   useEffect(() => {
      let isMounted = true;
      const preloadFavicon = () => {
         try {
            const domain = new URL(url).hostname;
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
            const img = new Image();
            img.src = faviconUrl;
            img.onload = () => {
               if (isMounted) {
                  setIconUrl(faviconUrl);
                  setIsIconReady(true);
               }
            };
            img.onerror = () => {
               if (isMounted) {
                  setIconUrl(null);
                  setIsIconReady(true);
               }
            };
         } catch (e) {
            if (isMounted) {
               setIconUrl(null);
               setIsIconReady(true);
            }
         }
      };
      preloadFavicon();
      return () => {
         isMounted = false;
      };
   }, [url]);
   if (!isIconReady || !iconUrl) {
      return defaultIconSvg;
   }
   return (
      <img
         src={iconUrl}
         alt="Source icon"
         className="w-3 h-3 object-contain transition-transform duration-200 group-hover:scale-110"
      />
   );
};

const ActivePodcastPreview = React.memo(
   ({
      podcastTitle,
      bannerUrl,
      scriptContent,
      audioUrl,
      webSearchRecording,
      sessionId,
      onClose,
      bannerImages,
      generatedScript,
      sources,
   }) => {
      const [showRecordingPlayer, setShowRecordingPlayer] = useState(false);
      const [activeTab, setActiveTab] = useState('banner');
      const [currentBannerIndex, setCurrentBannerIndex] = useState(0);
      const bannerRef = useRef(null);
      const sourcesRef = useRef(null);
      const recordingRef = useRef(null);
      const scriptRef = useRef(null);
      const audioRef = useRef(null);
      const allBannerImages =
         bannerImages && bannerImages.length > 0
            ? bannerImages.map(img => `${api.API_BASE_URL}/podcast_img/${img}`)
            : bannerUrl
            ? [bannerUrl]
            : [];
      const scriptData = generatedScript || null;
      const hasStructuredScript = scriptData && scriptData.sections;

      const scrollToSection = sectionId => {
         setActiveTab(sectionId);
         const refs = {
            banner: bannerRef,
            sources: sourcesRef,
            recording: recordingRef,
            script: scriptRef,
            audio: audioRef,
         };
         if (refs[sectionId]?.current) {
            refs[sectionId].current.scrollIntoView({ behavior: 'smooth' });
         }
      };
      const handleRecordingButtonClick = () => {
         setShowRecordingPlayer(true);
      };
      const getSpeakers = () => {
         if (!hasStructuredScript) return [];
         const speakers = new Set();
         scriptData.sections.forEach(section => {
            if (section.dialog) {
               section.dialog.forEach(line => speakers.add(line.speaker));
            }
         });
         return Array.from(speakers);
      };
      const getTotalLines = () => {
         if (!hasStructuredScript) return null;
         return scriptData.sections.reduce(
            (total, section) => total + (section.dialog ? section.dialog.length : 0),
            0
         );
      };
      const handleBannerPrevious = () => {
         setCurrentBannerIndex(prev => (prev === 0 ? allBannerImages.length - 1 : prev - 1));
      };
      const handleBannerNext = () => {
         setCurrentBannerIndex(prev => (prev + 1) % allBannerImages.length);
      };
      let recordingUrl = null;
      if (webSearchRecording && sessionId) {
         const filename = webSearchRecording.split('/').pop();
         recordingUrl = `${api.API_BASE_URL}/stream-recording/${sessionId}/${filename}`;
      }
      const SectionHeader = ({ title, icon, id, subtitle }) => (
         <div
            ref={
               id === 'banner'
                  ? bannerRef
                  : id === 'sources'
                  ? sourcesRef
                  : id === 'recording'
                  ? recordingRef
                  : id === 'script'
                  ? scriptRef
                  : audioRef
            }
            className="mb-4"
         >
            <div className="flex items-center gap-2 mb-2">
               <div className="p-1.5 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-lg">
                  {React.cloneElement(icon, { className: 'w-4 h-4 text-emerald-400' })}
               </div>
               <div>
                  <h3 className="text-sm font-semibold text-white">{title}</h3>
                  {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
               </div>
            </div>
         </div>
      );
      const EmptyContent = ({ message = 'No content yet', icon: Icon }) => (
         <div className="w-full h-24 bg-gradient-to-br from-gray-800/50 to-gray-700/50 rounded-xl border border-gray-700/50 flex flex-col items-center justify-center">
            {Icon && <Icon className="w-6 h-6 text-gray-500 mb-1" />}
            <p className="text-xs text-gray-500">{message}</p>
         </div>
      );
      const TabNav = () => (
         <div className="flex items-center justify-around px-4 py-3 border-b border-gray-700/30 bg-gradient-to-r from-gray-900/80 to-gray-800/80 backdrop-blur sticky top-0 z-10">
            <NavigationButton
               isActive={activeTab === 'banner'}
               onClick={() => scrollToSection('banner')}
               icon={<Image />}
               label="Banner"
            />
            {sources && sources.length > 0 && (
               <NavigationButton
                  isActive={activeTab === 'sources'}
                  onClick={() => scrollToSection('sources')}
                  icon={<Globe />}
                  label="Sources"
               />
            )}
            {recordingUrl && (
               <NavigationButton
                  isActive={activeTab === 'recording'}
                  onClick={() => scrollToSection('recording')}
                  icon={<Video />}
                  label="Browser"
               />
            )}
            <NavigationButton
               isActive={activeTab === 'script'}
               onClick={() => scrollToSection('script')}
               icon={<FileText />}
               label="Script"
            />
            <NavigationButton
               isActive={activeTab === 'audio'}
               onClick={() => scrollToSection('audio')}
               icon={<Volume2 />}
               label="Audio"
            />
         </div>
      );
      const NavigationButton = ({ isActive, onClick, icon, label }) => (
         <button
            onClick={onClick}
            className={`flex flex-col items-center px-2 py-1 rounded-md transition-all duration-200 ${
               isActive
                  ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/30'
                  : 'text-gray-400 hover:text-emerald-300 hover:bg-gray-700/30'
            }`}
         >
            {React.cloneElement(icon, {
               className: `w-3 h-3 ${isActive ? 'text-emerald-400' : 'text-gray-400'}`,
            })}
            <span className="text-[10px] mt-0.5 font-medium leading-tight">{label}</span>
         </button>
      );
      const SpeakerColors = {
         ALEX: 'from-slate-600 to-slate-700',
         MORGAN: 'from-gray-600 to-gray-700',
         default: 'from-zinc-600 to-zinc-700',
      };
      const getSpeakerColor = speaker => {
         return SpeakerColors[speaker] || SpeakerColors.default;
      };

      return (
         <div className="h-full flex flex-col relative bg-gradient-to-br from-gray-900 via-gray-850 to-gray-800">
            {!showRecordingPlayer && (
               <>
                  <div className="px-4 py-3 border-b border-gray-700/30">
                     <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                           <div className="inline-flex items-center px-2 py-1 rounded-lg bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/30">
                              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></div>
                              <span className="text-xs font-medium text-emerald-300">Active</span>
                           </div>
                        </div>
                        {onClose && (
                           <button
                              onClick={onClose}
                              className="p-1.5 text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-700/50 rounded-lg transition-all duration-200"
                           >
                              <X className="w-4 h-4" />
                           </button>
                        )}
                     </div>
                     <div className="mt-2">
                        <h2 className="text-sm font-semibold text-white truncate">
                           {podcastTitle}
                        </h2>
                        <p className="text-xs text-gray-400 mt-0.5">Live Preview</p>
                     </div>
                  </div>

                  <TabNav />

                  <div className="overflow-y-auto flex-1 custom-scrollbar px-4 py-4 space-y-6">
                     <div>
                        <SectionHeader
                           title="Podcast Banner"
                           icon={<Image />}
                           id="banner"
                           subtitle={
                              allBannerImages.length > 1
                                 ? `${allBannerImages.length} banners available`
                                 : undefined
                           }
                        />
                        {allBannerImages.length > 0 ? (
                           <div className="relative group">
                              <div className="aspect-video overflow-hidden rounded-xl border border-gray-700/30 bg-gray-800/50">
                                 <img
                                    src={allBannerImages[currentBannerIndex]}
                                    alt={`${podcastTitle} Banner ${currentBannerIndex + 1}`}
                                    className="w-full h-full object-cover transition-all duration-300 group-hover:scale-105"
                                 />
                              </div>
                              {allBannerImages.length > 1 && (
                                 <>
                                    <button
                                       onClick={handleBannerPrevious}
                                       className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-black/60 hover:bg-black/80 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200"
                                    >
                                       <ChevronLeft className="w-5 h-5" />
                                    </button>
                                    <button
                                       onClick={handleBannerNext}
                                       className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-black/60 hover:bg-black/80 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200"
                                    >
                                       <ChevronRight className="w-5 h-5" />
                                    </button>
                                    <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1">
                                       {allBannerImages.map((_, index) => (
                                          <button
                                             key={index}
                                             onClick={() => setCurrentBannerIndex(index)}
                                             className={`w-2 h-2 rounded-full transition-all duration-200 ${
                                                index === currentBannerIndex
                                                   ? 'bg-emerald-500 scale-125'
                                                   : 'bg-white/50 hover:bg-white/75'
                                             }`}
                                          />
                                       ))}
                                    </div>
                                 </>
                              )}
                           </div>
                        ) : (
                           <EmptyContent message="No banner yet" icon={Image} />
                        )}
                     </div>

                     {sources && sources.length > 0 && (
                        <div>
                           <SectionHeader
                              title="Research Sources"
                              icon={<Globe />}
                              id="sources"
                              subtitle={`${sources.length} sources used for podcast creation`}
                           />
                           <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl border border-gray-700/30 overflow-hidden">
                              <div className="p-3 border-b border-gray-700/30 bg-gray-800/30">
                                 <div className="flex items-center justify-between">
                                    <div className="text-xs text-gray-300">Research materials</div>
                                    <div className="text-xs text-gray-400">
                                       {sources.length} sources
                                    </div>
                                 </div>
                              </div>

                              <div className="p-3 max-h-64 overflow-y-auto custom-scrollbar">
                                 <div className="space-y-3">
                                    {sources.map((source, index) => (
                                       <div
                                          key={index}
                                          className="bg-gray-800/30 rounded-lg p-3 border border-gray-700/30"
                                       >
                                          <div className="flex items-start gap-2">
                                             <div className="flex-shrink-0 pt-0.5">
                                                {source.url && <SourceIcon url={source.url} />}
                                             </div>
                                             <div className="flex-1 min-w-0">
                                                <h4 className="text-xs font-medium text-white truncate">
                                                   <span className="text-emerald-400 mr-1">
                                                      {index + 1}.
                                                   </span>
                                                   {source.title}
                                                </h4>
                                                {source.url && (
                                                   <a
                                                      href={source.url}
                                                      target="_blank"
                                                      rel="noopener noreferrer"
                                                      className="text-xs text-emerald-400 hover:text-emerald-300 truncate block mt-1"
                                                   >
                                                      {new URL(source.url).hostname}
                                                   </a>
                                                )}
                                                {source.description && (
                                                   <p className="text-xs text-gray-400 mt-1 line-clamp-2 leading-relaxed">
                                                      {source.description}
                                                   </p>
                                                )}
                                                {source.published_date && (
                                                   <div className="flex items-center gap-1 mt-1">
                                                      <Calendar className="w-3 h-3 text-gray-500" />
                                                      <span className="text-xs text-gray-500">
                                                         {new Date(
                                                            source.published_date
                                                         ).toLocaleDateString()}
                                                      </span>
                                                   </div>
                                                )}
                                             </div>
                                          </div>
                                       </div>
                                    ))}
                                 </div>
                              </div>

                              <div className="px-3 py-2 border-t border-gray-700/30 bg-gray-800/30">
                                 <div className="flex items-center gap-2 text-emerald-400">
                                    <Globe className="w-3 h-3" />
                                    <span className="text-xs">
                                       All research sources used in podcast creation
                                    </span>
                                 </div>
                              </div>
                           </div>
                        </div>
                     )}

                     {recordingUrl && (
                        <div>
                           <SectionHeader
                              title="Browser Use Recording"
                              icon={<Video />}
                              id="recording"
                              subtitle="Browser usage process captured"
                           />
                           <button
                              onClick={handleRecordingButtonClick}
                              className="w-full group bg-gradient-to-r from-gray-800/50 to-gray-700/50 hover:from-gray-700/50 hover:to-gray-600/50 rounded-xl border border-gray-700/30 p-4 flex items-center justify-between transition-all duration-200 hover:border-gray-600/50"
                           >
                              <div className="flex items-center gap-3">
                                 <div className="p-2 bg-emerald-500/20 rounded-lg group-hover:bg-emerald-500/30 transition-colors">
                                    <Play className="w-5 h-5 text-emerald-400" />
                                 </div>
                                 <div className="text-left">
                                    <p className="text-xs text-gray-400">
                                       View Browser Use Recording
                                    </p>
                                 </div>
                              </div>
                              <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-400 transition-colors" />
                           </button>
                        </div>
                     )}

                     <div>
                        <SectionHeader
                           title="Podcast Script"
                           icon={<FileText />}
                           id="script"
                           subtitle={
                              hasStructuredScript
                                 ? `${scriptData.sections.length} sections • ${
                                      getSpeakers().length
                                   } speakers • ${getTotalLines()} lines`
                                 : 'Generated podcast script'
                           }
                        />
                        {hasStructuredScript ? (
                           <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl border border-gray-700/30 overflow-hidden">
                              <div className="p-3 border-b border-gray-700/30 bg-gray-800/30">
                                 <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-xs text-gray-300">
                                       <Users className="w-3 h-3" />
                                       <span>{getSpeakers().length} speakers</span>
                                    </div>
                                    <div className="text-xs text-gray-400">
                                       {getTotalLines()} dialogue lines
                                    </div>
                                 </div>
                              </div>

                              <div className="p-3 max-h-64 overflow-y-auto custom-scrollbar">
                                 <div className="space-y-3">
                                    {scriptData.sections.map((section, sectionIndex) => (
                                       <div key={sectionIndex}>
                                          <div className="mb-2">
                                             <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">
                                                {section.type}
                                                {section.title && ` - ${section.title}`}
                                             </h4>
                                             <div className="h-px bg-gradient-to-r from-emerald-500/30 to-transparent mt-1" />
                                          </div>

                                          {section.dialog && (
                                             <div className="space-y-2">
                                                {section.dialog.map((line, lineIndex) => (
                                                   <div key={lineIndex} className="space-y-1">
                                                      <div
                                                         className={`inline-block px-2 py-0.5 text-xs font-medium bg-gradient-to-r ${getSpeakerColor(
                                                            line.speaker
                                                         )} text-white rounded-full`}
                                                      >
                                                         {line.speaker}
                                                      </div>
                                                      <p className="text-xs text-gray-300 leading-relaxed pl-1">
                                                         {line.text}
                                                      </p>
                                                   </div>
                                                ))}
                                             </div>
                                          )}
                                       </div>
                                    ))}
                                 </div>
                              </div>

                              <div className="px-3 py-2 border-t border-gray-700/30 bg-gray-800/30">
                                 <div className="flex items-center gap-2 text-emerald-400">
                                    <Sparkles className="w-3 h-3" />
                                    <span className="text-xs">
                                       Complete structured script with all sections
                                    </span>
                                 </div>
                              </div>
                           </div>
                        ) : scriptContent ? (
                           <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl border border-gray-700/30 overflow-hidden">
                              <div className="p-3 max-h-64 overflow-y-auto custom-scrollbar">
                                 <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words font-mono leading-relaxed">
                                    {scriptContent}
                                 </pre>
                              </div>
                              <div className="px-3 py-2 border-t border-gray-700/30 bg-gray-800/30">
                                 <div className="flex items-center gap-2 text-emerald-400">
                                    <FileText className="w-3 h-3" />
                                    <span className="text-xs">
                                       Complete script content • Scroll to view all
                                    </span>
                                 </div>
                              </div>
                           </div>
                        ) : (
                           <EmptyContent message="No script yet" icon={FileText} />
                        )}
                     </div>

                     <div>
                        <SectionHeader
                           title="Podcast Audio"
                           icon={<Volume2 />}
                           id="audio"
                           subtitle="High-quality podcast audio"
                        />
                        {audioUrl ? (
                           <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl border border-gray-700/30 p-4">
                              <audio controls src={audioUrl} className="w-full h-12">
                                 Your browser does not support the audio element.
                              </audio>
                           </div>
                        ) : (
                           <EmptyContent message="No audio yet" icon={Volume2} />
                        )}
                     </div>
                  </div>

                  {audioUrl && (
                     <div className="border-t border-gray-700/30 p-3 bg-gradient-to-r from-gray-900/90 to-gray-800/90 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                           <div className="flex items-center gap-2">
                              <div className="p-1.5 bg-emerald-500/20 rounded-lg">
                                 <Volume2 className="w-3 h-3 text-emerald-400" />
                              </div>
                              <div className="min-w-0 flex-1">
                                 <p className="text-xs font-medium text-white truncate">
                                    {podcastTitle}
                                 </p>
                                 <p className="text-xs text-gray-400">Ready</p>
                              </div>
                           </div>
                           <button
                              onClick={() => scrollToSection('audio')}
                              className="px-2 py-1 text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-lg transition-all duration-200 border border-emerald-500/30"
                           >
                              Play
                           </button>
                        </div>
                     </div>
                  )}
               </>
            )}

            {showRecordingPlayer && recordingUrl && (
               <div className="absolute inset-0 bg-black/90 backdrop-blur-sm z-40 flex flex-col animate-fadeIn">
                  <div className="w-full h-full flex flex-col">
                     <div className="p-6 border-b border-gray-700/30 flex items-center justify-between flex-shrink-0">
                        <div className="flex items-center gap-3">
                           <div className="p-2 bg-emerald-500/20 rounded-lg">
                              <Video className="w-5 h-5 text-emerald-400" />
                           </div>
                           <div>
                              <h3 className="text-xs font-semibold text-white">
                                 Browser Use Recording
                              </h3>
                              <p style={{ fontSize: '9px' }} className="text-xs text-gray-400">
                                 View Browser Use Recording
                              </p>
                           </div>
                        </div>
                        <button
                           onClick={() => setShowRecordingPlayer(false)}
                           className="p-2 text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-700/50 rounded-lg transition-all duration-200"
                        >
                           <X className="w-6 h-6" />
                        </button>
                     </div>
                     <div className="relative w-full bg-black flex-grow max-h-[300px]">
                        <video
                           className="w-full h-full object-contain"
                           src={recordingUrl}
                           controls
                           autoPlay
                        >
                           Your browser does not support the video tag.
                        </video>
                     </div>
                     <div className="p-6 border-t border-gray-700/30 flex-shrink-0">
                        <p className="text-xs text-gray-400 mb-4">
                           This is one part of the search process agent used.
                        </p>
                        <div className="flex justify-end">
                           <button
                              onClick={() => setShowRecordingPlayer(false)}
                              className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium rounded-lg transition-all duration-200"
                           >
                              Close
                           </button>
                        </div>
                     </div>
                  </div>
               </div>
            )}

            <style jsx>{`
               @keyframes fadeIn {
                  from {
                     opacity: 0;
                  }
                  to {
                     opacity: 1;
                  }
               }
               .animate-fadeIn {
                  animation: fadeIn 0.2s ease-out forwards;
               }
               .custom-scrollbar {
                  scrollbar-width: thin;
                  scrollbar-color: rgba(75, 85, 99, 0.5) transparent;
               }
               .custom-scrollbar::-webkit-scrollbar {
                  width: 4px;
               }
               .custom-scrollbar::-webkit-scrollbar-track {
                  background: transparent;
               }
               .custom-scrollbar::-webkit-scrollbar-thumb {
                  background-color: rgba(75, 85, 99, 0.5);
                  border-radius: 20px;
               }
            `}</style>
         </div>
      );
   }
);

ActivePodcastPreview.displayName = 'ActivePodcastPreview';

export default ActivePodcastPreview;
