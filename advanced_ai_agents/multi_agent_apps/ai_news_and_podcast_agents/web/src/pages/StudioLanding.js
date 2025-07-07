import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import api from '../services/api';

const StudioLanding = () => {
   const [sessionCount, setSessionCount] = useState(0);
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState(null);
   const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
   const navigate = useNavigate();

   useEffect(() => {
      const fetchSessionCount = async () => {
         try {
            const response = await api.podcastAgent.listSessions();
            if (response && Array.isArray(response.data.sessions)) {
               setSessionCount(response.data.sessions.length);
            }
         } catch (error) {
            console.error('Error fetching sessions:', error);
         }
      };
      fetchSessionCount();
      const handleResize = () => {
         if (window.innerWidth >= 768) {
            setIsMobileSidebarOpen(false);
         }
      };
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
   }, []);

   const handleNewSession = async () => {
      try {
         setLoading(true);
         setError(null);
         const response = await api.podcastAgent.createSession(null);
         if (response && response.data.session_id) {
            navigate(`/studio/chat/${response.data.session_id}`);
         } else {
            throw new Error('Failed to create session: No session ID returned');
         }
      } catch (error) {
         console.error('Error creating new session:', error);
         setError(error.message || 'Failed to create new session. Please try again.');
      } finally {
         setLoading(false);
      }
   };

   const sidebarClass = isMobileSidebarOpen
      ? 'translate-x-0 shadow-lg'
      : '-translate-x-full md:translate-x-0';

   return (
      <div className="min-h-screen flex bg-gray-900">
         {isMobileSidebarOpen && (
            <div
               className="fixed inset-0 bg-black/70 z-20 md:hidden"
               onClick={() => setIsMobileSidebarOpen(false)}
               aria-hidden="true"
            />
         )}
         <div
            className={`fixed md:sticky top-0 left-0 h-full md:h-screen w-72 bg-gradient-to-b from-gray-800 to-gray-900 border-r border-gray-700 z-30 transform transition-transform duration-300 ease-in-out ${sidebarClass}`}
         >
            <Sidebar
               onNewSession={handleNewSession}
               onSessionSelect={() => setIsMobileSidebarOpen(false)}
            />
         </div>
         <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-gradient-to-r from-gray-900 to-gray-800 z-10 border-b border-gray-700 flex items-center px-4">
            <button
               className="p-2 text-gray-400 hover:text-white rounded-md hover:bg-gray-700 transition-colors"
               onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
               aria-label={isMobileSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            >
               {isMobileSidebarOpen ? (
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                     />
                  </svg>
               ) : (
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 6h16M4 12h16M4 18h16"
                     />
                  </svg>
               )}
            </button>
            <div className="flex items-center ml-2">
               <div className="w-10 h-10 relative mr-3 flex-shrink-0">
                  <div className="absolute inset-0 flex items-center justify-center z-10">
                     <svg
                        viewBox="0 0 24 24"
                        className="w-7 h-7 text-emerald-500"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                     >
                        <rect x="4" y="4" width="16" height="16" rx="2" />
                        <line x1="8" y1="4" x2="8" y2="20" />
                        <line x1="12" y1="4" x2="12" y2="20" />
                        <line x1="16" y1="4" x2="16" y2="20" />
                        <circle cx="8" cy="9" r="1" fill="currentColor" />
                        <circle cx="12" cy="13" r="1" fill="currentColor" />
                        <circle cx="16" cy="11" r="1" fill="currentColor" />
                     </svg>
                  </div>
                  {/* Glow effect */}
                  <div className="absolute inset-0 bg-emerald-500 opacity-10 rounded-full blur-md"></div>
                  {/* Border */}
                  <div className="absolute inset-0 rounded-full border border-gray-700 bg-gradient-to-r from-gray-800 to-gray-900"></div>
               </div>
               <h1 className="text-lg font-semibold text-white">AI Podcast Studio</h1>
            </div>
         </div>
         <div
            className="flex-1 flex items-center justify-center p-4 md:p-6 md:ml-72 pt-20 md:pt-4"
            style={{ marginLeft: 0 }}
         >
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md shadow-2xl max-w-md w-full p-6 backdrop-blur">
               <div className="relative w-20 h-20 mx-auto mb-6">
                  <div className="absolute inset-0 bg-emerald-500 opacity-5 rounded-full animate-pulse-slow"></div>
                  <div className="absolute inset-0 flex items-center justify-center z-10">
                     <svg
                        viewBox="0 0 24 24"
                        className="w-12 h-12 text-emerald-500"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                     >
                        <rect x="4" y="4" width="16" height="16" rx="2" />
                        <line x1="8" y1="4" x2="8" y2="20" />
                        <line x1="12" y1="4" x2="12" y2="20" />
                        <line x1="16" y1="4" x2="16" y2="20" />
                        <circle cx="8" cy="9" r="2" fill="currentColor" />
                        <circle cx="12" cy="13" r="2" fill="currentColor" />
                        <circle cx="16" cy="11" r="2" fill="currentColor" />
                     </svg>
                  </div>
                  <div className="absolute inset-0 border-2 border-emerald-500/30 rounded-full"></div>
               </div>
               <h1 className="text-2xl font-bold text-white mb-3 text-center">
                  Welcome to AI Podcast Studio
               </h1>
               <p className="text-gray-300 mb-8 text-center">
                  Create professional podcasts from your trusted sources with AI assistance. Choose
                  an existing chat from the sidebar or create a new one to get started.
               </p>
               {error && (
                  <div className="mb-6 p-4 bg-red-900/30 border border-red-800/50 rounded-md text-red-400 text-sm">
                     <div className="flex items-center">
                        <svg
                           className="w-5 h-5 mr-2 flex-shrink-0"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                              clipRule="evenodd"
                           />
                        </svg>
                        <span>{error}</span>
                     </div>
                  </div>
               )}
               <button
                  onClick={handleNewSession}
                  disabled={loading}
                  className={`w-full py-3 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white font-medium rounded-md transition flex items-center justify-center shadow-lg hover:shadow-emerald-900/20 ${
                     loading ? 'opacity-70 cursor-not-allowed' : ''
                  }`}
               >
                  {loading ? (
                     <>
                        <svg
                           className="animate-spin h-5 w-5 mr-2 text-white"
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
                        Creating...
                     </>
                  ) : (
                     <>
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-5 w-5 mr-2"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                              clipRule="evenodd"
                           />
                        </svg>
                        Create New Podcast
                     </>
                  )}
               </button>
               <div className="mt-8 space-y-2">
                  <p className="text-xs text-gray-400 mb-2">With AI Podcast Studio you can:</p>
                  <div className="flex items-start">
                     <div className="h-5 w-5 rounded-full bg-emerald-900/50 border border-emerald-800/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg
                           className="h-3 w-3 text-emerald-400"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </div>
                     <p className="ml-3 text-sm text-gray-300">
                        Generate podcast scripts on any topic
                     </p>
                  </div>
                  <div className="flex items-start">
                     <div className="h-5 w-5 rounded-full bg-emerald-900/50 border border-emerald-800/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg
                           className="h-3 w-3 text-emerald-400"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </div>
                     <p className="ml-3 text-sm text-gray-300">Create custom banner images</p>
                  </div>
                  <div className="flex items-start">
                     <div className="h-5 w-5 rounded-full bg-emerald-900/50 border border-emerald-800/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg
                           className="h-3 w-3 text-emerald-400"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </div>
                     <p className="ml-3 text-sm text-gray-300">
                        Generate professional voice narration
                     </p>
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
};

export default StudioLanding;
