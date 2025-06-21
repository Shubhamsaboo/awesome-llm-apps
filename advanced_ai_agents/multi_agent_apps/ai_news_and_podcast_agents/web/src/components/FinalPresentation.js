import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const FinalPresentation = ({
   podcastTitle,
   bannerUrl,
   audioUrl,
   recordingUrl,
   scriptContent,
   sessionId,
   onNewPodcast,
   isScriptModalOpen,
   onToggleScriptModal,
   podcastId,
}) => {
   const [isAudioPlaying, setIsAudioPlaying] = useState(false);
   const handleAudioPlay = () => setIsAudioPlaying(true);
   const handleAudioPause = () => setIsAudioPlaying(false);
   const handleAudioEnded = () => setIsAudioPlaying(false);

   return (
      <div className="space-y-4 overflow-hidden">
         <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
            <div className="flex items-center">
               <div className="flex-shrink-0 w-7 h-7 rounded-full bg-emerald-900/30 flex items-center justify-center mr-2.5">
                  <svg
                     className="w-3.5 h-3.5 text-emerald-500"
                     viewBox="0 0 20 20"
                     fill="currentColor"
                  >
                     <path
                        fillRule="evenodd"
                        clipRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                     />
                  </svg>
               </div>
               <div>
                  <h1 className="text-md font-medium text-gray-100">Your Podcast is Ready!</h1>
                  <p className="text-xs text-gray-400">
                     All podcast assets have been generated and are ready to use
                  </p>
               </div>
            </div>
            <button
               onClick={onNewPodcast}
               className="flex items-center text-xs bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-gray-300 py-1.5 px-3 rounded-sm border border-gray-700 shadow-sm self-start sm:self-center"
            >
               <svg className="w-3.5 h-3.5 mr-1.5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                     fillRule="evenodd"
                     d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                     clipRule="evenodd"
                  />
               </svg>
               Create New Podcast
            </button>
         </div>
         <div className="py-2 overflow-auto scrollbar-hide-when-inactive animate-fadeIn">
            <div className="flex flex-col md:flex-row gap-6">
               <div className="md:w-1/3 flex flex-col space-y-4">
                  <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md shadow-md overflow-hidden flex flex-col">
                     {bannerUrl ? (
                        <div className="overflow-hidden border-b border-gray-700 max-h-48">
                           <img
                              src={bannerUrl}
                              alt={podcastTitle}
                              className="w-full h-auto object-cover"
                              style={{ maxHeight: '12rem' }}
                           />
                        </div>
                     ) : (
                        <div className="h-32 bg-gradient-to-b from-gray-700 to-gray-800 flex items-center justify-center border-b border-gray-700">
                           <svg
                              className="h-10 w-10 text-gray-600"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                           >
                              <path
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                                 strokeWidth={1}
                                 d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                              />
                           </svg>
                        </div>
                     )}
                     <div className="p-3 flex-grow flex flex-col">
                        <h2 className="text-sm font-medium text-white mb-2 line-clamp-2">
                           {podcastTitle}
                        </h2>

                        {audioUrl && (
                           <div className="mt-1 mb-3">
                              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">
                                 Podcast Audio
                              </p>
                              <audio
                                 className="w-full h-8"
                                 controls
                                 src={audioUrl}
                                 onPlay={handleAudioPlay}
                                 onPause={handleAudioPause}
                                 onEnded={handleAudioEnded}
                              ></audio>
                           </div>
                        )}
                     </div>
                     <button
                        onClick={onToggleScriptModal}
                        className="w-full bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 border-t border-gray-700 text-xs flex items-center justify-center transition-colors mt-auto"
                     >
                        <svg
                           className="w-3.5 h-3.5 mr-1.5 text-gray-400"
                           fill="none"
                           viewBox="0 0 24 24"
                           stroke="currentColor"
                        >
                           <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                           />
                        </svg>
                        View Script
                     </button>
                  </div>
                  {recordingUrl && (
                     <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md shadow-md overflow-hidden">
                        <div className="p-2.5 border-b border-gray-700 bg-gradient-to-r from-gray-900 to-gray-800">
                           <h2 className="text-xs font-medium text-white flex items-center">
                              <svg
                                 className="w-3.5 h-3.5 mr-1.5 text-emerald-500"
                                 viewBox="0 0 20 20"
                                 fill="currentColor"
                              >
                                 <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm4.555 2.168A1 1 0 006 9v2a1 1 0 001.555.832l3-1.5a1 1 0 000-1.664l-3-1.5z" />
                              </svg>
                             Browser Use Recording
                           </h2>
                        </div>
                        <div className="p-3">
                           <p className="text-xs text-gray-400 mb-2">
                            Agents browser use recording
                           </p>
                           <div className="aspect-video rounded-sm overflow-hidden border border-gray-700 bg-black">
                              <video
                                 className="w-full h-full object-contain"
                                 controlsList="nodownload"
                                 controls
                                 preload="metadata"
                                 src={recordingUrl}
                              ></video>
                           </div>
                        </div>
                     </div>
                  )}
               </div>
               <div className="md:w-2/3 flex flex-col space-y-4">
                  {podcastId && (
                     <div className="bg-gradient-to-r from-emerald-900/40 to-emerald-900/10 border border-emerald-700/30 rounded-md p-3 flex items-start">
                        <div className="flex-shrink-0 w-4 h-4 text-emerald-400 mt-0.5">
                           <svg viewBox="0 0 20 20" fill="currentColor">
                              <path
                                 fillRule="evenodd"
                                 clipRule="evenodd"
                                 d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2h2a1 1 0 100-2H9z"
                              />
                           </svg>
                        </div>
                        <div className="ml-2.5 flex-1">
                           <p className="text-xs text-emerald-300">
                              Your podcast has been saved to the podcast library. You can now access
                              it from the
                              <Link
                                 to="/podcasts"
                                 className="font-medium text-emerald-400 hover:text-emerald-300 underline ml-1"
                              >
                                 Podcasts page
                              </Link>
                           </p>
                           <div className="mt-1.5">
                              <Link
                                 to={`/podcasts/${podcastId}`}
                                 className="inline-flex items-center px-2.5 py-1 bg-emerald-800/40 hover:bg-emerald-800 text-emerald-200 text-xs rounded-sm border border-emerald-700/50 transition-colors"
                              >
                                 <svg
                                    className="w-3.5 h-3.5 mr-1"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                 >
                                    <path
                                       strokeLinecap="round"
                                       strokeLinejoin="round"
                                       strokeWidth={2}
                                       d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                    />
                                    <path
                                       strokeLinecap="round"
                                       strokeLinejoin="round"
                                       strokeWidth={2}
                                       d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                                    />
                                 </svg>
                                 View in Podcast Library
                              </Link>
                           </div>
                        </div>
                     </div>
                  )}
                  <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md shadow-md">
                     <div className="p-2.5 border-b border-gray-700 bg-gradient-to-r from-gray-900 to-gray-800">
                        <h2 className="text-xs font-medium text-white">Quick Actions</h2>
                     </div>
                     <div className="p-3 grid grid-cols-2 gap-2">
                        <Link
                           to="/podcasts"
                           className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 rounded-sm py-1.5 px-3 text-xs flex items-center justify-center"
                        >
                           <svg
                              className="w-3.5 h-3.5 mr-1"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                           >
                              <path
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                                 strokeWidth={2}
                                 d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                              />
                           </svg>
                           Browse Podcasts
                        </Link>
                        <button
                           onClick={onNewPodcast}
                           className="bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-sm py-1.5 px-3 text-xs flex items-center justify-center"
                        >
                           <svg
                              className="w-3.5 h-3.5 mr-1"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                           >
                              <path
                                 fillRule="evenodd"
                                 d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                                 clipRule="evenodd"
                              />
                           </svg>
                           New Podcast
                        </button>
                        {audioUrl && (
                           <a
                              href={audioUrl}
                              download={`${podcastTitle.replace(/\s+/g, '_')}.wav`}
                              className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 rounded-sm py-1.5 px-3 text-xs flex items-center justify-center"
                           >
                              <svg
                                 className="w-3.5 h-3.5 mr-1"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                              >
                                 <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                                 />
                              </svg>
                              Download Audio
                           </a>
                        )}
                        <button
                           onClick={onToggleScriptModal}
                           className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 rounded-sm py-1.5 px-3 text-xs flex items-center justify-center"
                        >
                           <svg
                              className="w-3.5 h-3.5 mr-1"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                           >
                              <path
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                                 strokeWidth={2}
                                 d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                              />
                           </svg>
                           View Script
                        </button>
                     </div>
                  </div>
                  <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md shadow-md">
                     <div className="p-2.5 border-b border-gray-700 bg-gradient-to-r from-gray-900 to-gray-800">
                        <h2 className="text-xs font-medium text-white">What's Next?</h2>
                     </div>
                     <div className="p-3">
                        <p className="text-xs text-gray-300 mb-2">
                           Your podcast has been successfully created! Here are some things you can
                           do now:
                        </p>
                        <div className="space-y-2">
                           <div className="flex items-start">
                              <div className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-emerald-900/30 text-emerald-500 mr-2">
                                 <svg
                                    className="w-2.5 h-2.5"
                                    viewBox="0 0 20 20"
                                    fill="currentColor"
                                 >
                                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                                    <path
                                       fillRule="evenodd"
                                       clipRule="evenodd"
                                       d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                                    />
                                 </svg>
                              </div>
                              <div>
                                 <h3 className="text-xs font-medium text-white">
                                    Browse Your Podcast
                                 </h3>
                                 <p className="text-xs text-gray-400 text-xs">
                                    View your podcast in the library.
                                 </p>
                              </div>
                           </div>
                           <div className="flex items-start">
                              <div className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-emerald-900/30 text-emerald-500 mr-2">
                                 <svg
                                    className="w-2.5 h-2.5"
                                    viewBox="0 0 20 20"
                                    fill="currentColor"
                                 >
                                    <path
                                       fillRule="evenodd"
                                       clipRule="evenodd"
                                       d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                                    />
                                 </svg>
                              </div>
                              <div>
                                 <h3 className="text-xs font-medium text-white">
                                    Create Another Podcast
                                 </h3>
                                 <p className="text-xs text-gray-400 text-xs">
                                    Start a new podcast on a different topic.
                                 </p>
                              </div>
                           </div>
                           <div className="flex items-start">
                              <div className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-emerald-900/30 text-emerald-500 mr-2">
                                 <svg
                                    className="w-2.5 h-2.5"
                                    viewBox="0 0 20 20"
                                    fill="currentColor"
                                 >
                                    <path
                                       fillRule="evenodd"
                                       clipRule="evenodd"
                                       d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                                    />
                                 </svg>
                              </div>
                              <div>
                                 <h3 className="text-xs font-medium text-white">Download Assets</h3>
                                 <p className="text-xs text-gray-400 text-xs">
                                    Download the audio or script for other platforms.
                                 </p>
                              </div>
                           </div>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
         </div>
         {isScriptModalOpen && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
               <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl animate-fadeIn">
                  <div className="p-3 border-b border-gray-700 bg-gradient-to-r from-gray-900 to-gray-800 flex items-center justify-between">
                     <h3 className="text-sm font-medium text-white">Podcast Script</h3>
                     <button
                        onClick={onToggleScriptModal}
                        className="text-gray-400 hover:text-white transition-colors"
                     >
                        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                           <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                  </div>
                  <div className="p-4 overflow-y-auto flex-1">
                     <div className="prose prose-invert prose-emerald max-w-none">
                        <pre className="whitespace-pre-wrap font-sans text-sm text-gray-300 bg-gray-900 p-4 rounded-md border border-gray-700">
                           {scriptContent}
                        </pre>
                     </div>
                  </div>
                  <div className="p-3 border-t border-gray-700 bg-gradient-to-r from-gray-900 to-gray-800 flex justify-end">
                     <button
                        onClick={onToggleScriptModal}
                        className="bg-gray-800 hover:bg-gray-700 text-gray-200 px-3 py-1.5 rounded-sm border border-gray-700 text-xs"
                     >
                        Close
                     </button>
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
               animation: fadeIn 0.2s ease-out;
            }
         `}</style>
      </div>
   );
};

export default FinalPresentation;
