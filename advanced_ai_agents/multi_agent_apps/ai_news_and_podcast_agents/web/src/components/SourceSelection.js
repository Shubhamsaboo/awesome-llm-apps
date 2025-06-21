import React, { useState, useEffect } from 'react';
import {
   Settings,
   Check,
   Loader2,
   CheckSquare,
   Square,
   Calendar,
   ExternalLink,
   Sparkles,
   FileText,
   HammerIcon,
} from 'lucide-react';
import LanguageSelector from './LanguageSelector';

const SourceIcon = ({ url }) => {
   const [iconUrl, setIconUrl] = useState(null);
   const [isIconReady, setIsIconReady] = useState(false);
   const defaultIconSvg = (
      <ExternalLink className="w-2.5 h-2.5 text-emerald-400 transition-transform duration-200 group-hover:scale-110" />
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
         className="w-2.5 h-2.5 object-contain transition-transform duration-200 group-hover:scale-110"
      />
   );
};

const SourceSelection = ({
   sources,
   selectedIndices,
   onToggleSelection,
   onToggleSelectAll,
   onConfirm,
   isProcessing,
   languages,
   selectedLanguage,
   onSelectLanguage,
}) => {
   const formatDate = dateString => {
      if (!dateString) return null;

      try {
         const date = new Date(dateString);
         return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
         });
      } catch (error) {
         return null;
      }
   };

   return (
      <div className="w-full max-w-2xl mx-auto mt-2">
         <div className="bg-gradient-to-br from-gray-900 via-gray-850 to-gray-800 rounded-md overflow-hidden shadow-lg border border-gray-700/50 transition-all duration-300 hover:shadow-xl">
            <div className="relative px-2 py-1.5 bg-gradient-to-r from-gray-800/80 to-gray-900/80 backdrop-blur border-b border-gray-700/30">
               <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5" />
               <div className="relative">
                  <div className="flex items-center justify-between">
                     <div className="flex items-center gap-1.5">
                        <div className="p-0.5 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-sm">
                           <FileText className="w-2.5 h-2.5 text-emerald-400" />
                        </div>
                        <div>
                           <h3 className="text-sm font-semibold text-white">Select Sources</h3>
                           <p className="text-xs text-gray-400">Choose sources</p>
                        </div>
                     </div>
                     <div className="flex items-center">
                        <div className="text-xs text-emerald-400 bg-emerald-500/20 px-1.5 py-0.5 rounded-sm border border-emerald-500/30">
                           <span className="font-medium">{selectedIndices.length}</span>
                           <span className="text-gray-300 mx-0.5">of</span>
                           <span className="font-medium">{sources.length}</span>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
            <div className="p-2">
               <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
                  {sources.map((source, index) => (
                     <div
                        key={index}
                        className={`group relative p-2 rounded-md border transition-all duration-300 cursor-pointer ${
                           selectedIndices.includes(index)
                              ? 'bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-emerald-500/30 shadow-md'
                              : 'bg-gradient-to-r from-gray-800/50 to-gray-700/50 border-gray-700/30 hover:border-gray-600/50 hover:bg-gradient-to-r hover:from-gray-700/50 hover:to-gray-600/50'
                        }`}
                        onClick={() => !isProcessing && onToggleSelection(index)}
                     >
                        <div className="flex items-start gap-1.5">
                           <div className="flex-shrink-0 pt-0.5">
                              {selectedIndices.includes(index) ? (
                                 <CheckSquare className="w-2.5 h-2.5 text-emerald-400" />
                              ) : (
                                 <Square className="w-2.5 h-2.5 text-gray-500 group-hover:text-gray-400" />
                              )}
                           </div>
                           <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between gap-2">
                                 <h4
                                    className={`text-xs font-medium leading-tight ${
                                       selectedIndices.includes(index)
                                          ? 'text-white'
                                          : 'text-gray-300 group-hover:text-white'
                                    } transition-colors duration-200`}
                                 >
                                    <span className="text-emerald-400 font-semibold">
                                       {index + 1}.
                                    </span>{' '}
                                    {source.title}
                                 </h4>
                              </div>
                              <div className="flex items-center gap-0.5 mt-0.5 flex-wrap">
                                 <div className="relative group/source">
                                    <div className="bg-gray-800/50 border border-gray-700/50 px-1 py-0.5 rounded-sm flex items-center gap-0.5">
                                       <Sparkles className="w-2.5 h-2.5 text-blue-400" />
                                       <span
                                          style={{ fontSize: '8px' }}
                                          className="text-xs text-gray-400 font-medium"
                                       >
                                          Source
                                       </span>
                                    </div>
                                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900 text-white text-xs rounded shadow-lg border border-gray-700 opacity-0 group-hover/source:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                                       {source.source_name || source.source_id || 'Unknown'}
                                    </div>
                                 </div>
                                 {source.tool_used && (
                                    <div className="relative group/tool">
                                       <div className="bg-gray-800/50 border border-gray-700/50 px-1 py-0.5 rounded-sm flex items-center gap-0.5">
                                          <HammerIcon className="w-2.5 h-2.5 text-blue-400" />
                                          <span
                                             style={{ fontSize: '8px' }}
                                             className="text-xs text-gray-400 font-medium"
                                          >
                                             Tool
                                          </span>
                                       </div>
                                       <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900 text-white text-xs rounded shadow-lg border border-gray-700 opacity-0 group-hover/tool:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                                          {source.tool_used}
                                       </div>
                                    </div>
                                 )}
                                 {formatDate(source.published_date) && (
                                    <div className="bg-gray-800/50 border border-gray-700/50 px-1 py-0.5 rounded-sm flex items-center gap-0.5">
                                       <Calendar className="w-2.5 h-2.5 text-blue-400" />
                                       <span
                                          style={{ fontSize: '8px' }}
                                          className="text-xs text-gray-400"
                                       >
                                          {formatDate(source.published_date)}
                                       </span>
                                    </div>
                                 )}
                                 {source.url && (
                                    <a
                                       href={source.url}
                                       target="_blank"
                                       rel="noopener noreferrer"
                                       onClick={e => e.stopPropagation()}
                                       className="px-1 py-0.5 rounded-sm flex items-center gap-0.5"
                                       title={`Link ${new URL(source.url).hostname}`}
                                    >
                                       <SourceIcon url={source.url} />
                                       <span
                                          style={{ fontSize: '8px' }}
                                          className="text-xs text-emerald-300 font-medium"
                                       >
                                          Link
                                       </span>
                                    </a>
                                 )}
                              </div>
                              {source.description && (
                                 <p className="text-xs text-gray-500 mt-0.5 leading-tight line-clamp-1">
                                    {source.description}
                                 </p>
                              )}
                           </div>
                        </div>
                     </div>
                  ))}
               </div>
               <div className="mt-2">
                  <LanguageSelector
                     languages={languages}
                     selectedLanguage={selectedLanguage}
                     onSelectLanguage={onSelectLanguage}
                     isDisabled={isProcessing}
                  />
               </div>
            </div>
            <div className="px-2 py-1.5 bg-gradient-to-r from-gray-900/50 to-gray-800/50 backdrop-blur border-t border-gray-700/30">
               <div className="flex items-center justify-between">
                  <button
                     type="button"
                     onClick={onToggleSelectAll}
                     disabled={isProcessing}
                     className={`flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium rounded-sm transition-all duration-200 ${
                        isProcessing
                           ? 'text-gray-500 cursor-not-allowed bg-gray-800/50'
                           : 'text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 border border-emerald-500/30 hover:border-emerald-400/50'
                     }`}
                  >
                     {selectedIndices.length === sources.length ? (
                        <>
                           <Square className="w-2.5 h-2.5" />
                           Deselect All
                        </>
                     ) : (
                        <>
                           <CheckSquare className="w-2.5 h-2.5" />
                           Select All
                        </>
                     )}
                  </button>
                  <button
                     onClick={onConfirm}
                     disabled={isProcessing || selectedIndices.length === 0}
                     className={`group flex items-center justify-center gap-1 px-3 py-1 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-medium rounded-md transition-all duration-200 hover:scale-105 hover:shadow-md border border-emerald-500/30 ${
                        isProcessing || selectedIndices.length === 0
                           ? 'opacity-70 cursor-not-allowed'
                           : ''
                     }`}
                  >
                     {isProcessing ? (
                        <>
                           <Loader2 className="w-3 h-3 animate-spin" />
                           <span>Processing...</span>
                        </>
                     ) : (
                        <>
                           <Check className="w-3 h-3 group-hover:scale-110 transition-transform" />
                           <span>Confirm</span>
                        </>
                     )}
                  </button>
               </div>
               <div className="mt-1 text-center">
                  <p className="text-xs text-gray-400 flex items-center justify-center gap-1">
                     <Sparkles className="w-2.5 h-2.5" />
                     {selectedIndices.length > 0
                        ? `${selectedIndices.length} source${
                             selectedIndices.length > 1 ? 's' : ''
                          } selected`
                        : 'Select sources to continue'}
                  </p>
               </div>
            </div>
         </div>
      </div>
   );
};

export default SourceSelection;
