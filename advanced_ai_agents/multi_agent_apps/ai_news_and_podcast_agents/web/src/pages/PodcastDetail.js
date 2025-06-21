import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
   ChevronDown,
   ChevronUp,
   Eye,
   FileText,
   Globe,
   Calendar,
   Volume2,
   Play,
   ExternalLink,
   Users,
   Sparkles,
   X,
   Download,
   Edit3,
   Trash2,
   Info,
   Pause,
   ChevronLeft,
   ChevronRight,
} from 'lucide-react';
import apiService from '../services/api';

const formatTtsEngineName = engine => {
   if (!engine) return '';
   return engine;
};

const getLanguageName = code => {
   if (!code) return '';
   return code;
};

const SourceIcon = ({ url }) => {
   const [iconUrl, setIconUrl] = useState(null);
   const [isIconReady, setIsIconReady] = useState(false);
   const defaultIconSvg = (
      <ExternalLink className="w-4 h-4 text-emerald-400 transition-transform duration-200 group-hover:scale-110" />
   );

   useEffect(() => {
      let isMounted = true;
      const preloadFavicon = () => {
         try {
            const domain = new URL(url).hostname;
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
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
         className="w-4 h-4 object-contain transition-transform duration-200"
      />
   );
};

const StackedSourceIcons = ({ sources, maxIcons = 4 }) => {
   const displaySources = sources.slice(0, maxIcons);

   return (
      <div className="flex -space-x-2 mr-2 relative">
         <div className="absolute inset-0 bg-emerald-500/10 blur-md rounded-full"></div>
         {displaySources.map((source, index) => {
            const sourceUrl = typeof source === 'string' ? source : source.url;
            return (
               <div
                  key={index}
                  className="w-6 h-6 rounded-full bg-gradient-to-br from-gray-800 to-gray-700 border border-gray-600/50 flex items-center justify-center overflow-hidden relative group"
                  style={{
                     zIndex: displaySources.length - index,
                     boxShadow: '0 0 0 1px rgba(16, 185, 129, 0.1)',
                  }}
               >
                  <div className="absolute inset-0 bg-emerald-500/0 group-hover:bg-emerald-500/10 transition-all duration-200"></div>
                  <div className="relative z-10 w-4 h-4 flex items-center justify-center">
                     <SourceIcon url={sourceUrl} />
                  </div>
               </div>
            );
         })}
         {sources.length > maxIcons && (
            <div
               className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-600/30 to-teal-600/30 border border-emerald-500/30 flex items-center justify-center text-xs font-medium text-emerald-400"
               style={{ zIndex: 0 }}
            >
               +{sources.length - maxIcons}
            </div>
         )}
      </div>
   );
};

const PodcastDetail = () => {
   const { identifier } = useParams();
   const navigate = useNavigate();
   const [podcast, setPodcast] = useState(null);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [isPlaying, setIsPlaying] = useState(false);
   const [audioError, setAudioError] = useState(null);
   const [waveform, setWaveform] = useState([]);
   const audioRef = useRef(null);
   const animationRef = useRef(null);
   const [showEditModal, setShowEditModal] = useState(false);
   const [isSaving, setIsSaving] = useState(false);
   const [actionError, setActionError] = useState(null);
   const [newTitle, setNewTitle] = useState('');
   const [isFullScriptOpen, setIsFullScriptOpen] = useState(false);
   const [isSourcesOpen, setIsSourcesOpen] = useState(false);
   const [currentBannerIndex, setCurrentBannerIndex] = useState(0);
   const carouselIntervalRef = useRef(null);

   useEffect(() => {
      const fetchPodcast = async () => {
         setLoading(true);
         setError(null);
         setAudioError(null);
         try {
            const response = await apiService.podcasts.getByIdentifier(identifier);
            setPodcast(response.data);
            if (response.data && response.data.podcast && response.data.podcast.title) {
               setNewTitle(response.data.podcast.title);
            }
         } catch (err) {
            setError(`Failed to fetch podcast: ${err.message}`);
         } finally {
            setLoading(false);
         }
      };
      fetchPodcast();
      const initialWaveform = Array.from({ length: 32 }, () => Math.random() * 80 + 20);
      setWaveform(initialWaveform);
      return () => {
         if (animationRef.current) cancelAnimationFrame(animationRef.current);
         if (carouselIntervalRef.current) clearInterval(carouselIntervalRef.current);
      };
   }, [identifier]);
   useEffect(() => {
      if (podcast && podcast.banner_images && podcast.banner_images.length > 1) {
         carouselIntervalRef.current = setInterval(() => {
            setCurrentBannerIndex(prevIndex =>
               prevIndex === podcast.banner_images.length - 1 ? 0 : prevIndex + 1
            );
         }, 5000);
      }
      return () => {
         if (carouselIntervalRef.current) clearInterval(carouselIntervalRef.current);
      };
   }, [podcast]);

   const nextBanner = () => {
      if (!podcast || !podcast.banner_images || podcast.banner_images.length <= 1) return;
      if (carouselIntervalRef.current) clearInterval(carouselIntervalRef.current);
      setCurrentBannerIndex(prevIndex =>
         prevIndex === podcast.banner_images.length - 1 ? 0 : prevIndex + 1
      );
      carouselIntervalRef.current = setInterval(() => {
         setCurrentBannerIndex(prevIndex =>
            prevIndex === podcast.banner_images.length - 1 ? 0 : prevIndex + 1
         );
      }, 5000);
   };

   const prevBanner = () => {
      if (!podcast || !podcast.banner_images || podcast.banner_images.length <= 1) return;
      if (carouselIntervalRef.current) clearInterval(carouselIntervalRef.current);
      setCurrentBannerIndex(prevIndex =>
         prevIndex === 0 ? podcast.banner_images.length - 1 : prevIndex - 1
      );
      carouselIntervalRef.current = setInterval(() => {
         setCurrentBannerIndex(prevIndex =>
            prevIndex === podcast.banner_images.length - 1 ? 0 : prevIndex + 1
         );
      }, 5000);
   };

   useEffect(() => {
      const handleKeyPress = e => {
         if ((e.key === ' ' || e.key === 'k') && audioRef.current) {
            e.preventDefault();
            if (audioRef.current.paused) {
               audioRef.current.play();
            } else {
               audioRef.current.pause();
            }
         } else if (e.key === 'ArrowLeft' && audioRef.current) {
            e.preventDefault();
            audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10);
         } else if (e.key === 'ArrowRight' && audioRef.current) {
            e.preventDefault();
            audioRef.current.currentTime = Math.min(
               audioRef.current.duration,
               audioRef.current.currentTime + 10
            );
         } else if (e.key === 'm' && audioRef.current) {
            e.preventDefault();
            audioRef.current.muted = !audioRef.current.muted;
         }
      };
      window.addEventListener('keydown', handleKeyPress);
      return () => window.removeEventListener('keydown', handleKeyPress);
   }, []);

   useEffect(() => {
      if (isPlaying) {
         const animateWaveform = () => {
            setWaveform(prevWaveform =>
               prevWaveform.map((height, index) => {
                  let newHeight = height + (Math.random() * 20 - 10);
                  newHeight = Math.max(20, Math.min(100, newHeight));
                  return newHeight;
               })
            );
            animationRef.current = requestAnimationFrame(animateWaveform);
         };
         animationRef.current = requestAnimationFrame(animateWaveform);
      } else {
         if (animationRef.current) cancelAnimationFrame(animationRef.current);
      }
      return () => {
         if (animationRef.current) cancelAnimationFrame(animationRef.current);
      };
   }, [isPlaying]);

   const handleGoBack = () => navigate(-1);

   const handleDelete = async () => {
      const confirmDelete = window.confirm(
         'Are you sure you want to delete this podcast? This action cannot be undone.'
      );
      if (!confirmDelete) {
         return;
      }
      try {
         await apiService.podcasts.delete(podcast.podcast.id);
         navigate('/podcasts');
      } catch (err) {
         alert(`Failed to delete podcast: ${err.message}`);
      }
   };

   const handleTitleUpdate = async () => {
      if (!newTitle.trim()) {
         setActionError('Title cannot be empty');
         return;
      }
      setIsSaving(true);
      setActionError(null);
      try {
         const currentContent = { ...podcast.content };
         currentContent.title = newTitle.trim();
         const updateData = {
            title: newTitle.trim(),
            content: currentContent,
         };
         await apiService.podcasts.update(podcast.podcast.id, updateData);
         const refreshedData = await apiService.podcasts.getByIdentifier(identifier);
         setPodcast(refreshedData.data);
         setShowEditModal(false);
      } catch (err) {
         setActionError(`Failed to update title: ${err.message}`);
      } finally {
         setIsSaving(false);
      }
   };

   const formatDate = dateString => {
      if (!dateString) return '';
      const date = new Date(dateString.replace(' ', 'T'));
      if (isNaN(date)) return 'Invalid Date';
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return date.toLocaleDateString(undefined, options);
   };

   const speakerColors = {
      ALEX: 'from-slate-600 to-slate-700',
      MORGAN: 'from-gray-600 to-gray-700',
      default: 'from-zinc-600 to-zinc-700',
   };

   const getSpeakerColor = speaker => {
      return speakerColors[speaker] || speakerColors.default;
   };

   if (loading) {
      return (
         <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
               <div className="w-12 h-12 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
               <p className="text-gray-400">Loading podcast...</p>
            </div>
         </div>
      );
   }

   if (error) {
      return (
         <div className="min-h-screen flex items-center justify-center p-4">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border-l-4 border-red-500 p-4 rounded-sm shadow-sm mb-4 text-red-400">
               {error}
            </div>
         </div>
      );
   }

   if (!podcast) {
      return (
         <div className="min-h-screen flex items-center justify-center bg-gray-900 p-4">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border-l-4 border-yellow-500 p-4 rounded-sm shadow-sm mb-4 text-yellow-300">
               Podcast not found.
            </div>
         </div>
      );
   }

   const { podcast: podcastData, content, audio_url, sources } = podcast;
   const hasAudio = podcastData.audio_generated && audio_url;
   const hasBanner = !!podcastData.banner_img;
   const bannerImages = podcast.banner_images || [];
   const hasBannerCarousel = Array.isArray(bannerImages) && bannerImages.length > 0;
   const hasSources = Array.isArray(sources) && sources.length > 0;
   const hasScript = content && content.sections && content.sections.length > 0;
   let streamingAudioUrl = '';
   if (hasAudio) {
      const originalAudioUrl = audio_url;
      const filename = originalAudioUrl.split('/').pop();
      streamingAudioUrl = `${apiService.API_BASE_URL}/stream-audio/${filename}`;
   }

   return (
      <div className="min-h-screen py-4 px-4 relative overflow-hidden">
         {podcast && podcast.banner_images && podcast.banner_images.length > 0 && (
            <div className="fixed inset-0 w-full h-full z-0">
               <div className="absolute inset-0 w-full h-full opacity-90">
                  <img
                     src={`${apiService.API_BASE_URL}/podcast_img/${podcast.banner_images[currentBannerIndex]}`}
                     alt="Background"
                     className="w-full h-full object-cover blur-xl transition-all duration-1500 ease-in-out bg-banner-background"
                     style={{ transform: 'scale(1.05)' }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-b from-gray-900/90 via-gray-900/80 to-gray-900/95" />
               </div>
            </div>
         )}
         <div className="absolute inset-0 opacity-20">
            <div className="absolute top-20 left-20 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse"></div>
            <div
               className="absolute bottom-20 right-20 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl animate-pulse"
               style={{ animationDelay: '1s' }}
            ></div>
         </div>
         <div className="max-w-lg mx-auto relative z-10">
            <button
               onClick={handleGoBack}
               className="text-gray-300 hover:text-emerald-300 flex items-center mb-3 transition-colors duration-200 group"
            >
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4 mr-1 group-hover:transform group-hover:-translate-x-1 transition-transform duration-200"
                  viewBox="0 0 20 20"
                  fill="currentColor"
               >
                  <path
                     fillRule="evenodd"
                     d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                     clipRule="evenodd"
                  />
               </svg>
               Back
            </button>
            <div className="bg-gradient-to-br from-gray-900/80 via-gray-850/80 to-gray-800/80 rounded-2xl overflow-hidden shadow-2xl border border-gray-700/50 transition-all duration-300 hover:shadow-3xl backdrop-blur-lg">
               {hasBannerCarousel && (
                  <div className="h-65 relative overflow-hidden mb-16">
                     <div className="h-full w-full relative">
                        {bannerImages.map((image, index) => (
                           <div
                              key={index}
                              className={`absolute inset-0 transition-opacity duration-500 ${
                                 currentBannerIndex === index ? 'opacity-100 z-10' : 'opacity-0 z-0'
                              }`}
                           >
                              <img
                                 src={`${apiService.API_BASE_URL}/podcast_img/${image}`}
                                 alt={`Banner ${index + 1}`}
                                 className="w-full h-full object-cover transition-transform duration-700 ease-in-out"
                                 style={{
                                    transform:
                                       currentBannerIndex === index ? 'scale(1)' : 'scale(1.1)',
                                 }}
                              />
                           </div>
                        ))}
                        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/80 to-gray-900/30 z-20" />
                        {bannerImages.length > 1 && (
                           <>
                              <button
                                 onClick={prevBanner}
                                 className="absolute left-4 top-1/2 -translate-y-1/2 z-30 p-2 rounded-full bg-black/30 backdrop-blur-sm text-white/70 hover:text-white hover:bg-black/50 transition-all duration-200 hover:scale-110 border border-white/10 group"
                              >
                                 <ChevronLeft className="w-5 h-5 group-hover:-translate-x-0.5 transition-transform" />
                              </button>
                              <button
                                 onClick={nextBanner}
                                 className="absolute right-4 top-1/2 -translate-y-1/2 z-30 p-2 rounded-full bg-black/30 backdrop-blur-sm text-white/70 hover:text-white hover:bg-black/50 transition-all duration-200 hover:scale-110 border border-white/10 group"
                              >
                                 <ChevronRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
                              </button>
                           </>
                        )}
                        {bannerImages.length > 1 && (
                           <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 flex space-x-2">
                              {bannerImages.map((_, index) => (
                                 <button
                                    key={index}
                                    onClick={() => {
                                       setCurrentBannerIndex(index);
                                       if (carouselIntervalRef.current)
                                          clearInterval(carouselIntervalRef.current);
                                       carouselIntervalRef.current = setInterval(() => {
                                          setCurrentBannerIndex(prevIndex =>
                                             prevIndex === bannerImages.length - 1
                                                ? 0
                                                : prevIndex + 1
                                          );
                                       }, 5000);
                                    }}
                                    className={`w-2 h-2 rounded-full transition-all duration-300 ${
                                       currentBannerIndex === index
                                          ? 'bg-emerald-400 w-6'
                                          : 'bg-white/30 hover:bg-white/50'
                                    }`}
                                    aria-label={`Go to slide ${index + 1}`}
                                 />
                              ))}
                           </div>
                        )}
                     </div>
                  </div>
               )}
               {!hasBannerCarousel && hasBanner && (
                  <div className="h-80 relative overflow-hidden mb-16">
                     <img
                        src={`${apiService.API_BASE_URL}/podcast_img/${podcastData.banner_img}`}
                        alt={content.title || 'Podcast'}
                        className="w-full h-full object-cover"
                     />
                     <div className="absolute inset-0 bg-gradient-to-t from-gray-900/95 via-gray-900/70 to-gray-900/30" />
                  </div>
               )}
               <div
                  className={`${
                     hasBanner || hasBannerCarousel ? 'absolute top-64 left-0 right-0 z-30' : ''
                  } px-4 py-3 bg-gradient-to-r from-gray-800/90 to-gray-900/90 backdrop-blur-md border-b border-gray-700/30`}
               >
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5" />
                  <div className="relative flex justify-between items-center">
                     <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div
                           className={`p-1.5 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-lg transition-all duration-300 ${
                              isPlaying ? 'scale-110 shadow-lg shadow-emerald-500/25' : ''
                           }`}
                        >
                           <Volume2
                              className={`w-4 h-4 text-emerald-400 transition-all duration-300 ${
                                 isPlaying ? 'scale-110' : ''
                              }`}
                           />
                        </div>
                        <div className="min-w-0">
                           <h3 className="text-base font-semibold text-white truncate">
                              {content.title || `Podcast - ${formatDate(podcastData.date)}`}
                           </h3>
                           <p className="text-xs text-gray-400 flex items-center gap-1.5">
                              <Calendar className="w-3 h-3" />
                              {formatDate(podcastData.date)}
                              {isPlaying && (
                                 <span className="flex items-center gap-1 text-emerald-400 ml-1">
                                    <Play className="w-2.5 h-2.5" />
                                    <span className="text-xs">Playing</span>
                                 </span>
                              )}
                           </p>
                        </div>
                     </div>
                     <div className="flex gap-1">
                        <button
                           onClick={() => setShowEditModal(true)}
                           className="p-1.5 text-gray-400 hover:text-blue-400 transition-all duration-200 hover:bg-gray-700/30 rounded"
                           title="Edit Title"
                        >
                           <Edit3 className="w-3.5 h-3.5" />
                        </button>
                        <button
                           onClick={handleDelete}
                           className="p-1.5 text-gray-400 hover:text-red-400 transition-all duration-200 hover:bg-gray-700/30 rounded"
                           title="Delete Podcast"
                        >
                           <Trash2 className="w-3.5 h-3.5" />
                        </button>
                     </div>
                  </div>
               </div>
               <div className="px-4 py-2 mt-16">
                  <div className="flex flex-wrap justify-center gap-1.5">
                     {podcastData.language_code && (
                        <div className="flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-blue-900/80 to-blue-800/80 text-blue-200 border border-blue-800/50">
                           <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-3 w-3 mr-0.5"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                           >
                              <path
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                                 strokeWidth={2}
                                 d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
                              />
                           </svg>
                           <span>{getLanguageName(podcastData.language_code)}</span>
                        </div>
                     )}
                     {podcastData.tts_engine && (
                        <div className="flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-purple-900/80 to-purple-800/80 text-purple-200 border border-purple-800/50">
                           <Sparkles className="w-3 h-3 mr-1" />
                           <span>{formatTtsEngineName(podcastData.tts_engine)}</span>
                        </div>
                     )}
                  </div>
               </div>
               {hasAudio && (
                  <div className="px-4 py-3">
                     <div className="relative">
                        <div className="absolute inset-0 overflow-hidden rounded-lg">
                           <div className="flex items-end justify-center h-full gap-px p-2">
                              {waveform.map((height, index) => (
                                 <div
                                    key={index}
                                    className={`bg-gradient-to-t from-emerald-600/30 to-teal-400/30 rounded-full transition-all duration-300 ${
                                       isPlaying ? 'animate-pulse' : 'opacity-40'
                                    }`}
                                    style={{
                                       width: '2px',
                                       height: isPlaying ? `${height}%` : '20%',
                                       animationDelay: `${index * 30}ms`,
                                       animationDuration: `${1000 + Math.random() * 300}ms`,
                                    }}
                                 />
                              ))}
                           </div>
                        </div>
                        <div className="relative bg-gradient-to-r from-gray-800/90 to-gray-700/90 rounded-lg p-3 border border-gray-600/30 backdrop-blur-sm">
                           {audioError ? (
                              <div className="flex items-center gap-2 text-red-400">
                                 <Info className="w-4 h-4" />
                                 <span className="text-xs">{audioError}</span>
                              </div>
                           ) : (
                              <audio
                                 ref={audioRef}
                                 controls
                                 className="w-full h-8"
                                 src={streamingAudioUrl}
                                 onPlay={() => setIsPlaying(true)}
                                 onPause={() => setIsPlaying(false)}
                                 onEnded={() => setIsPlaying(false)}
                                 onError={e => {
                                    console.error('Audio playback error:', e);
                                    setAudioError('There was an error playing this audio file.');
                                 }}
                              >
                                 Your browser does not support the audio element.
                              </audio>
                           )}
                        </div>
                        {isPlaying && (
                           <div className="absolute inset-0 rounded-lg pointer-events-none">
                              <div className="absolute inset-0 border border-emerald-500/20 rounded-lg animate-ping" />
                              <div className="absolute inset-1 border border-emerald-400/10 rounded-lg animate-pulse" />
                           </div>
                        )}
                     </div>
                     <div className="mt-2 text-center">
                        <p className="text-xs text-gray-400 flex items-center justify-center gap-1.5">
                           <Sparkles
                              className={`w-3 h-3 transition-all duration-300 ${
                                 isPlaying ? 'text-emerald-400' : ''
                              }`}
                           />
                           High-quality podcast audio
                           {isPlaying && (
                              <span className="ml-1 px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded">
                                 ♪ Playing
                              </span>
                           )}
                        </p>
                     </div>
                  </div>
               )}
               <div className="px-4 py-3 bg-gradient-to-r from-gray-900/50 to-gray-800/50 backdrop-blur border-t border-gray-700/30">
                  <div className="flex justify-center gap-3">
                     {hasScript && (
                        <button
                           onClick={() => setIsFullScriptOpen(true)}
                           className="group flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-600 hover:to-gray-500 text-white text-xs font-medium rounded-full transition-all duration-200 hover:scale-105 border border-gray-600/30 relative overflow-hidden"
                        >
                           <div className="absolute inset-0 bg-emerald-500/0 group-hover:bg-emerald-500/10 transition-all duration-200"></div>
                           <div className="p-1 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
                              <FileText className="w-3 h-3 text-emerald-400" />
                           </div>
                           <span className="relative z-10">Script</span>
                        </button>
                     )}
                     {hasSources && (
                        <button
                           onClick={() => setIsSourcesOpen(true)}
                           className="group flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-600 hover:to-gray-500 text-white text-xs font-medium rounded-full transition-all duration-200 hover:scale-105 border border-gray-600/30 relative overflow-hidden"
                        >
                           <div className="absolute inset-0 bg-emerald-500/0 group-hover:bg-emerald-500/10 transition-all duration-200"></div>
                           <StackedSourceIcons sources={sources} />
                           <span className="relative z-10">Sources</span>
                        </button>
                     )}
                  </div>
                  {hasAudio && (
                     <div className="mt-2 text-center">
                        <div className="flex justify-center text-xs text-gray-500 gap-2">
                           <span className="flex items-center gap-1">
                              <kbd className="px-1.5 py-0.5 bg-gray-700/50 rounded text-xs">
                                 Space
                              </kbd>
                              Play
                           </span>
                           <span className="flex items-center gap-1">
                              <kbd className="px-1.5 py-0.5 bg-gray-700/50 rounded text-xs">←→</kbd>
                              Seek
                           </span>
                           <span className="flex items-center gap-1">
                              <kbd className="px-1.5 py-0.5 bg-gray-700/50 rounded text-xs">M</kbd>
                              Mute
                           </span>
                        </div>
                     </div>
                  )}
               </div>
               {isPlaying && hasAudio && (
                  <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden rounded-2xl">
                     <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64">
                        <div
                           className="absolute inset-0 border border-emerald-500/10 rounded-full animate-ping"
                           style={{ animationDuration: '3s' }}
                        />
                        <div
                           className="absolute inset-8 border border-teal-400/10 rounded-full animate-ping"
                           style={{ animationDuration: '2s', animationDelay: '0.5s' }}
                        />
                        <div
                           className="absolute inset-16 border border-emerald-300/10 rounded-full animate-ping"
                           style={{ animationDuration: '4s', animationDelay: '1s' }}
                        />
                     </div>
                  </div>
               )}
            </div>
            {isFullScriptOpen && hasScript && (
               <div className="fixed inset-0 z-50">
                  <div
                     className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                     onClick={() => setIsFullScriptOpen(false)}
                  ></div>
                  <div className="absolute inset-0 flex justify-end">
                     <div
                        className={`w-full sm:w-96 bg-gradient-to-br from-gray-900/95 via-gray-850/95 to-gray-800/95 shadow-2xl border-l border-gray-700/50 backdrop-blur-xl flex flex-col transform transition-transform duration-300 ease-out ${
                           isFullScriptOpen ? 'translate-x-0' : 'translate-x-full'
                        }`}
                     >
                        <div className="px-4 py-3 bg-gradient-to-r from-gray-800/90 to-gray-700/90 border-b border-gray-700/30 backdrop-blur-sm flex-shrink-0">
                           <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5" />
                           <div className="relative flex items-center justify-between">
                              <div className="flex items-center min-w-0 flex-1">
                                 <div className="p-1.5 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-lg mr-3 flex-shrink-0">
                                    <FileText className="w-4 h-4 text-emerald-400" />
                                 </div>
                                 <div className="min-w-0 flex-1">
                                    <h2 className="text-lg font-semibold text-white truncate">
                                       Podcast Script
                                    </h2>
                                    <p className="text-xs text-gray-400 truncate">
                                       {content.title}
                                    </p>
                                 </div>
                              </div>
                              <button
                                 onClick={() => setIsFullScriptOpen(false)}
                                 className="ml-2 p-1.5 text-gray-400 hover:text-white transition-all duration-200 hover:bg-gray-700/30 rounded flex-shrink-0"
                              >
                                 <X className="w-5 h-5" />
                              </button>
                           </div>
                        </div>
                        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800/30">
                           {content.sections.map((section, sectionIndex) => (
                              <div
                                 key={sectionIndex}
                                 className="border-gray-700/20 pb-4 last:border-0"
                              >
                                 <div className="px-4 py-2 bg-gradient-to-r from-gray-800/90 to-gray-700/90 backdrop-blur-sm">
                                    <div className="flex items-center">
                                       <h3 className="text-sm font-medium text-emerald-400">
                                          {section.type?.charAt(0).toUpperCase() +
                                             section.type?.slice(1)}
                                       </h3>
                                    </div>
                                 </div>
                                 {section.dialog && (
                                    <div className="px-4 pt-2">
                                       {section.dialog.map((line, lineIndex) => (
                                          <div key={lineIndex} className="mb-3 last:mb-0">
                                             <div
                                                className={`inline-flex px-2 py-0.5 text-xs font-medium bg-gradient-to-r ${getSpeakerColor(
                                                   line.speaker
                                                )} text-white rounded mb-1`}
                                             >
                                                {line.speaker}
                                             </div>
                                             <div className="text-gray-300 text-sm leading-relaxed">
                                                {line.text}
                                             </div>
                                          </div>
                                       ))}
                                    </div>
                                 )}
                              </div>
                           ))}
                        </div>
                     </div>
                  </div>
               </div>
            )}
            {isSourcesOpen && hasSources && (
               <div className="fixed inset-0 z-50">
                  <div
                     className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                     onClick={() => setIsSourcesOpen(false)}
                  ></div>
                  <div className="absolute inset-0 flex justify-end">
                     <div
                        className={`w-full sm:w-96 bg-gradient-to-br from-gray-900/95 via-gray-850/95 to-gray-800/95 shadow-2xl border-l border-gray-700/50 backdrop-blur-xl flex flex-col transform transition-transform duration-300 ease-out ${
                           isSourcesOpen ? 'translate-x-0' : 'translate-x-full'
                        }`}
                     >
                        <div className="px-4 py-3 bg-gradient-to-r from-gray-800/90 to-gray-700/90 border-b border-gray-700/30 backdrop-blur-sm flex-shrink-0">
                           <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5" />
                           <div className="relative flex items-center justify-between">
                              <div className="flex items-center min-w-0 flex-1">
                                 <div className="p-1.5 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-lg mr-3 flex-shrink-0">
                                    <Globe className="w-4 h-4 text-emerald-400" />
                                 </div>
                                 <h2 className="text-lg font-semibold text-white">Sources</h2>
                              </div>
                              <button
                                 onClick={() => setIsSourcesOpen(false)}
                                 className="ml-2 p-1.5 text-gray-400 hover:text-white transition-all duration-200 hover:bg-gray-700/30 rounded flex-shrink-0"
                              >
                                 <X className="w-5 h-5" />
                              </button>
                           </div>
                        </div>
                        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800/30">
                           {sources.map((source, index) => {
                              const sourceUrl = typeof source === 'string' ? source : source.url;
                              let hostname = '';
                              try {
                                 hostname = new URL(sourceUrl).hostname.replace(/^www\./, '');
                              } catch (e) {
                                 hostname = 'Unknown Source';
                              }
                              return (
                                 <a
                                    key={index}
                                    href={sourceUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block px-4 py-3 border-b border-gray-700/30 hover:bg-gray-800/50 transition-colors group"
                                 >
                                    <div className="flex items-start">
                                       <div className="flex-shrink-0 pt-1">
                                          <div className="p-1.5 bg-gradient-to-br from-gray-800 to-gray-700 rounded-lg flex items-center justify-center group-hover:from-emerald-500/10 group-hover:to-teal-500/10 transition-all duration-200">
                                             <SourceIcon url={sourceUrl} />
                                          </div>
                                       </div>
                                       <div className="ml-3 flex-1 min-w-0">
                                          <h3 className="font-medium text-emerald-400 group-hover:text-emerald-300 transition-colors truncate">
                                             {hostname}
                                          </h3>
                                          <p className="text-sm text-gray-400 mt-1 line-clamp-2 break-all">
                                             {sourceUrl}
                                          </p>
                                          <div className="mt-2 flex items-center text-xs text-gray-500">
                                             <ExternalLink className="w-3 h-3 mr-1 text-emerald-500/70 group-hover:translate-x-0.5 transition-transform duration-200" />
                                             <span className="group-hover:text-gray-400 transition-colors">
                                                View source
                                             </span>
                                          </div>
                                       </div>
                                    </div>
                                 </a>
                              );
                           })}
                        </div>
                     </div>
                  </div>
               </div>
            )}
            {showEditModal && (
               <div className="fixed inset-0 bg-black/80 backdrop-blur-lg flex items-center justify-center z-50 p-4">
                  <div className="bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-2xl shadow-2xl max-w-md w-full p-8">
                     <h3 className="text-xl font-bold text-gray-100 mb-4">Edit Podcast Title</h3>
                     {actionError && (
                        <div className="bg-red-900/30 border border-red-500/50 text-red-300 p-4 mb-4 rounded-xl backdrop-blur-sm">
                           {actionError}
                        </div>
                     )}
                     <div className="mb-6">
                        <label
                           htmlFor="podcastTitle"
                           className="block text-sm font-medium text-gray-300 mb-2"
                        >
                           Title
                        </label>
                        <input
                           type="text"
                           id="podcastTitle"
                           value={newTitle}
                           onChange={e => setNewTitle(e.target.value)}
                           className="w-full px-4 py-3 bg-gray-800/50 border border-gray-600/50 rounded-xl text-gray-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 backdrop-blur-sm transition-all"
                           placeholder="Enter podcast title"
                        />
                     </div>
                     <div className="flex justify-end space-x-3">
                        <button
                           onClick={() => setShowEditModal(false)}
                           className="px-6 py-3 bg-gray-800/50 text-gray-300 rounded-xl hover:bg-gray-700/50 transition-all backdrop-blur-sm border border-gray-700/50"
                           disabled={isSaving}
                        >
                           Cancel
                        </button>
                        <button
                           onClick={handleTitleUpdate}
                           className="px-6 py-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 flex items-center transition-all"
                           disabled={isSaving}
                        >
                           {isSaving ? (
                              <>
                                 <svg
                                    className="animate-spin h-4 w-4 mr-2 text-white"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                 >
                                    <circle
                                       className="opacity-25"
                                       cx="12"
                                       cy="12"
                                       r="10"
                                       stroke="currentColor"
                                       strokeWidth="4"
                                    ></circle>
                                    <path
                                       className="opacity-75"
                                       fill="currentColor"
                                       d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                    ></path>
                                 </svg>
                                 Saving...
                              </>
                           ) : (
                              'Save Changes'
                           )}
                        </button>
                     </div>
                  </div>
               </div>
            )}
         </div>
         <style jsx>{`
            @keyframes slideInRight {
               from {
                  transform: translateX(100%);
               }
               to {
                  transform: translateX(0);
               }
            }

            @keyframes fadeIn {
               from {
                  opacity: 0;
               }
               to {
                  opacity: 1;
               }
            }

            /* Subtle background glow effect */
            @keyframes subtle-background-glow {
               0% {
                  filter: brightness(1) saturate(0.8);
               }
               50% {
                  filter: brightness(1.1) saturate(1);
               }
               100% {
                  filter: brightness(1) saturate(0.8);
               }
            }

            .bg-banner-background {
               animation: subtle-background-glow 10s infinite ease-in-out;
            }
         `}</style>
      </div>
   );
};

export default PodcastDetail;
