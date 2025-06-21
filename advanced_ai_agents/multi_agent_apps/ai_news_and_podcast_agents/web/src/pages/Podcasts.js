import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import api from '../services/api';

const ToggleSwitch = ({ isActive, isUpdating, onChange }) => {
   return (
      <button
         onClick={onChange}
         disabled={isUpdating}
         className={`relative inline-flex h-5 w-10 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 ${
            isUpdating ? 'cursor-wait opacity-70' : ''
         } ${
            isActive ? 'bg-emerald-600 focus:ring-emerald-500' : 'bg-gray-700 focus:ring-gray-500'
         }`}
      >
         <span
            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
               isActive ? 'translate-x-6' : 'translate-x-1'
            }`}
         />
         {isUpdating && (
            <span className="absolute inset-0 flex items-center justify-center">
               <svg
                  className="animate-spin h-3 w-3 text-white"
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
            </span>
         )}
         <span className="sr-only">{isActive ? 'Active' : 'Inactive'}</span>
      </button>
   );
};

const Podcasts = () => {
   const [podcasts, setPodcasts] = useState([]);
   const [languages, setLanguages] = useState([]);
   const [ttsEngines, setTtsEngines] = useState([]);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [hoveredItem, setHoveredItem] = useState(null);
   const [page, setPage] = useState(1);
   const [perPage, setPerPage] = useState(10);
   const [totalPages, setTotalPages] = useState(0);
   const [totalItems, setTotalItems] = useState(0);
   const [hasNext, setHasNext] = useState(false);
   const [hasPrev, setHasPrev] = useState(false);
   const [searchQuery, setSearchQuery] = useState('');
   const [selectedLanguage, setSelectedLanguage] = useState('');
   const [selectedTtsEngine, setSelectedTtsEngine] = useState('');
   const [hasAudio, setHasAudio] = useState(null);
   const [dateFrom, setDateFrom] = useState('');
   const [dateTo, setDateTo] = useState('');
   const [isFilterOpen, setIsFilterOpen] = useState(false);

   useEffect(() => {
      const fetchFilterData = async () => {
         try {
            const [languagesRes, ttsEnginesRes] = await Promise.all([
               api.podcasts.getLanguageCodes(),
               api.podcasts.getTtsEngines(),
            ]);
            setLanguages(languagesRes.data || []);
            setTtsEngines(ttsEnginesRes.data || []);
         } catch (err) {
            console.error('Error fetching filter data:', err);
         }
      };
      fetchFilterData();
   }, []);

   useEffect(() => {
      const fetchPodcasts = async () => {
         setLoading(true);
         setError(null);

         try {
            const params = {
               page,
               per_page: perPage,
            };
            if (searchQuery) params.search = searchQuery;
            if (selectedLanguage) params.language_code = selectedLanguage;
            if (selectedTtsEngine) params.tts_engine = selectedTtsEngine;
            if (hasAudio !== null) params.has_audio = hasAudio;
            if (dateFrom) params.date_from = dateFrom;
            if (dateTo) params.date_to = dateTo;
            const response = await api.podcasts.getAll(params);
            const data = response.data;
            setPodcasts(data.items || []);
            setTotalPages(data.total_pages || 0);
            setTotalItems(data.total || 0);
            setHasNext(data.has_next || false);
            setHasPrev(data.has_prev || false);
         } catch (err) {
            setError(`Failed to fetch podcasts: ${err.message}`);
            console.error('Error fetching podcasts:', err);
         } finally {
            setLoading(false);
         }
      };

      fetchPodcasts();
   }, [
      page,
      perPage,
      selectedLanguage,
      selectedTtsEngine,
      searchQuery,
      hasAudio,
      dateFrom,
      dateTo,
   ]);

   const handleFilterSubmit = e => {
      e.preventDefault();
      setPage(1);
      setIsFilterOpen(false);
   };

   const handleResetFilters = () => {
      setSelectedLanguage('');
      setSelectedTtsEngine('');
      setSearchQuery('');
      setHasAudio(null);
      setDateFrom('');
      setDateTo('');
      setPage(1);
      setIsFilterOpen(false);
   };

   const formatDate = dateString => {
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString(undefined, options);
   };

   const formatTtsEngineName = engine => {
      if (!engine) return '';
      return engine;
   };

   const getLanguageName = code => {
      if (!code) return '';
      return code;
   };

   return (
      <div className="max-w-6xl mx-auto">
         <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 relative">
            <div className="relative mb-4 md:mb-0">
               <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-8 h-8">
                  <div className="relative w-8 h-8">
                     <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                        className="text-emerald-500 w-8 h-8 relative z-10"
                     >
                        <path
                           d="M12 1C8.14 1 5 4.14 5 8V11C5 14.86 8.14 18 12 18C15.86 18 19 14.86 19 11V8C19 4.14 15.86 1 12 1Z"
                           stroke="currentColor"
                           strokeWidth="1.5"
                        />
                        <path
                           d="M12 18V23"
                           stroke="currentColor"
                           strokeWidth="1.5"
                           strokeLinecap="round"
                        />
                        <path
                           d="M8 23H16"
                           stroke="currentColor"
                           strokeWidth="1.5"
                           strokeLinecap="round"
                        />
                        <path
                           d="M13.5 6.5C13.5 7.33 12.83 8 12 8C11.17 8 10.5 7.33 10.5 6.5C10.5 5.67 11.17 5 12 5C12.83 5 13.5 5.67 13.5 6.5Z"
                           fill="currentColor"
                        />
                        <path
                           d="M16 11V11.25C16 13.32 14.32 15 12.25 15H11.75C9.68 15 8 13.32 8 11.25V11"
                           stroke="currentColor"
                           strokeWidth="1.5"
                           strokeLinecap="round"
                        />
                     </svg>
                     <div className="absolute inset-0 bg-emerald-500 opacity-30 blur-md rounded-full"></div>
                  </div>
               </div>
               <h1 className="text-2xl font-medium text-gray-100 ml-10">Podcasts</h1>
            </div>
            <div className="flex items-center space-x-2">
               <div className="relative flex-grow">
                  <input
                     type="text"
                     value={searchQuery}
                     onChange={e => setSearchQuery(e.target.value)}
                     placeholder="Search podcasts..."
                     className="w-full pl-10 pr-4 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 text-gray-300"
                  />
                  <div className="absolute left-3 top-2.5 text-gray-500">
                     <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5"
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
               <button
                  onClick={() => setIsFilterOpen(!isFilterOpen)}
                  className="flex items-center justify-center p-2 bg-gradient-to-r from-gray-800 to-gray-900 border border-gray-700 rounded-sm shadow-sm hover:border-gray-600 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-colors duration-200"
                  aria-expanded={isFilterOpen}
                  aria-label="Toggle filters"
               >
                  <svg
                     xmlns="http://www.w3.org/2000/svg"
                     className="h-5 w-5 text-gray-400"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                     />
                  </svg>
               </button>
            </div>
         </div>
         {isFilterOpen && (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm p-4 mb-6 border border-gray-700">
               <form
                  onSubmit={handleFilterSubmit}
                  className="space-y-4 md:space-y-0 md:grid md:grid-cols-4 md:gap-2"
               >
                  <div>
                     <label
                        htmlFor="language"
                        className="block text-sm font-medium text-gray-300 mb-1"
                     >
                        Language
                     </label>
                     <select
                        id="language"
                        value={selectedLanguage}
                        onChange={e => setSelectedLanguage(e.target.value)}
                        className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                     >
                        <option value="">All Languages</option>
                        {languages.map(lang => (
                           <option key={lang} value={lang}>
                              {getLanguageName(lang)}
                           </option>
                        ))}
                     </select>
                  </div>
                  <div>
                     <label
                        htmlFor="ttsEngine"
                        className="block text-sm font-medium text-gray-300 mb-1"
                     >
                        TTS Engine
                     </label>
                     <select
                        id="ttsEngine"
                        value={selectedTtsEngine}
                        onChange={e => setSelectedTtsEngine(e.target.value)}
                        className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                     >
                        <option value="">All TTS Engines</option>
                        {ttsEngines.map(engine => (
                           <option key={engine} value={engine}>
                              {formatTtsEngineName(engine)}
                           </option>
                        ))}
                     </select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                     <div>
                        <label
                           htmlFor="dateFrom"
                           className="block text-sm font-medium text-gray-300 mb-1"
                        >
                           From Date
                        </label>
                        <input
                           type="date"
                           id="dateFrom"
                           value={dateFrom}
                           onChange={e => setDateFrom(e.target.value)}
                           className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                        />
                     </div>
                     <div>
                        <label
                           htmlFor="dateTo"
                           className="block text-sm font-medium text-gray-300 mb-1"
                        >
                           To Date
                        </label>
                        <input
                           type="date"
                           id="dateTo"
                           value={dateTo}
                           onChange={e => setDateTo(e.target.value)}
                           className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                        />
                     </div>
                  </div>
                  <div className="flex h-full items-center">
                     <div className="flex items-center justify-center h-full">
                        <div className="mt-5">
                           <label
                              htmlFor="showOnlyActive"
                              className="ml-0 block text-sm text-gray-300"
                           >
                              Has Audio
                           </label>
                           <ToggleSwitch
                              isActive={hasAudio}
                              isUpdating={false}
                              onChange={() => setHasAudio(!hasAudio)}
                           />
                        </div>
                     </div>
                  </div>
                  <div className="md:col-span-1 flex items-end space-x-2">
                     <button
                        type="submit"
                        className="flex-1 px-4 py-2 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-sm hover:shadow-md hover:shadow-emerald-900/50 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:ring-offset-2 text-sm font-medium transition-all duration-300"
                     >
                        Apply Filters
                     </button>
                     <button
                        type="button"
                        onClick={handleResetFilters}
                        className="flex-1 px-4 py-2 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-gray-300 rounded-sm hover:shadow-md focus:outline-none focus:ring-1 focus:ring-gray-500 focus:ring-offset-2 text-sm font-medium transition-all duration-300"
                     >
                        Reset
                     </button>
                  </div>
               </form>
            </div>
         )}
         {(selectedLanguage || selectedTtsEngine || hasAudio !== null || dateFrom || dateTo) && (
            <div className="flex flex-wrap items-center gap-2 mb-4">
               <span className="text-sm text-gray-400 font-medium">Active filters:</span>
               {selectedLanguage && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     Language: {getLanguageName(selectedLanguage)}
                     <button
                        onClick={() => setSelectedLanguage('')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label={`Remove ${getLanguageName(selectedLanguage)} filter`}
                     >
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-3 w-3"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                  </span>
               )}
               {selectedTtsEngine && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     TTS: {formatTtsEngineName(selectedTtsEngine)}
                     <button
                        onClick={() => setSelectedTtsEngine('')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label={`Remove ${formatTtsEngineName(selectedTtsEngine)} filter`}
                     >
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-3 w-3"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                  </span>
               )}
               {hasAudio === true && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border border-emerald-700 relative group">
                     Has Audio
                     <button
                        onClick={() => setHasAudio(null)}
                        className="ml-1.5 text-emerald-500 hover:text-emerald-200 transition-colors duration-200"
                        aria-label="Remove has audio filter"
                     >
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-3 w-3"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                  </span>
               )}
               {dateFrom && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     From: {dateFrom}
                     <button
                        onClick={() => setDateFrom('')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label="Remove date from filter"
                     >
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-3 w-3"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                  </span>
               )}
               {dateTo && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     To: {dateTo}
                     <button
                        onClick={() => setDateTo('')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label="Remove date to filter"
                     >
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-3 w-3"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                  </span>
               )}
            </div>
         )}
         {loading ? (
            <div className="flex items-center justify-center h-48">
               <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
         ) : error ? (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm p-6 text-center border border-gray-700">
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-12 w-12 text-yellow-500 mx-auto mb-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
               >
                  <path
                     strokeLinecap="round"
                     strokeLinejoin="round"
                     strokeWidth={1.5}
                     d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
               </svg>
               <h2 className="text-lg font-medium text-gray-300 mb-2">Error Loading Podcasts</h2>
               <p className="text-gray-400 mb-4">
                  We encountered an error while loading podcasts. Please try again later.
               </p>
               <div className="text-sm text-gray-500 bg-gradient-to-r from-gray-900 to-gray-800 p-3 rounded-sm mx-auto max-w-md border border-gray-700">
                  <p className="font-semibold mb-1 text-gray-400">Technical details:</p>
                  <p className="font-mono text-xs break-all text-red-400">{error}</p>
               </div>
            </div>
         ) : podcasts.length === 0 ? (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm p-8 text-center border border-gray-700">
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-12 w-12 text-gray-600 mx-auto mb-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
               >
                  <path
                     strokeLinecap="round"
                     strokeLinejoin="round"
                     strokeWidth={1}
                     d="M19 9l-7 7-7-7"
                  />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 17V5" />
               </svg>
               <p className="text-lg text-gray-300 font-medium">No podcasts found</p>
               <p className="text-gray-400 mt-1">Try adjusting your filters or search query</p>
            </div>
         ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
               {podcasts.map(podcast => (
                  <Link
                     key={podcast.id}
                     to={`/podcasts/${podcast.identifier}`}
                     className="block bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-gray-700 hover:border-gray-600 transition-all duration-300 transform hover:scale-[1.02] hover:shadow-xl"
                     onMouseEnter={() => setHoveredItem(podcast.identifier)}
                     onMouseLeave={() => setHoveredItem(null)}
                  >
                     <div className="relative">
                        {podcast.banner_img ? (
                           <div className="h-32 w-full overflow-hidden relative">
                              <img
                                 src={api.API_BASE_URL + '/podcast_img/' + podcast.banner_img}
                                 alt={podcast.title}
                                 className="w-full h-full object-cover"
                              />
                              <div className="absolute inset-0 bg-gradient-to-t from-gray-900 to-transparent"></div>
                              {podcast.audio_generated && (
                                 <div className="absolute top-2 right-2 flex items-center bg-gray-900 bg-opacity-75 px-2 py-1 rounded-full text-emerald-400 text-xs">
                                    <svg
                                       xmlns="http://www.w3.org/2000/svg"
                                       className="h-3 w-3 mr-1"
                                       fill="none"
                                       viewBox="0 0 24 24"
                                       stroke="currentColor"
                                    >
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                                       />
                                    </svg>
                                    Audio
                                 </div>
                              )}
                           </div>
                        ) : (
                           <div className="h-32 flex items-center justify-center bg-gradient-to-r from-gray-900 to-gray-800 border-b border-gray-700 relative">
                              <div className="h-14 w-14 bg-gradient-to-b from-gray-700 to-gray-800 rounded-full flex items-center justify-center border border-gray-600 shadow-lg">
                                 <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    className={`h-8 w-8 ${
                                       hoveredItem === podcast.identifier
                                          ? 'text-emerald-400'
                                          : 'text-gray-400'
                                    } transition-colors duration-200`}
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                 >
                                    <path
                                       strokeLinecap="round"
                                       strokeLinejoin="round"
                                       strokeWidth={2}
                                       d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                                    />
                                 </svg>
                              </div>
                              {podcast.audio_generated && (
                                 <div className="absolute top-2 right-2 flex items-center bg-gray-900 bg-opacity-75 px-2 py-1 rounded-full text-emerald-400 text-xs">
                                    <svg
                                       xmlns="http://www.w3.org/2000/svg"
                                       className="h-3 w-3 mr-1"
                                       fill="none"
                                       viewBox="0 0 24 24"
                                       stroke="currentColor"
                                    >
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                                       />
                                    </svg>
                                    Audio
                                 </div>
                              )}
                           </div>
                        )}
                        <div className="p-4">
                           <h2
                              className={`text-md font-medium mb-1 transition-colors duration-200 line-clamp-2 ${
                                 hoveredItem === podcast.identifier
                                    ? 'text-emerald-300'
                                    : 'text-gray-200'
                              }`}
                           >
                              {podcast.title || `Podcast - ${formatDate(podcast.date)}`}
                           </h2>
                           <div className="flex items-center text-xs text-gray-400">
                              <svg
                                 xmlns="http://www.w3.org/2000/svg"
                                 className="h-3.5 w-3.5 mr-1 text-gray-500"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                              >
                                 <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                                 />
                              </svg>
                              <span>{formatDate(podcast.date)}</span>
                           </div>
                           <div className="mt-3 flex flex-wrap gap-1">
                              {podcast.language_code && (
                                 <span className="inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium bg-gradient-to-r from-blue-900 to-blue-800 text-blue-300 border border-blue-800">
                                    <svg
                                       xmlns="http://www.w3.org/2000/svg"
                                       className="h-3 w-3 mr-0.5"
                                       fill="none"
                                       viewBox="0 0 24 24"
                                       stroke="currentColor"
                                    >
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
                                       />
                                    </svg>
                                    {getLanguageName(podcast.language_code)}
                                 </span>
                              )}
                              {podcast.tts_engine && podcast.tts_engine && (
                                 <span className="inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium bg-gradient-to-r from-purple-900 to-purple-800 text-purple-300 border border-purple-800">
                                   <Sparkles className="w-3 h-3 mr-1" />
                                    {formatTtsEngineName(podcast.tts_engine)}
                                 </span>
                              )}
                           </div>
                        </div>
                        <div
                           className={`absolute bottom-3 right-3 w-6 h-6 flex items-center justify-center rounded-full bg-gray-900 bg-opacity-70 text-emerald-400 transition-opacity duration-200 ${
                              hoveredItem === podcast.identifier ? 'opacity-100' : 'opacity-0'
                           }`}
                        >
                           <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-3.5 w-3.5"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                           >
                              <path
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                                 strokeWidth={2}
                                 d="M9 5l7 7-7 7"
                              />
                           </svg>
                        </div>
                     </div>
                  </Link>
               ))}
            </div>
         )}
         {!loading && !error && podcasts.length > 0 && (
            <div className="mt-6 flex items-center justify-between bg-gradient-to-r from-gray-800 to-gray-900 p-3 rounded-sm border-t border-gray-700">
               <div className="flex items-center text-xs text-gray-400">
                  Showing <span className="font-medium text-gray-300 px-1">{podcasts.length}</span>{' '}
                  of <span className="font-medium text-gray-300 px-1">{totalItems}</span> results
               </div>
               <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-end">
                  <nav
                     className="inline-flex -space-x-px rounded-sm shadow-sm"
                     aria-label="Pagination"
                  >
                     <button
                        onClick={() => setPage(1)}
                        disabled={!hasPrev}
                        className={`relative inline-flex items-center rounded-l-sm px-2 py-1 ${
                           hasPrev
                              ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                              : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-600 border border-gray-700 cursor-not-allowed opacity-70'
                        } transition-colors duration-200`}
                     >
                        <span className="sr-only">First</span>
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-5 w-5"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M15.707 15.707a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 010 1.414zm-6 0a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 1.414L5.414 10l4.293 4.293a1 1 0 010 1.414z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                     <button
                        onClick={() => setPage(page - 1)}
                        disabled={!hasPrev}
                        className={`relative inline-flex items-center px-2 py-1 ${
                           hasPrev
                              ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                              : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-600 border border-gray-700 cursor-not-allowed opacity-70'
                        } transition-colors duration-200`}
                     >
                        <span className="sr-only">Previous</span>
                        <svg
                           className="h-5 w-5"
                           xmlns="http://www.w3.org/2000/svg"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                           aria-hidden="true"
                        >
                           <path
                              fillRule="evenodd"
                              d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                     <span className="relative inline-flex items-center px-4 py-1 text-sm font-medium bg-gradient-to-b from-gray-700 to-gray-800 text-emerald-400 border border-gray-600">
                        Page {page} of {totalPages}
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400 opacity-70"></span>
                     </span>
                     <button
                        onClick={() => setPage(page + 1)}
                        disabled={!hasNext}
                        className={`relative inline-flex items-center px-2 py-1 ${
                           hasNext
                              ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                              : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-600 border border-gray-700 cursor-not-allowed opacity-70'
                        } transition-colors duration-200`}
                     >
                        <span className="sr-only">Next</span>
                        <svg
                           className="h-5 w-5"
                           xmlns="http://www.w3.org/2000/svg"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                           aria-hidden="true"
                        >
                           <path
                              fillRule="evenodd"
                              d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                     <button
                        onClick={() => setPage(totalPages)}
                        disabled={!hasNext}
                        className={`relative inline-flex items-center rounded-r-sm px-2 py-1 ${
                           hasNext
                              ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                              : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-600 border border-gray-700 cursor-not-allowed opacity-70'
                        } transition-colors duration-200`}
                     >
                        <span className="sr-only">Last</span>
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-5 w-5"
                           viewBox="0 0 20 20"
                           fill="currentColor"
                        >
                           <path
                              fillRule="evenodd"
                              d="M10.293 15.707a1 1 0 010-1.414L14.586 10l-4.293-4.293a1 1 0 111.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z"
                              clipRule="evenodd"
                           />
                           <path
                              fillRule="evenodd"
                              d="M4.293 15.707a1 1 0 010-1.414L8.586 10 4.293 5.707a1 1 0 011.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z"
                              clipRule="evenodd"
                           />
                        </svg>
                     </button>
                  </nav>
               </div>
               <div className="flex flex-1 justify-between sm:hidden">
                  <button
                     onClick={() => setPage(page - 1)}
                     disabled={!hasPrev}
                     className={`relative inline-flex items-center rounded-sm px-4 py-2 text-sm font-medium ${
                        hasPrev
                           ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-300 border border-gray-700 hover:bg-gray-700'
                           : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-500 border border-gray-700 cursor-not-allowed'
                     } transition-colors duration-200`}
                  >
                     Previous
                  </button>
                  <button
                     onClick={() => setPage(page + 1)}
                     disabled={!hasNext}
                     className={`relative ml-3 inline-flex items-center rounded-sm px-4 py-2 text-sm font-medium ${
                        hasNext
                           ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-300 border border-gray-700 hover:bg-gray-700'
                           : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-500 border border-gray-700 cursor-not-allowed'
                     } transition-colors duration-200`}
                  >
                     Next
                  </button>
               </div>
            </div>
         )}
      </div>
   );
};

export default Podcasts;
