import React, { useState, useEffect, useRef } from 'react';

const SourceSelector = ({ sources, selectedSource, onSourceChange }) => {
   const [isOpen, setIsOpen] = useState(false);
   const [searchTerm, setSearchTerm] = useState('');
   const dropdownRef = useRef(null);
   const filteredSources = searchTerm
      ? sources.filter(source => source.toLowerCase().includes(searchTerm.toLowerCase()))
      : sources;

   useEffect(() => {
      const handleClickOutside = event => {
         if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
            setIsOpen(false);
         }
      };
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
         document.removeEventListener('mousedown', handleClickOutside);
      };
   }, []);

   const handleSelectSource = source => {
      onSourceChange(source);
      setIsOpen(false);
      setSearchTerm('');
   };

   const getSourceColor = source => {
      const colors = [
         'bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border-emerald-700',
         'bg-gradient-to-r from-gray-800 to-gray-900 text-gray-300 border-gray-700',
         'bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border-gray-700',
         'bg-gradient-to-r from-gray-800 to-gray-900 text-gray-300 border-gray-700',
         'bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border-gray-700',
         'bg-gradient-to-r from-gray-800 to-gray-900 text-gray-300 border-gray-700',
      ];
      const hash = source.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      return colors[hash % colors.length];
   };

   return (
      <div className="relative" ref={dropdownRef}>
         <label htmlFor="source" className="block text-sm font-medium text-gray-300 mb-1">
            Source
         </label>
         <div
            className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm cursor-pointer flex items-center justify-between hover:border-gray-600 transition-colors duration-200"
            onClick={() => setIsOpen(!isOpen)}
         >
            <div className="flex items-center">
               {selectedSource ? (
                  <span
                     className={`px-2 py-0.5 rounded-sm text-xs font-medium ${getSourceColor(
                        selectedSource
                     )} border mr-2`}
                  >
                     {selectedSource}
                  </span>
               ) : (
                  <span className="text-gray-400">All Sources</span>
               )}
            </div>
            <svg
               xmlns="http://www.w3.org/2000/svg"
               className={`h-5 w-5 text-gray-400 transition-transform ${
                  isOpen ? 'transform rotate-180' : ''
               }`}
               viewBox="0 0 20 20"
               fill="currentColor"
            >
               <path
                  fillRule="evenodd"
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                  clipRule="evenodd"
               />
            </svg>
         </div>
         {isOpen && (
            <div className="absolute z-10 mt-1 w-full bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg max-h-60 rounded-sm py-1 text-base border border-gray-700 overflow-auto focus:outline-none sm:text-sm">
               <div className="sticky top-0 px-3 py-2 bg-gradient-to-br from-gray-800 to-gray-900 border-b border-gray-700">
                  <div className="relative">
                     <input
                        type="text"
                        className="w-full pl-8 pr-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 text-sm text-gray-300"
                        placeholder="Search sources..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        onClick={e => e.stopPropagation()}
                     />
                     <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-4 w-4 text-gray-500"
                           fill="none"
                           viewBox="0 0 24 24"
                           stroke="currentColor"
                        >
                           <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                           />
                        </svg>
                     </div>
                  </div>
               </div>
               <div
                  className={`px-3 py-2 cursor-pointer hover:bg-gray-700 flex items-center ${
                     !selectedSource ? 'bg-gray-700' : ''
                  } transition-colors duration-200`}
                  onClick={() => handleSelectSource('')}
               >
                  <span className="px-2 py-0.5 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700 mr-2">
                     All
                  </span>
                  <span className="text-gray-300">All Sources</span>
               </div>
               <div className="border-t border-gray-700 my-1"></div>
               {filteredSources.length > 0 ? (
                  filteredSources.map((source, index) => (
                     <div
                        key={index}
                        className={`px-3 py-2 cursor-pointer hover:bg-gray-700 flex items-center ${
                           selectedSource === source ? 'bg-gray-700' : ''
                        } transition-colors duration-200`}
                        onClick={() => handleSelectSource(source)}
                     >
                        <span
                           className={`px-2 py-0.5 rounded-sm text-xs font-medium ${getSourceColor(
                              source
                           )} border mr-2`}
                        >
                           {source.substring(0, 2).toUpperCase()}
                        </span>
                        <span className="text-gray-300">{source}</span>
                     </div>
                  ))
               ) : (
                  <div className="px-3 py-2 text-sm text-gray-400 text-center">
                     No sources found
                  </div>
               )}
            </div>
         )}
      </div>
   );
};

export default SourceSelector;
