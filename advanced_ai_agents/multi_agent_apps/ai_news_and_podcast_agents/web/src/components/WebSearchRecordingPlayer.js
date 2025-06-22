import React, { useEffect, useState } from 'react';
import api from '../services/api';

const WebSearchRecordingPlayer = ({ sessionId, recordingPath, onClose, isProcessing }) => {
   const [videoUrl, setVideoUrl] = useState('');
   const [isLoading, setIsLoading] = useState(true);
   const [error, setError] = useState(null);

   useEffect(() => {
      if (!recordingPath) {
         setError('No recording available');
         setIsLoading(false);
         return;
      }
      if (!sessionId) {
         console.error('SessionId is missing when constructing recording URL');
         setError('Session ID missing. Cannot play recording.');
         setIsLoading(false);
         return;
      }
      try {
         const pathParts = recordingPath.split('/');
         const filename = pathParts[pathParts.length - 1];
         const streamUrl = `${api.API_BASE_URL}/stream-recording/${sessionId}/${filename}`;
         setVideoUrl(streamUrl);
         setIsLoading(false);
      } catch (error) {
         console.error('Error constructing video URL:', error);
         setError('Failed to prepare the recording for playback.');
         setIsLoading(false);
      }
   }, [recordingPath, sessionId]);

   if (isLoading) {
      return (
         <div className="mb-4 fade-in">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 backdrop-blur-sm border border-gray-700 rounded-sm overflow-hidden shadow-lg">
               <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
                  <div className="text-sm font-medium text-white flex items-center">
                     <svg
                        className="h-4 w-4 mr-1.5 text-emerald-500"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                     >
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                        <path
                           fillRule="evenodd"
                           d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                           clipRule="evenodd"
                        />
                     </svg>
                     Web Search Recording
                  </div>
                  <button
                     onClick={onClose}
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
               <div className="p-4 flex items-center justify-center">
                  <div className="flex items-center space-x-2">
                     <svg
                        className="animate-spin h-5 w-5 text-emerald-500"
                        viewBox="0 0 24 24"
                        fill="none"
                     >
                        <circle
                           className="opacity-25"
                           cx="12"
                           cy="12"
                           r="10"
                           stroke="currentColor"
                           strokeWidth="4"
                        />
                        <path
                           className="opacity-75"
                           fill="currentColor"
                           d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                     </svg>
                     <span className="text-gray-300">Loading web search recording...</span>
                  </div>
               </div>
            </div>
         </div>
      );
   }

   if (error) {
      return (
         <div className="mb-4 fade-in">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 backdrop-blur-sm border border-gray-700 rounded-sm overflow-hidden shadow-lg">
               <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
                  <div className="text-sm font-medium text-white flex items-center">
                     <svg
                        className="h-4 w-4 mr-1.5 text-emerald-500"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                     >
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                        <path
                           fillRule="evenodd"
                           d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                           clipRule="evenodd"
                        />
                     </svg>
                     Web Search Recording
                  </div>
                  <button
                     onClick={onClose}
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
               <div className="p-4 text-center">
                  <svg
                     className="h-10 w-10 text-gray-500 mx-auto mb-2"
                     viewBox="0 0 24 24"
                     fill="none"
                     stroke="currentColor"
                  >
                     <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                     />
                  </svg>
                  <p className="text-gray-300 font-medium mb-2">Unable to load recording</p>
                  <p className="text-gray-400 text-sm mb-3">{error}</p>
                  <button
                     onClick={onClose}
                     className="px-4 py-1.5 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-white text-sm font-medium rounded-sm transition"
                  >
                     Continue
                  </button>
               </div>
            </div>
         </div>
      );
   }

   return (
      <div className="mb-4 fade-in">
         <div className="bg-gradient-to-br from-gray-800 to-gray-900 backdrop-blur-sm border border-gray-700 rounded-sm overflow-hidden shadow-lg">
            <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
               <div className="flex items-center">
                  <svg
                     className="h-4 w-4 mr-1.5 text-emerald-500"
                     viewBox="0 0 20 20"
                     fill="currentColor"
                  >
                     <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                     <path
                        fillRule="evenodd"
                        d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                        clipRule="evenodd"
                     />
                  </svg>
                  <span className="text-sm font-medium text-white">Web Search Recording</span>
               </div>
               <div className="flex items-center space-x-2">
                  <div className="text-xs px-2 py-0.5 rounded-sm bg-emerald-900/50 text-emerald-300 border border-emerald-800/50">
                     AI Search Process
                  </div>
                  <button
                     onClick={onClose}
                     disabled={isProcessing}
                     className={`text-gray-400 hover:text-white transition-colors ${
                        isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                     }`}
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
            </div>
            <div className="relative aspect-video max-h-96 w-full bg-black">
               <video className="w-full h-full" src={videoUrl} controls autoPlay>
                  Your browser does not support the video tag.
               </video>
            </div>
            <div className="px-4 py-3 bg-gradient-to-r from-gray-800 to-gray-900 flex justify-between items-center">
               <div className="text-xs text-gray-400">
                  Watch how AI searched the web for podcast content
               </div>
               <button
                  onClick={onClose}
                  disabled={isProcessing}
                  className={`px-3 py-1.5 text-xs bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white font-medium rounded-sm transition flex items-center ${
                     isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
               >
                  {isProcessing ? 'Processing...' : 'Close Player'}
               </button>
            </div>
         </div>
      </div>
   );
};

export default WebSearchRecordingPlayer;
