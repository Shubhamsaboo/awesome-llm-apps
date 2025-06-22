import React from 'react';

const PodcastAssetsToggle = ({ isVisible, onClick }) => {
   return (
      <button
         onClick={onClick}
         className={`
        relative p-2 rounded-md transition-all duration-300 overflow-hidden
        backdrop-blur-sm border
        ${
           isVisible
              ? 'bg-emerald-900/20 text-emerald-400 border-emerald-600/30'
              : 'bg-gray-800/30 text-gray-400 hover:text-gray-300 border-gray-700/50'
        }
      `}
         aria-label={isVisible ? 'Hide podcast assets' : 'Show podcast assets'}
         title={isVisible ? 'Hide podcast assets' : 'Show podcast assets'}
      >
         <div
            className={`absolute inset-0 transition-opacity duration-300 ${
               isVisible ? 'opacity-100' : 'opacity-0'
            }`}
         >
            <div className="absolute inset-0 bg-emerald-800/20 blur-sm"></div>
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-600/0 via-emerald-500/80 to-emerald-600/0"></div>
         </div>
         <div className="relative z-10 flex items-center justify-center">
            <svg
               className="h-5 w-5"
               viewBox="0 0 24 24"
               fill="none"
               xmlns="http://www.w3.org/2000/svg"
            >
               {isVisible ? (
                  <>
                     <rect
                        x="3"
                        y="3"
                        width="18"
                        height="18"
                        rx="2"
                        stroke="currentColor"
                        strokeWidth="1.5"
                     />
                     <line
                        x1="15"
                        y1="9"
                        x2="18"
                        y2="9"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                     <line
                        x1="15"
                        y1="12"
                        x2="18"
                        y2="12"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                     <line
                        x1="15"
                        y1="15"
                        x2="18"
                        y2="15"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                     <rect
                        x="6"
                        y="8"
                        width="5"
                        height="5"
                        rx="1"
                        stroke="currentColor"
                        strokeWidth="1.5"
                     />
                     <circle cx="8.5" cy="16" r="1.5" stroke="currentColor" strokeWidth="1.5" />
                  </>
               ) : (
                  <>
                     <rect
                        x="3"
                        y="3"
                        width="18"
                        height="18"
                        rx="2"
                        stroke="currentColor"
                        strokeWidth="1.5"
                     />
                     <path d="M9 3V21" stroke="currentColor" strokeWidth="1.5" />
                     <circle cx="6" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.5" />
                     <circle cx="6" cy="16" r="1.5" stroke="currentColor" strokeWidth="1.5" />
                     <line
                        x1="14"
                        y1="8"
                        x2="18"
                        y2="8"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                     <line
                        x1="12"
                        y1="12"
                        x2="18"
                        y2="12"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                     <line
                        x1="14"
                        y1="16"
                        x2="18"
                        y2="16"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                  </>
               )}
            </svg>
         </div>
      </button>
   );
};
export { PodcastAssetsToggle };
