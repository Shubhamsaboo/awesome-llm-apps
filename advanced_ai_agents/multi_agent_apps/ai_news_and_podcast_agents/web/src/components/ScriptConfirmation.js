import React, { useState, useEffect } from 'react';
import { Check, Loader2, FileText, Sparkles, Eye, X, Users, Globe } from 'lucide-react';

const SourceIcon = ({ url }) => {
   const [iconUrl, setIconUrl] = useState(null);
   const [isIconReady, setIsIconReady] = useState(false);
   const defaultIconSvg = (
      <svg
         className="w-2.5 h-2.5 text-emerald-400 transition-transform duration-200 group-hover:scale-110"
         fill="none"
         viewBox="0 0 24 24"
         stroke="currentColor"
      >
         <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
         />
      </svg>
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

const ScriptConfirmation = ({
   scriptText,
   onApprove,
   isProcessing,
   isModalOpen,
   onToggleModal,
   generated_script,
}) => {
   const [selectedSection, setSelectedSection] = useState(null);
   const scriptData = generated_script || { sections: [] };
   const hasStructuredScript = generated_script && generated_script.sections;
   const speakerColors = {
      ALEX: 'from-slate-600 to-slate-700',
      MORGAN: 'from-gray-600 to-gray-700',
      default: 'from-zinc-600 to-zinc-700',
   };
   const getSpeakerColor = speaker => {
      return speakerColors[speaker] || speakerColors.default;
   };
   const formatScriptMarkdown = text =>
      text
         .replace(/^# (.*$)/gm, '<h1 class="text-base font-bold mt-3 mb-2 text-white">$1</h1>')
         .replace(
            /^## (.*$)/gm,
            '<h2 class="text-sm font-semibold mt-2 mb-1 text-gray-100">$1</h2>'
         )
         .replace(/^### (.*$)/gm, '<h3 class="text-xs font-medium mt-2 mb-1 text-gray-200">$3</h3>')
         .replace(/\[([^\]]+)\]:/g, '<strong class="text-emerald-400">$1:</strong>')
         .replace(/\n/g, '<br>');
   const getScriptPreview = () => {
      if (hasStructuredScript && scriptData.sections.length > 0) {
         const firstSection = scriptData.sections[0];
         if (firstSection.dialog && firstSection.dialog.length > 0) {
            return firstSection.dialog.slice(0, 2).map((line, index) => (
               <div key={index} className="mb-1.5">
                  <span
                     className={`inline-block px-2 py-0.5 text-[10px] font-medium bg-gradient-to-r ${getSpeakerColor(
                        line.speaker
                     )} text-white rounded-full mr-2 min-w-12 text-center`}
                  >
                     {line.speaker}
                  </span>
                  <span className="text-gray-300 text-xs">{line.text}</span>
               </div>
            ));
         }
      }
      return (
         <div
            dangerouslySetInnerHTML={{
               __html: formatScriptMarkdown(scriptText.split('\n').slice(0, 3).join('\n') + '...'),
            }}
         />
      );
   };
   const formatSectionType = type => {
      return type.charAt(0).toUpperCase() + type.slice(1);
   };
   const getTotalLines = () => {
      if (!hasStructuredScript) return null;
      return scriptData.sections.reduce(
         (total, section) => total + (section.dialog ? section.dialog.length : 0),
         0
      );
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

   return (
      <>
         <div className="w-full max-w-2xl mx-auto">
            <div className="bg-gradient-to-br from-gray-900 via-gray-850 to-gray-800 rounded-lg overflow-hidden shadow-xl border border-gray-700/50 transition-all duration-300 hover:shadow-2xl">
               <div className="relative px-3 py-2 bg-gradient-to-r from-gray-800/80 to-gray-900/80 backdrop-blur border-b border-gray-700/30">
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5" />
                  <div className="relative">
                     <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                           <div className="p-1 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-md">
                              <FileText className="w-3 h-3 text-emerald-400" />
                           </div>
                           <div>
                              <h3 className="text-sm font-semibold text-white">Script Preview</h3>
                           </div>
                        </div>
                        <button
                           onClick={onToggleModal}
                           disabled={isProcessing}
                           className="group flex items-center gap-1 px-2 py-1 bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-600 hover:to-gray-500 text-white text-[10px] font-medium rounded-md transition-all duration-200 hover:scale-105 border border-gray-600/30 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                           <Eye className="w-2.5 h-2.5 group-hover:scale-110 transition-transform" />
                           View Full
                        </button>
                     </div>
                     <div className="flex items-center gap-3 mt-1 ml-8">
                        {hasStructuredScript && scriptData.title && (
                           <p className="text-xs text-gray-400">"{scriptData.title}"</p>
                        )}
                        {hasStructuredScript && (
                           <div className="flex items-center gap-2 text-[10px] text-gray-400">
                              <span className="flex items-center gap-0.5">
                                 <Users className="w-2 h-2" />
                                 {getSpeakers().length}
                              </span>
                              <span className="flex items-center gap-0.5">
                                 <FileText className="w-2 h-2" />
                                 {getTotalLines()}
                              </span>
                           </div>
                        )}
                     </div>
                  </div>
               </div>
               <div className="px-3 py-3">
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-lg p-3 border border-gray-600/30 backdrop-blur-sm">
                     {hasStructuredScript ? (
                        <div className="space-y-2">
                           {getScriptPreview()}
                           <div className="pt-2 border-t border-gray-600/30">
                              <div
                                 className="text-emerald-400 text-xs font-medium cursor-pointer hover:underline flex items-center gap-1"
                                 onClick={() => !isProcessing && onToggleModal()}
                              >
                                 <Sparkles className="w-3 h-3" />
                                 Read complete script with {scriptData.sections.length} sections...
                              </div>
                           </div>
                        </div>
                     ) : (
                        <div>
                           <div
                              className="text-xs text-gray-300"
                              dangerouslySetInnerHTML={{
                                 __html: formatScriptMarkdown(
                                    scriptText.split('\n').slice(0, 3).join('\n') + '...'
                                 ),
                              }}
                           />
                           <div className="pt-2 border-t border-gray-600/30">
                              <div
                                 className="text-emerald-400 text-xs cursor-pointer hover:underline flex items-center gap-1"
                                 onClick={() => !isProcessing && onToggleModal()}
                              >
                                 <Sparkles className="w-3 h-3" />
                                 Click to expand full script...
                              </div>
                           </div>
                        </div>
                     )}
                  </div>
                  {hasStructuredScript && scriptData.sections.length > 0 && (
                     <div className="mt-2">
                        <div className="flex flex-wrap gap-1">
                           {scriptData.sections.map((section, index) => (
                              <div
                                 key={index}
                                 className="px-2 py-1 bg-gray-700/50 text-gray-300 text-[10px] rounded-md border border-gray-600/30"
                              >
                                 {formatSectionType(section.type)}
                                 {section.title && ` - ${section.title.substring(0, 20)}...`}
                              </div>
                           ))}
                        </div>
                     </div>
                  )}
               </div>
               <div className="px-3 py-2 bg-gradient-to-r from-gray-900/50 to-gray-800/50 backdrop-blur border-t border-gray-700/30">
                  <div className="flex justify-center">
                     <button
                        onClick={onApprove}
                        disabled={isProcessing}
                        className={`group flex items-center justify-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-emerald-500/25 border border-emerald-500/30 ${
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
                              <span>Approve Script</span>
                           </>
                        )}
                     </button>
                  </div>
                  <div className="mt-1.5 text-center">
                     <p className="text-xs text-gray-400 flex items-center justify-center gap-1">
                        <FileText className="w-3 h-3" />
                        {hasStructuredScript
                           ? 'Review complete script before approval'
                           : 'Review script before approval'}
                     </p>
                  </div>
               </div>
            </div>
         </div>
         {isModalOpen && (
            <div className="fixed inset-0 bg-black/95 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4">
               <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg border border-gray-700/50 w-full max-w-full sm:max-w-5xl h-full sm:h-[80vh] flex flex-col shadow-xl">
                  <div className="px-3 sm:px-4 py-3 border-b border-gray-700/30 flex items-center justify-between flex-shrink-0">
                     <div className="min-w-0 flex-1">
                        <h3 className="text-base sm:text-lg font-semibold text-white truncate">
                           Complete Script
                        </h3>
                        {hasStructuredScript && scriptData.title && (
                           <p className="text-xs sm:text-sm text-gray-400 mt-0.5 truncate">
                              {scriptData.title}
                           </p>
                        )}
                     </div>
                     <button
                        onClick={onToggleModal}
                        disabled={isProcessing}
                        className="ml-2 p-1.5 text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-700/50 rounded-md transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                     >
                        <X className="w-4 h-4" />
                     </button>
                  </div>
                  <div className="flex-1 overflow-hidden">
                     {hasStructuredScript ? (
                        <div className="flex flex-col sm:flex-row h-full">
                           <div className="sm:w-56 border-b sm:border-b-0 sm:border-r border-gray-700/30 bg-gray-800/30 flex-shrink-0">
                              <div className="sm:hidden p-2">
                                 <h4 className="text-xs font-medium text-gray-300 mb-2">
                                    Sections
                                 </h4>
                                 <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                                    {scriptData.sections.map((section, index) => (
                                       <button
                                          key={index}
                                          onClick={() => setSelectedSection(index)}
                                          className={`flex-shrink-0 px-3 py-2 rounded-md text-xs transition-all duration-200 ${
                                             selectedSection === index
                                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                                : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700/30 bg-gray-700/20'
                                          }`}
                                       >
                                          <div className="font-medium whitespace-nowrap">
                                             {formatSectionType(section.type)}
                                          </div>
                                          {section.dialog && (
                                             <div className="text-[10px] text-gray-500 mt-0.5 whitespace-nowrap">
                                                {section.dialog.length} lines
                                             </div>
                                          )}
                                       </button>
                                    ))}
                                 </div>
                              </div>
                              <div className="hidden sm:block h-full overflow-y-auto">
                                 <div className="p-3">
                                    <h4 className="text-sm font-medium text-gray-300 mb-2">
                                       Sections
                                    </h4>
                                    <div className="space-y-1.5">
                                       {scriptData.sections.map((section, index) => (
                                          <button
                                             key={index}
                                             onClick={() => setSelectedSection(index)}
                                             className={`w-full text-left px-2 py-1.5 rounded-md text-xs transition-all duration-200 ${
                                                selectedSection === index
                                                   ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                                   : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700/30'
                                             }`}
                                          >
                                             <div className="font-medium">
                                                {formatSectionType(section.type)}
                                             </div>
                                             {section.title && (
                                                <div className="text-[10px] text-gray-500 mt-0.5 truncate">
                                                   {section.title}
                                                </div>
                                             )}
                                             {section.dialog && (
                                                <div className="text-[10px] text-gray-500 mt-0.5">
                                                   {section.dialog.length} lines
                                                </div>
                                             )}
                                          </button>
                                       ))}
                                    </div>
                                 </div>
                              </div>
                           </div>
                           <div className="flex-1 overflow-y-auto">
                              <div className="p-2 sm:p-4">
                                 {scriptData.sections.map((section, sectionIndex) => (
                                    <div
                                       key={sectionIndex}
                                       className={`mb-4 sm:mb-6 ${
                                          selectedSection !== null &&
                                          selectedSection !== sectionIndex
                                             ? 'hidden'
                                             : ''
                                       }`}
                                    >
                                       <div className="mb-2 sm:mb-3">
                                          <h2 className="text-sm sm:text-base font-semibold text-white mb-1">
                                             {formatSectionType(section.type)}
                                             {section.title && ` - ${section.title}`}
                                          </h2>
                                          <div className="h-px bg-gradient-to-r from-emerald-500/50 to-transparent" />
                                       </div>
                                       {section.dialog ? (
                                          <div className="space-y-2 sm:space-y-3">
                                             {section.dialog.map((line, lineIndex) => (
                                                <div
                                                   key={lineIndex}
                                                   className="flex flex-col sm:flex-row gap-2 sm:gap-3 sm:items-start"
                                                >
                                                   <div
                                                      className={`flex-shrink-0 px-2 py-1 text-[10px] font-medium bg-gradient-to-r ${getSpeakerColor(
                                                         line.speaker
                                                      )} text-white rounded-full text-center self-start sm:min-w-14`}
                                                   >
                                                      {line.speaker}
                                                   </div>
                                                   <div className="flex-1 text-gray-300 text-xs sm:text-sm leading-relaxed">
                                                      {line.text}
                                                   </div>
                                                </div>
                                             ))}
                                          </div>
                                       ) : (
                                          <div className="text-gray-400 italic text-xs sm:text-sm">
                                             No dialog for this section
                                          </div>
                                       )}
                                    </div>
                                 ))}
                                 {scriptData.sources && scriptData.sources.length > 0 && (
                                    <div className="mt-4 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-700/30">
                                       <h3 className="text-sm sm:text-base font-semibold text-white mb-2 sm:mb-3 flex items-center gap-2">
                                          <Globe className="w-3 h-3 sm:w-4 sm:h-4" />
                                          Sources
                                       </h3>
                                       <div className="space-y-2">
                                          {scriptData.sources.map((source, index) => (
                                             <a
                                                key={index}
                                                href={source}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="group flex items-center gap-2 p-2 bg-gray-800/30 rounded-md border border-gray-700/30 hover:border-gray-600/50 hover:bg-gray-700/30 transition-all duration-200"
                                             >
                                                <div className="flex-shrink-0">
                                                   <SourceIcon url={source} />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                   <div className="text-emerald-400 group-hover:text-emerald-300 text-xs font-medium truncate">
                                                      {new URL(source).hostname}
                                                   </div>
                                                   <div className="text-gray-500 text-[10px] truncate mt-0.5 break-all">
                                                      {source}
                                                   </div>
                                                </div>
                                             </a>
                                          ))}
                                       </div>
                                    </div>
                                 )}
                              </div>
                           </div>
                        </div>
                     ) : (
                        <div className="p-2 sm:p-4 overflow-y-auto h-full">
                           <div
                              className="prose prose-invert prose-sm max-w-none text-xs sm:text-sm"
                              dangerouslySetInnerHTML={{ __html: formatScriptMarkdown(scriptText) }}
                           />
                        </div>
                     )}
                  </div>
                  <div className="px-3 sm:px-4 py-3 border-t border-gray-700/30 flex justify-end flex-shrink-0">
                     <button
                        onClick={() => {
                           onToggleModal();
                           onApprove();
                        }}
                        disabled={isProcessing}
                        className={`flex items-center gap-1.5 px-3 sm:px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs sm:text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-emerald-500/25 border border-emerald-500/30 ${
                           isProcessing ? 'opacity-70 cursor-not-allowed' : ''
                        }`}
                     >
                        {isProcessing ? (
                           <>
                              <Loader2 className="w-3 h-3 sm:w-4 sm:h-4 animate-spin" />
                              Processing...
                           </>
                        ) : (
                           <>
                              <Check className="w-3 h-3 sm:w-4 sm:h-4" />
                              Approve Script
                           </>
                        )}
                     </button>
                  </div>
               </div>
            </div>
         )}
      </>
   );
};

export default ScriptConfirmation;
