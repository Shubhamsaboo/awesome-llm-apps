import React, { useState, useEffect, useRef } from 'react';
import { Download, Check, Loader2, Volume2, Sparkles, Play } from 'lucide-react';

const AudioConfirmation = ({ audioUrl, topic, onApprove, isProcessing }) => {
   const [isPlaying, setIsPlaying] = useState(false);
   const audioRef = useRef(null);

   const handleDownload = () => {
      const a = document.createElement('a');
      a.href = audioUrl;
      a.download = `${topic.replace(/\s+/g, '-').toLowerCase()}-podcast.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
   };

   useEffect(() => {
      const audio = audioRef.current;
      if (!audio) return;

      const handlePlay = () => setIsPlaying(true);
      const handlePause = () => setIsPlaying(false);
      const handleEnded = () => setIsPlaying(false);

      audio.addEventListener('play', handlePlay);
      audio.addEventListener('pause', handlePause);
      audio.addEventListener('ended', handleEnded);

      return () => {
         audio.removeEventListener('play', handlePlay);
         audio.removeEventListener('pause', handlePause);
         audio.removeEventListener('ended', handleEnded);
      };
   }, []);

   const generateFrequencyBars = count => {
      return Array.from({ length: count }, (_, i) => ({
         id: i,
         height: Math.random() * 100 + 20,
         delay: i * 100,
      }));
   };
   const frequencyBars = generateFrequencyBars(48);

   return (
      <div className="w-full max-w-2xl mx-auto">
         <div className="bg-gradient-to-br from-gray-900 via-gray-850 to-gray-800 rounded-lg overflow-hidden shadow-xl border border-gray-700/50 transition-all duration-300 hover:shadow-2xl">
            <div className="relative px-3 py-2 bg-gradient-to-r from-gray-800/80 to-gray-900/80 backdrop-blur border-b border-gray-700/30">
               <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5" />
               <div className="relative flex items-center gap-2">
                  <div
                     className={`p-1 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-md transition-all duration-300 ${
                        isPlaying ? 'scale-110 shadow-lg shadow-emerald-500/25' : ''
                     }`}
                  >
                     <Volume2
                        className={`w-3 h-3 text-emerald-400 transition-all duration-300 ${
                           isPlaying ? 'scale-110' : ''
                        }`}
                     />
                  </div>
                  <div>
                     <h3 className="text-sm font-semibold text-white">Audio Preview</h3>
                     <p className="text-xs text-gray-400 flex items-center gap-1.5">
                        "{topic}"
                        {isPlaying && (
                           <span className="flex items-center gap-0.5 text-emerald-400">
                              <Play className="w-2 h-2" />
                              <span className="text-[10px]">Playing</span>
                           </span>
                        )}
                     </p>
                  </div>
               </div>
            </div>
            <div className="px-3 py-3">
               <div className="relative">
                  <div className="absolute inset-0 overflow-hidden rounded-lg">
                     <div className="flex items-end justify-center h-full gap-1 p-3">
                        {frequencyBars.map(bar => (
                           <div
                              key={bar.id}
                              className={`bg-gradient-to-t from-emerald-600/30 to-teal-400/30 rounded-full transition-all duration-300 ${
                                 isPlaying ? 'animate-pulse' : 'opacity-40'
                              }`}
                              style={{
                                 width: '3px',
                                 height: isPlaying ? `${bar.height}%` : '20%',
                                 animationDelay: `${bar.delay}ms`,
                                 animationDuration: `${1000 + Math.random() * 1000}ms`,
                              }}
                           />
                        ))}
                     </div>
                  </div>
                  {isPlaying && (
                     <div className="absolute inset-0 rounded-lg">
                        <div className="absolute inset-0 border-2 border-emerald-500/20 rounded-lg animate-ping" />
                        <div className="absolute inset-2 border border-emerald-400/10 rounded-lg animate-pulse" />
                     </div>
                  )}
                  <div className="relative bg-gradient-to-r from-gray-800/90 to-gray-700/90 rounded-lg p-3 border border-gray-600/30 backdrop-blur-sm">
                     <audio
                        ref={audioRef}
                        controls
                        className="w-full h-10 outline-none focus:outline-none"
                        style={{
                           backgroundColor: 'transparent',
                        }}
                     >
                        <source src={audioUrl} type="audio/mpeg" />
                        Your browser does not support the audio element.
                     </audio>
                  </div>
                  <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-emerald-500/5 to-teal-500/5 pointer-events-none" />
               </div>
               <div className="mt-2 flex items-center justify-center gap-1 h-8 overflow-hidden">
                  {Array.from({ length: 32 }, (_, i) => (
                     <div
                        key={i}
                        className={`bg-gradient-to-t from-emerald-500/40 to-teal-400/40 rounded-full transition-all duration-200 ${
                           isPlaying ? 'animate-bounce' : 'animate-pulse opacity-30'
                        }`}
                        style={{
                           width: '3px',
                           height: isPlaying ? `${Math.random() * 80 + 20}%` : '15%',
                           animationDelay: `${i * 50}ms`,
                           animationDuration: `${800 + Math.random() * 600}ms`,
                        }}
                     />
                  ))}
               </div>
               <div className="mt-2 text-center">
                  <p className="text-xs text-gray-400 flex items-center justify-center gap-1.5">
                     <Sparkles
                        className={`w-3 h-3 transition-all duration-300 ${
                           isPlaying ? 'text-emerald-400' : ''
                        }`}
                     />
                     Audio ready
                     {isPlaying && (
                        <span className="ml-1 px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] rounded-full">
                           ♪ Playing
                        </span>
                     )}
                  </p>
               </div>
            </div>
            <div className="px-3 py-2 bg-gradient-to-r from-gray-900/50 to-gray-800/50 backdrop-blur border-t border-gray-700/30">
               <div className="flex gap-3 justify-center">
                  <button
                     onClick={handleDownload}
                     disabled={isProcessing}
                     className="group flex-1 max-w-32 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-600 hover:to-gray-500 text-white text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105 hover:shadow-lg border border-gray-600/30 disabled:opacity-50 disabled:cursor-not-allowed"
                     aria-disabled={isProcessing}
                  >
                     <Download className="w-4 h-4 group-hover:scale-110 transition-transform" />
                     Download
                  </button>
                  <button
                     onClick={onApprove}
                     disabled={isProcessing}
                     className={`group flex-1 max-w-40 flex items-center justify-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-emerald-500/25 border border-emerald-500/30 ${
                        isProcessing ? 'opacity-70 cursor-not-allowed' : ''
                     }`}
                     aria-disabled={isProcessing}
                  >
                     {isProcessing ? (
                        <>
                           <Loader2 className="w-4 h-4 animate-spin" />
                           <span>Processing...</span>
                        </>
                     ) : (
                        <>
                           <Check className="w-4 h-4 group-hover:scale-110 transition-transform" />
                           <span>Sounds Great!</span>
                        </>
                     )}
                  </button>
               </div>
               <div className="mt-1.5 text-center">
                  <p className="text-xs text-gray-400">
                     {isPlaying ? '🎵 Audio visualization active' : 'Use the controls to preview'}
                  </p>
               </div>
            </div>
            {isPlaying && (
               <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden rounded-lg">
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72">
                     <div
                        className="absolute inset-0 border border-emerald-500/10 rounded-full animate-ping"
                        style={{ animationDuration: '3s' }}
                     />
                     <div
                        className="absolute inset-6 border border-teal-400/10 rounded-full animate-ping"
                        style={{ animationDuration: '2s', animationDelay: '0.5s' }}
                     />
                     <div
                        className="absolute inset-12 border border-emerald-300/10 rounded-full animate-ping"
                        style={{ animationDuration: '4s', animationDelay: '1s' }}
                     />
                  </div>
               </div>
            )}
         </div>
      </div>
   );
};

export default AudioConfirmation;
