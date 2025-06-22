import React from 'react';

const ProgressIndicator = ({ progress, message, type, elapsed }) => {
   const progressWidth = `${progress}%`;
   const formatElapsedTime = seconds => {
      if (!seconds) return '';

      if (seconds < 60) {
         return `${seconds}s`;
      } else {
         const minutes = Math.floor(seconds / 60);
         const remainingSeconds = seconds % 60;
         return `${minutes}m ${remainingSeconds}s`;
      }
   };
   const getTypeDisplayName = type => {
      const typeMap = {
         chat_processing: 'message',
         script_generation: 'podcast script',
         banner_generation: 'podcast banner',
         audio_generation: 'podcast audio',
         web_search: 'web search',
         embedding_search: 'content search',
         chat: 'message',
      };
      return typeMap[type] || type || 'request';
   };
   const displayType = getTypeDisplayName(type);
   const elapsedFormatted = formatElapsedTime(elapsed);

   return (
      <div className="mb-4 px-4 py-3 bg-gray-800/80 border border-gray-700 text-gray-200 text-sm rounded-md shadow-md">
         <div className="flex flex-col">
            <div className="flex items-center mb-2">
               <div className="mr-2 h-4 w-4 relative">
                  <svg
                     className="animate-spin"
                     viewBox="0 0 24 24"
                     fill="none"
                     xmlns="http://www.w3.org/2000/svg"
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
               </div>
               <span className="font-medium flex-grow">{`Processing ${displayType}...`}</span>
               {progress > 0 && (
                  <span className="ml-2 text-xs bg-gray-700 px-2 py-0.5 rounded-full">
                     {progress}%
                  </span>
               )}
               {elapsedFormatted && (
                  <span className="ml-2 text-xs text-gray-400">{elapsedFormatted}</span>
               )}
            </div>
            {message && !message.includes(`Processing ${displayType}`) && (
               <p className="text-xs text-gray-300 ml-6 mb-2">{message}</p>
            )}
            <div className="w-full bg-gray-700 rounded-full h-2 ml-6 overflow-hidden">
               <div
                  className="bg-emerald-500 h-2 rounded-full transition-all duration-300 ease-out"
                  style={{ width: progressWidth }}
               ></div>
            </div>
         </div>
      </div>
   );
};

export default ProgressIndicator;
