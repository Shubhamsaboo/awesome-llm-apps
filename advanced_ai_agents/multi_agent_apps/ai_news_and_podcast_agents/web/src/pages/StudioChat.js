import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import ChatMessage, { LoadingIndicator } from '../components/ChatMessage';
import SourceSelection from '../components/SourceSelection';
import ScriptConfirmation from '../components/ScriptConfirmation';
import BannerConfirmation from '../components/BannerConfirmation';
import AudioConfirmation from '../components/AudioConfirmation';
import FinalPresentation from '../components/FinalPresentation';
import ActivePodcastPreview from '../components/ActivePodcastPreview';
import { PodcastAssetsToggle } from '../components/AssetPannelToggle';
import api from '../services/api';

const PodcastSession = () => {
   const { sessionId } = useParams();
   const navigate = useNavigate();
   const [messages, setMessages] = useState([]);
   const [inputMessage, setInputMessage] = useState('');
   const [loading, setLoading] = useState(false);
   const [isProcessing, setIsProcessing] = useState(false);
   const [processingType, setProcessingType] = useState(null);
   const [currentTaskId, setCurrentTaskId] = useState(null);
   const [sessionState, setSessionState] = useState({});
   const [currentStage, setCurrentStage] = useState('welcome');
   const [error, setError] = useState(null);
   const [showCompletionModal, setShowCompletionModal] = useState(false);
   const [isPreviewVisible, setIsPreviewVisible] = useState(window.innerWidth >= 1024);
   const [selectedSourceIndices, setSelectedSourceIndices] = useState([]);
   const [isScriptModalOpen, setIsScriptModalOpen] = useState(false);
   const [isFinalScriptModalOpen, setIsFinalScriptModalOpen] = useState(false);
   const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
   const [showRecordingPlayer, setShowRecordingPlayer] = useState(false);
   const [webSearchRecording, setWebSearchRecording] = useState(null);
   const [selectedLanguageCode, setSelectedLanguageCode] = useState('en');
   const [availableLanguages, setAvailableLanguages] = useState([{ code: 'en', name: 'English' }]);
   const chatContainerRef = useRef(null);
   const pollTimerRef = useRef(null);
   const messagesEndRef = useRef(null);
   const inputRef = useRef(null);
   console.log('webSearchRecording', webSearchRecording);
   const hasAutoOpenedRecording = useRef(false);

   useEffect(() => {
      // Auto-open recording player once when webSearchRecording becomes available
      if (webSearchRecording && !hasAutoOpenedRecording.current) {
         console.log('Auto-opening recording player for the first time');
         setShowRecordingPlayer(true);
         if(sessionState.stage === 'search'){
            hasAutoOpenedRecording.current = true;
         }
      }
   }, [webSearchRecording]);

   useEffect(() => {
      if (sessionId) {
         console.log('Session ID available:', sessionId);
         initializeSession(sessionId);
      } else {
         console.error('No sessionId available from URL params!');
      }
      const handleResize = () => {
         setIsPreviewVisible(window.innerWidth >= 1024);
         if (window.innerWidth >= 768) {
            setIsMobileSidebarOpen(false);
         }
      };
      window.addEventListener('resize', handleResize);
      return () => {
         if (pollTimerRef.current) clearInterval(pollTimerRef.current);
         window.removeEventListener('resize', handleResize);
      };
   }, [sessionId]);

   useEffect(() => {
      if (messagesEndRef.current) {
         messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
   }, [messages]);

   useEffect(() => {
      if (sessionState.show_sources_for_selection && sessionState.search_results) {
         setSelectedSourceIndices(
            Array.from({ length: sessionState.search_results.length }, (_, i) => i)
         );
      }
      if (sessionState.show_recording_player !== undefined) {
         setShowRecordingPlayer(sessionState.show_recording_player);
      }
      if (sessionState.available_languages && sessionState.available_languages.length > 0) {
         setAvailableLanguages(sessionState.available_languages);
      }
      if (sessionState.selected_language && sessionState.selected_language.code) {
         setSelectedLanguageCode(sessionState.selected_language.code);
      }
   }, [sessionState]);

   const getLanguages = async () => {
      try {
         const response = await api.podcastAgent.languages();
         if (response?.data && response.data?.languages?.length > 0) {
            setAvailableLanguages(response.data.languages);
         }
      } catch (error) {
         console.error('Error fetching languages:', error);
      }
   };

   const parseSessionState = stateString => {
      if (!stateString) return null;
      try {
         return typeof stateString === 'string' ? JSON.parse(stateString) : stateString;
      } catch (err) {
         console.error('Error parsing session state:', err);
         return null;
      }
   };

   const initializeSession = async id => {
      try {
         setError(null);
         const sessionResponse = await api.podcastAgent.createSession(id);

         // Verify we got a valid session ID back
         if (!sessionResponse?.data?.session_id) {
            throw new Error('Failed to activate session');
         }

         // Ensure we're working with the correct session ID
         const confirmedSessionId = sessionResponse.data.session_id;
         if (confirmedSessionId !== id) {
            console.warn(`Session ID mismatch: Requested ${id}, got ${confirmedSessionId}`);
         }

         const historyData = await api.podcastAgent.getSessionHistory(confirmedSessionId);

         try {
            hasAutoOpenedRecording.current = false;
         } catch (err) {
            console.error('Error resetting auto-open state:', err);
         }

         // Verify history is for the correct session
         if (historyData.data.session_id !== confirmedSessionId) {
            console.error(
               `History session mismatch: Expected ${confirmedSessionId}, got ${historyData.data.session_id}`
            );
            throw new Error('Session validation failed');
         }


         if (historyData.data.browser_recording_path) {
            setWebSearchRecording(historyData.data.browser_recording_path);
         }

         const uniqueMessages =
            historyData.data.messages?.filter(
               (msg, idx, self) =>
                  msg.content &&
                  msg.role &&
                  idx === self.findIndex(m => m.role === msg.role && m.content === msg.content)
            ) || [];

         setMessages(
            uniqueMessages.length
               ? uniqueMessages
               : [
                    {
                       role: 'assistant',
                       content:
                          "Hi there! I'm your podcast creation assistant. What topic would you like to create a podcast about?",
                    },
                 ]
         );

         getLanguages();
         if (historyData.data.is_processing) {
            console.log(
               `Session ${confirmedSessionId} has active processing: ${historyData.data.process_type}`
            );
            setIsProcessing(true);
            setProcessingType(historyData.data.process_type || 'unknown');

            // If we have an active task ID, use it for polling
            if (historyData.data.task_id) {
               setCurrentTaskId(historyData.data.task_id);
               startPollingForCompletion(historyData.data.task_id);
            } else {
               startPollingForCompletion();
            }
         } else {
            setIsProcessing(false);
            setProcessingType(null);
            setCurrentTaskId(null);
         }

         if (historyData.data.state) {
            const parsedState = parseSessionState(historyData.data.state);
            if (parsedState) {
               setSessionState(parsedState);
               setCurrentStage(parsedState.stage || 'welcome');
            }
         }
      } catch (error) {
         console.error('Error initializing session:', error);
         setError('Failed to load session. Please try again.');
         setMessages([
            {
               role: 'assistant',
               content: `Sorry, I couldn't load the session: ${error.message}`,
            },
            {
               role: 'assistant',
               content: "Let's start a new conversation instead.",
            },
         ]);
      }
   };

   const startNewSession = async () => {
      try {
         setError(null);
         setLoading(true);
         setMessages([]);
         setSessionState({});
         setCurrentStage('welcome');
         if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
         }
         setIsProcessing(false);
         setProcessingType(null);
         setCurrentTaskId(null);
         setSelectedSourceIndices([]);
         setIsScriptModalOpen(false);
         setIsFinalScriptModalOpen(false);
         setShowCompletionModal(false);
         setIsMobileSidebarOpen(false);
         setShowRecordingPlayer(false);
         try {
            hasAutoOpenedRecording.current = false;
         } catch (err) {
            console.error('Error resetting auto-open state:', err);
         }
         const response = await api.podcastAgent.createSession(null);
         if (response?.data?.session_id) {
            window.location.href = `/studio/chat/${response.data.session_id}`;
            // navigate(`/studio/chat/${response.data.session_id}`, { replace: true });
            setMessages([
               {
                  role: 'assistant',
                  content:
                     "Hi there! I'm your podcast creation assistant. What topic would you like to create a podcast about?",
               },
            ]);
         } else {
            throw new Error('Failed to create new session - no session ID returned');
         }
      } catch (error) {
         console.error('Error creating new session:', error);
         setError('Failed to create new session. Please try again.');
      } finally {
         setLoading(false);
      }
   };

   const handleSendMessage = async () => {
      if (!inputMessage.trim() || !sessionId || isProcessing) return;
      setInputMessage('');
      const userMessage = { role: 'user', content: inputMessage };
      setMessages(prev => [...prev, userMessage]);
      hideAllConfirmationUIs();

      try {
         setLoading(true);
         const predictedProcessType = predictProcessingType(inputMessage, currentStage);
         if (predictedProcessType) {
            setProcessingType(predictedProcessType);
         }

         // Send message to chat endpoint
         const response = await api.podcastAgent.chat(sessionId, inputMessage);

         // Store the task ID for polling if available
         if (response.data.task_id) {
            setCurrentTaskId(response.data.task_id);
         }

         // Set processing state but don't add a "processing" message to the chat
         setIsProcessing(true);

         // Only update session state if provided
         if (response.data.session_state) {
            updateSessionState(response.data.session_state);
         }

         // Start polling for the final result using task ID if available
         startPollingForCompletion(response.data.task_id);
      } catch (error) {
         console.error('Error sending message:', error);
         setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error.message}` }]);
         setError(`Failed to send message: ${error.message}`);
         setIsProcessing(false);
         setProcessingType(null);
         setCurrentTaskId(null);
      } finally {
         setLoading(false);
      }
   };

   const hideAllConfirmationUIs = useCallback(() => {
      setSessionState(prevState => ({
         ...prevState,
         show_sources_for_selection: false,
         show_script_for_confirmation: false,
         show_banner_for_confirmation: false,
         show_audio_for_confirmation: false,
         show_recording_player: false,
      }));
   }, []);

   const updateSessionState = stateString => {
      const parsedState = parseSessionState(stateString);
      if (parsedState) {
         setSessionState(parsedState);
         setCurrentStage(parsedState.stage || currentStage);
         if (parsedState.podcast_generated) setShowCompletionModal(false);
         if (parsedState.show_recording_player !== undefined) {
            setShowRecordingPlayer(parsedState.show_recording_player);
         }
      }
   };

   const startPollingForCompletion = (taskId = null) => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      const pollInterval = 3000;
      const maxPolls = 100;
      let pollCount = 0;

      // Store the current session ID at poll start time to ensure consistency
      const currentSessionId = sessionId;

      // If a taskId is provided, update the current task ID
      if (taskId) {
         setCurrentTaskId(taskId);
      }

      pollTimerRef.current = setInterval(async () => {
         // First verify we're still on the same session as when polling started
         if (currentSessionId !== sessionId) {
            console.log('Session changed during polling - stopping poll');
            clearInterval(pollTimerRef.current);
            return;
         }

         pollCount++;
         if (pollCount > maxPolls) {
            clearInterval(pollTimerRef.current);
            setIsProcessing(false);
            setProcessingType(null);
            setCurrentTaskId(null);
            setMessages(prev => [
               ...prev,
               { role: 'assistant', content: 'Process timed out. Please try again.' },
            ]);
            return;
         }

         try {
            // Check status using task ID if available
            const statusResponse = await api.podcastAgent.checkStatus(currentSessionId, taskId);
            console.log('Status response:', statusResponse.data);
            // CRITICAL: Verify the response is for our current session
            if (
               statusResponse.data.session_id &&
               statusResponse.data.session_id !== currentSessionId
            ) {
               console.error(
                  `Session ID mismatch! Expected ${currentSessionId}, got ${statusResponse.data.session_id}`
               );
               return; // Skip this cycle
            }

            if (statusResponse.data.browser_recording_path) {
               setWebSearchRecording(statusResponse.data.browser_recording_path);
            }

            // If the task is complete (is_processing is false)
            if (statusResponse.data.is_processing === false) {
               clearInterval(pollTimerRef.current);
               setIsProcessing(false);
               setProcessingType(null);
               setCurrentTaskId(null);

               // Only add the final response to the chat if it's not a processing status message
               if (statusResponse.data.response) {
                  // Don't add processing messages to the chat
                  const responseText = statusResponse.data.response;
                  if (
                     !responseText.includes('being processed') &&
                     !responseText.includes('still being processed') &&
                     !responseText.includes('Please check the status')
                  ) {
                     setMessages(prev => [...prev, { role: 'assistant', content: responseText }]);
                  }
               }

               // Update session state if provided
               if (statusResponse.data.session_state) {
                  updateSessionState(statusResponse.data.session_state);
               }

               
            }
            // If it's still processing but there's a status update
            else if (
               statusResponse.data.process_type &&
               statusResponse.data.process_type !== processingType
            ) {
               setProcessingType(statusResponse.data.process_type);
            }
         } catch (error) {
            console.error('Error polling:', error);
         }
      }, pollInterval);
   };

   const predictProcessingType = useCallback((message, stage) => {
      const lowerMessage = message.toLowerCase();
      if (stage === 'source_selection' && /\d/.test(message)) return 'script generation';
      if (
         stage === 'script' &&
         (lowerMessage.includes('approve') || lowerMessage.includes('looks good'))
      )
         return 'banner generation';
      if (
         stage === 'banner' &&
         (lowerMessage.includes('approve') || lowerMessage.includes('looks good'))
      )
         return 'audio generation';
      return null;
   }, []);

   const handleToggleSourceSelection = useCallback(
      index => {
         if (isProcessing) return;
         setSelectedSourceIndices(prev =>
            prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
         );
      },
      [isProcessing]
   );

   const handleToggleSelectAllSources = useCallback(() => {
      if (isProcessing || !sessionState.search_results) return;
      setSelectedSourceIndices(
         selectedSourceIndices.length === sessionState.search_results.length
            ? []
            : Array.from({ length: sessionState.search_results.length }, (_, i) => i)
      );
   }, [isProcessing, selectedSourceIndices.length, sessionState.search_results]);

   const handleSourceSelectionConfirm = async () => {
      if (isProcessing || selectedSourceIndices.length === 0) {
         setError('Please select at least one source.');
         return;
      }
      const selectedLang = availableLanguages.find(lang => lang.code === selectedLanguageCode);
      const langName = selectedLang ? selectedLang.name : 'English';
      const oneBasedIndices = selectedSourceIndices.map(idx => idx + 1);
      const selectionString = `I've selected sources ${oneBasedIndices.join(
         ', '
      )} and I want the podcast in ${langName}.`;
      setMessages(prev => [...prev, { role: 'user', content: selectionString }]);
      setLoading(true);
      setProcessingType('script generation');

      try {
         // Send message to chat endpoint
         const response = await api.podcastAgent.chat(sessionId, selectionString);

         // Store the task ID for polling if available
         if (response.data.task_id) {
            setCurrentTaskId(response.data.task_id);
         }

         // Set processing state but don't add a "processing" message to the chat
         setIsProcessing(true);

         // Update session state if provided
         if (response.data.session_state) {
            updateSessionState(response.data.session_state);
         }

         // Start polling for the final result
         startPollingForCompletion(response.data.task_id);
      } catch (error) {
         console.error('Error confirming sources:', error);
         setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error.message}` }]);
         setError(`Failed to confirm sources: ${error.message}`);
         setIsProcessing(false);
         setProcessingType(null);
         setCurrentTaskId(null);
      } finally {
         setLoading(false);
      }
   };

   const handleLanguageSelection = useCallback(languageCode => {
      setSelectedLanguageCode(languageCode);
   }, []);

   const handleScriptConfirm = useCallback(() => {
      setSessionState(prevState => ({
         ...prevState,
         show_script_for_confirmation: false,
      }));
      const message = 'I approve this script. It looks good!';
      sendDirectMessage(message);
   }, []);

   const handleBannerConfirm = useCallback(() => {
      setSessionState(prevState => ({
         ...prevState,
         show_banner_for_confirmation: false,
      }));
      const message = 'I approve this banner. It looks good!';
      sendDirectMessage(message);
   }, []);

   const handleAudioConfirm = useCallback(() => {
      setSessionState(prevState => ({
         ...prevState,
         show_audio_for_confirmation: false,
      }));
      const message = "The audio sounds great! I'm happy with the final podcast.";
      sendDirectMessage(message);
   }, []);

   const sendDirectMessage = async message => {
      if (!message.trim() || !sessionId || isProcessing) return;
      setMessages(prev => [...prev, { role: 'user', content: message }]);
      hideAllConfirmationUIs();
      setLoading(true);

      try {
         const predictedProcessType = predictProcessingType(message, currentStage);
         if (predictedProcessType) {
            setProcessingType(predictedProcessType);
         }

         // Send message to chat endpoint
         const response = await api.podcastAgent.chat(sessionId, message);

         // Store the task ID for polling if available
         if (response.data.task_id) {
            setCurrentTaskId(response.data.task_id);
         }

         // Set processing state but don't add a "processing" message to the chat
         setIsProcessing(true);

         // Update session state if provided
         if (response.data.session_state) {
            updateSessionState(response.data.session_state);
         }

         // Start polling for the final result
         startPollingForCompletion(response.data.task_id);
      } catch (error) {
         console.error('Error sending message:', error);
         setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error.message}` }]);
         setError(`Failed to send message: ${error.message}`);
         setIsProcessing(false);
         setProcessingType(null);
         setCurrentTaskId(null);
      } finally {
         setLoading(false);
      }
   };

   const podcastInfo = useMemo(() => {
      let title = 'AI Podcast Studio';
      let scriptText = '';
      let bannerUrl = '';
      let audioUrl = '';
      if (sessionState.generated_script?.title) title = sessionState.generated_script.title;
      else if (sessionState.podcast_info?.topic) title = sessionState.podcast_info.topic;
      if (sessionState.generated_script) {
         if (typeof sessionState.generated_script === 'object') {
            try {
               const scriptLines = [];
               if (sessionState.generated_script.title) {
                  scriptLines.push(sessionState.generated_script.title);
               }
               sessionState.generated_script.sections?.forEach(section => {
                  scriptLines.push(` ${section.title || section.type}\n`);
                  section.dialog?.forEach(line =>
                     scriptLines.push(`[${line.speaker}]: ${line.text}\n`)
                  );
                  scriptLines.push('\n');
               });
               scriptText = scriptLines.join('');
            } catch (error) {
               console.error('Error formatting script:', error);
               scriptText = JSON.stringify(sessionState.generated_script, null, 2);
            }
         } else scriptText = sessionState.generated_script;
      }
      if (sessionState.banner_url) bannerUrl = sessionState.banner_url;
      if (sessionState.audio_url) audioUrl = sessionState.audio_url;
      return { title, scriptText, bannerUrl, audioUrl };
   }, [sessionState]);

   const bannerUrlFull = useMemo(() => {
      return podcastInfo.bannerUrl
         ? `${api.API_BASE_URL}/podcast_img/${podcastInfo.bannerUrl}`
         : '';
   }, [podcastInfo.bannerUrl]);

   const audioUrlFull = useMemo(() => {
      return podcastInfo.audioUrl ? `${api.API_BASE_URL}/audio/${podcastInfo.audioUrl}` : '';
   }, [podcastInfo.audioUrl]);

   const handleClosePreview = useCallback(() => {
      setIsPreviewVisible(false);
   }, []);

   const handleTogglePreview = useCallback(() => {
      setIsPreviewVisible(prev => !prev);
   }, []);

   const showFinalPresentation =
      sessionState.podcast_generated === true &&
      sessionState.stage === 'complete' &&
      sessionState.podcast_id;
   console.log('sessionState.podcast_generated', sessionState.podcast_generated);

   const sidebarClass = isMobileSidebarOpen
      ? 'translate-x-0 shadow-lg'
      : '-translate-x-full md:translate-x-0';
   const contentClass = isPreviewVisible ? 'lg:mr-72' : 'lg:mr-0';

   return (
      <div className="min-h-screen flex bg-[#0A0E14]">
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
               onNewSession={startNewSession}
               onSessionSelect={() => setIsMobileSidebarOpen(false)}
            />
         </div>
         <div
            className={`flex-1 min-h-screen flex flex-col ml-0 md:ml-72 relative ${contentClass} transition-all duration-300`}
            style={{ marginLeft: 0 }}
         >
            <header className="sticky top-0 z-10 bg-[#0A0E14] border-b border-gray-700 shadow-md">
               <div className="h-16 px-4 flex items-center justify-between">
                  <div className="flex items-center">
                     <button
                        className="md:hidden mr-3 p-2 text-gray-400 hover:text-white rounded-md hover:bg-gray-700 transition-colors"
                        onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
                        aria-label={isMobileSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
                     >
                        {isMobileSidebarOpen ? (
                           <svg
                              className="h-6 w-6"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                           >
                              <path
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                                 strokeWidth={2}
                                 d="M6 18L18 6M6 6l12 12"
                              />
                           </svg>
                        ) : (
                           <svg
                              className="h-6 w-6"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                           >
                              <path
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                                 strokeWidth={2}
                                 d="M4 6h16M4 12h16M4 18h16"
                              />
                           </svg>
                        )}
                     </button>
                     <div className="flex items-center">
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
                           <div className="absolute inset-0 bg-emerald-500 opacity-10 rounded-full blur-md"></div>
                           <div className="absolute inset-0 rounded-full border border-gray-700 bg-gradient-to-r from-gray-800 to-gray-900"></div>
                        </div>
                        <h1 className="text-lg font-semibold text-white truncate max-w-[180px] sm:max-w-xs">
                           {podcastInfo.title}
                        </h1>
                     </div>
                  </div>
                  <div className="flex items-center space-x-2">
                     <div className="hidden sm:flex items-center px-3 py-1 bg-[#121824] rounded-full border border-gray-700 text-xs text-gray-300">
                        <span
                           className={`w-2 h-2 rounded-full ${
                              isProcessing ? 'bg-emerald-400 animate-pulse' : 'bg-gray-500'
                           } mr-2`}
                        ></span>
                        <span>
                           {isProcessing
                              ? `Processing ${processingType || ''}...`
                              : `Stage: ${currentStage}`}
                        </span>
                     </div>
                     <PodcastAssetsToggle
                        isVisible={isPreviewVisible}
                        onClick={handleTogglePreview}
                     />
                  </div>
               </div>
               <div className="sm:hidden px-4 py-1.5 border-t border-gray-700 flex items-center justify-center bg-[#121824]/50">
                  <div className="text-xs text-gray-400 flex items-center">
                     <span
                        className={`w-2 h-2 rounded-full ${
                           isProcessing ? 'bg-emerald-400 animate-pulse' : 'bg-gray-500'
                        } mr-2`}
                     ></span>
                     <span>
                        {isProcessing
                           ? `Processing ${processingType || ''}...`
                           : `Stage: ${currentStage}`}
                     </span>
                  </div>
               </div>
            </header>
            <main className="flex-1 flex flex-col max-h-[calc(100vh-4rem)] overflow-hidden">
               {showFinalPresentation ? (
                  <div className="flex-1 overflow-y-auto p-4 md:p-6">
                     <FinalPresentation
                        podcastTitle={podcastInfo.title}
                        bannerUrl={bannerUrlFull}
                        audioUrl={audioUrlFull}
                        recordingUrl={
                           webSearchRecording && sessionId
                              ? `${
                                   api.API_BASE_URL
                                }/stream-recording/${sessionId}/${webSearchRecording
                                   .split('/')
                                   .pop()}`
                              : ''
                        }
                        sessionId={sessionId}
                        scriptContent={podcastInfo.scriptText}
                        onNewPodcast={startNewSession}
                        isScriptModalOpen={isFinalScriptModalOpen}
                        onToggleScriptModal={() => setIsFinalScriptModalOpen(prev => !prev)}
                        podcastId={sessionState.podcast_id || null}
                     />
                  </div>
               ) : (
                  <>
                     <div
                        ref={chatContainerRef}
                        className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4"
                     >
                        {isProcessing && (
                           <div className="mb-4 px-4 py-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm rounded-md shadow-lg">
                              <div className="flex items-center">
                                 <div className="animate-spin mr-2 h-4 w-4">
                                    <svg
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
                                 <span>
                                    {processingType
                                       ? `Processing ${processingType}...`
                                       : 'Processing request...'}
                                    {currentTaskId && (
                                       <span className="ml-1 text-xs opacity-60">
                                          (Task: {currentTaskId.substring(0, 8)})
                                       </span>
                                    )}
                                 </span>
                              </div>
                           </div>
                        )}
                        <div className="space-y-2">
                           {messages.map((msg, index) => (
                              <ChatMessage key={index} message={msg.content} role={msg.role} />
                           ))}
                           {(isProcessing || loading) && <LoadingIndicator />}
                           {sessionState.show_sources_for_selection &&
                              sessionState.search_results && (
                                 <SourceSelection
                                    sources={sessionState.search_results}
                                    selectedIndices={selectedSourceIndices}
                                    onToggleSelection={handleToggleSourceSelection}
                                    onToggleSelectAll={handleToggleSelectAllSources}
                                    onConfirm={handleSourceSelectionConfirm}
                                    isProcessing={isProcessing}
                                    languages={availableLanguages}
                                    selectedLanguage={selectedLanguageCode}
                                    onSelectLanguage={handleLanguageSelection}
                                 />
                              )}
                           {sessionState.show_script_for_confirmation &&
                              sessionState.generated_script && (
                                 <ScriptConfirmation
                                    generated_script={sessionState.generated_script}
                                    scriptText={podcastInfo.scriptText}
                                    onApprove={() => handleScriptConfirm(true)}
                                    onRequestChanges={() => handleScriptConfirm(false)}
                                    isProcessing={isProcessing}
                                    isModalOpen={isScriptModalOpen}
                                    onToggleModal={() => setIsScriptModalOpen(prev => !prev)}
                                 />
                              )}
                           {sessionState.show_banner_for_confirmation &&
                              sessionState.banner_url && (
                                 <BannerConfirmation
                                    bannerImages={sessionState.banner_images}
                                    bannerUrl={bannerUrlFull}
                                    topic={podcastInfo.title}
                                    onApprove={() => handleBannerConfirm(true)}
                                    onRequestChanges={() => handleBannerConfirm(false)}
                                    isProcessing={isProcessing}
                                 />
                              )}
                           {sessionState.show_audio_for_confirmation && sessionState.audio_url && (
                              <AudioConfirmation
                                 audioUrl={audioUrlFull}
                                 topic={podcastInfo.title}
                                 onApprove={() => handleAudioConfirm(true)}
                                 onRequestChanges={() => handleAudioConfirm(false)}
                                 isProcessing={isProcessing}
                              />
                           )}
                           {error && (
                              <div className="p-3 bg-red-900/30 border border-red-800/50 rounded-md text-red-400 text-sm">
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
                           <div ref={messagesEndRef} />
                        </div>
                     </div>
                     <div className="sticky bottom-0 border-t border-gray-700 bg-[#0A0E14] shadow-lg">
                        <div className="px-4 py-4">
                           <div className="max-w-4xl mx-auto">
                              <div className="relative flex items-center">
                                 <input
                                    ref={inputRef}
                                    type="text"
                                    value={inputMessage}
                                    onChange={e => !isProcessing && setInputMessage(e.target.value)}
                                    onKeyPress={e => {
                                       if (
                                          e.key === 'Enter' &&
                                          !isProcessing &&
                                          inputMessage.trim()
                                       ) {
                                          handleSendMessage();
                                          e.preventDefault();
                                       }
                                    }}
                                    placeholder={
                                       isProcessing || loading
                                          ? `Processing ${processingType || 'request'}...`
                                          : 'Type your message...'
                                    }
                                    disabled={isProcessing || loading}
                                    readOnly={isProcessing || loading}
                                    className={`w-full bg-[#121824] text-white border ${
                                       isProcessing || loading
                                          ? 'border-gray-600'
                                          : 'border-gray-700'
                                    } rounded-md py-3 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-600 placeholder-gray-500 ${
                                       isProcessing || loading
                                          ? 'opacity-60 cursor-not-allowed bg-gray-800/50'
                                          : ''
                                    } shadow-sm`}
                                 />
                                 <button
                                    onClick={handleSendMessage}
                                    disabled={!inputMessage.trim() || isProcessing || loading}
                                    aria-disabled={!inputMessage.trim() || isProcessing || loading}
                                    className={`absolute right-2 h-9 w-9 flex items-center justify-center bg-gradient-to-r ${
                                       !inputMessage.trim() || isProcessing || loading
                                          ? 'from-gray-700 to-gray-800 opacity-50 cursor-not-allowed'
                                          : 'from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 hover:shadow-md'
                                    } text-white rounded-md transition-all`}
                                    aria-label="Send message"
                                 >
                                    {isProcessing || loading ? (
                                       <svg
                                          className="animate-spin h-5 w-5 text-white"
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
                                          />
                                          <path
                                             className="opacity-75"
                                             fill="currentColor"
                                             d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                          />
                                       </svg>
                                    ) : (
                                       <svg
                                          className="h-5 w-5"
                                          viewBox="0 0 20 20"
                                          fill="currentColor"
                                       >
                                          <path
                                             fillRule="evenodd"
                                             d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                                             clipRule="evenodd"
                                          />
                                       </svg>
                                    )}
                                 </button>
                              </div>
                              <div className="mt-1.5 px-1 flex justify-between items-center">
                                 <span className="text-xs text-gray-500">
                                    {isProcessing
                                       ? 'Processing... Please wait'
                                       : 'Ask about your podcast or give instructions'}
                                 </span>
                                 <button
                                    onClick={startNewSession}
                                    disabled={isProcessing}
                                    className={`text-xs ${
                                       isProcessing
                                          ? 'text-gray-500 cursor-not-allowed'
                                          : 'text-emerald-400 hover:text-emerald-300 hover:bg-gray-800'
                                    } transition-colors px-2 py-1 rounded`}
                                 >
                                    New Podcast
                                 </button>
                              </div>
                           </div>
                        </div>
                     </div>
                  </>
               )}
            </main>
         </div>
         {isPreviewVisible && (
            <div className="fixed right-0 top-0 bottom-0 w-full sm:w-80 md:w-72 bg-[#0A0E14] border-l border-gray-700 overflow-hidden z-40 shadow-xl transform transition-transform duration-300 ease-in-out">
               <div className="flex items-center justify-between p-4 border-b border-gray-700">
                  <div className="flex items-center">
                     <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse mr-2"></div>
                     <h3 className="text-sm font-semibold text-white">Active Assets</h3>
                  </div>
                  <button
                     onClick={handleClosePreview}
                     className="text-gray-400 hover:text-white transition-colors duration-200 p-1 rounded-full hover:bg-gray-700"
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
               <ActivePodcastPreview
                  sources={sessionState.search_results}
                  bannerImages={sessionState.banner_images || []}
                  generatedScript={sessionState.generated_script || null}
                  podcastTitle={podcastInfo.title}
                  bannerUrl={bannerUrlFull}
                  audioUrl={audioUrlFull}
                  sessionId={sessionId || ''}
                  webSearchRecording={webSearchRecording || null}
                  scriptContent={podcastInfo.scriptText}
                  onClose={handleClosePreview}
                  hasAutoOpenedRecording={hasAutoOpenedRecording}
                  stage={sessionState?.stage}
               />
            </div>
         )}
         {showCompletionModal && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
               <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md max-w-md w-full p-6 text-center shadow-2xl animate-fade-in-up">
                  <div className="relative w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-5">
                     <svg
                        className="h-8 w-8 text-emerald-500"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                     >
                        <path
                           fillRule="evenodd"
                           d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                           clipRule="evenodd"
                        />
                     </svg>
                     <div className="absolute inset-0 rounded-full bg-emerald-500 opacity-10 animate-ping"></div>
                  </div>
                  <h2 className="text-xl font-bold text-white mb-2">Podcast Creation Complete!</h2>
                  <p className="text-gray-400 mb-6">
                     Your podcast is ready! You can now view and download all components.
                  </p>
                  <button
                     onClick={() => setShowCompletionModal(false)}
                     className="w-full py-3 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white font-medium rounded-md transition-all flex items-center justify-center shadow-lg hover:shadow-emerald-900/30 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                  >
                     <svg className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                        <path
                           fillRule="evenodd"
                           d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                           clipRule="evenodd"
                        />
                     </svg>
                     View My Podcast
                  </button>
               </div>
            </div>
         )}
         <style jsx>{`
            @keyframes fadeInUp {
               from {
                  opacity: 0;
                  transform: translateY(20px);
               }
               to {
                  opacity: 1;
                  transform: translateY(0);
               }
            }

            @keyframes slideUp {
               from {
                  transform: translateY(30px);
                  opacity: 0;
               }
               to {
                  transform: translateY(0);
                  opacity: 1;
               }
            }

            .animate-fade-in-up {
               animation: fadeInUp 0.3s ease-out forwards;
            }
         `}</style>
      </div>
   );
};

export default PodcastSession;
