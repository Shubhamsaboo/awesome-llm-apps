import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import SourceSelector from '../components/SourceSelector';

const Articles = () => {
   const [articles, setArticles] = useState([]);
   const [sources, setSources] = useState([]);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [hoveredCard, setHoveredCard] = useState(null);
   const [page, setPage] = useState(1);
   const [perPage, setPerPage] = useState(10);
   const [totalPages, setTotalPages] = useState(0);
   const [totalItems, setTotalItems] = useState(0);
   const [hasNext, setHasNext] = useState(false);
   const [hasPrev, setHasPrev] = useState(false);
   const [selectedSource, setSelectedSource] = useState('');
   const [dateFrom, setDateFrom] = useState('');
   const [dateTo, setDateTo] = useState('');
   const [searchQuery, setSearchQuery] = useState('');
   const [isFilterOpen, setIsFilterOpen] = useState(false);
   useEffect(() => {
      const fetchSources = async () => {
         try {
            const response = await api.articles.getSources();
            setSources(response.data || []);
         } catch (err) {
            console.error('Error fetching sources:', err);
         }
      };
      fetchSources();
   }, []);

   useEffect(() => {
      const fetchArticles = async () => {
         setLoading(true);
         setError(null);
         try {
            const params = {
               page,
               per_page: perPage,
            };
            if (selectedSource) params.source = selectedSource;
            if (dateFrom) params.date_from = dateFrom;
            if (dateTo) params.date_to = dateTo;
            if (searchQuery) params.search = searchQuery;
            const response = await api.articles.getAll(params);
            const data = response.data;
            setArticles(data.items || []);
            setTotalPages(data.total_pages || 0);
            setTotalItems(data.total || 0);
            setHasNext(data.has_next || false);
            setHasPrev(data.has_prev || false);
         } catch (err) {
            setError(`Failed to fetch articles: ${err.message}`);
            console.error('Error fetching articles:', err);
         } finally {
            setLoading(false);
         }
      };

      fetchArticles();
   }, [page, perPage, selectedSource, dateFrom, dateTo, searchQuery]);

   const handleFilterSubmit = e => {
      e.preventDefault();
      setPage(1);
      setIsFilterOpen(false);
   };

   const handleResetFilters = () => {
      setSearchQuery('');
      setDateFrom('');
      setDateTo('');
      setPage(1);
      setIsFilterOpen(false);
   };

   const formatDate = dateString => {
      if (!dateString) return '';
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString(undefined, options);
   };

   const renderCategories = categories => {
      if (!categories || categories.length === 0) {
         return null;
      }
      if (categories.length > 1) {
         return (
            <span className="flex items-center">
               <span>{categories[0]}</span>
               <span className="ml-1 text-xs text-gray-500">+{categories.length - 1}</span>
            </span>
         );
      }
      return <span>{categories[0]}</span>;
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
                        <path d="M19 5V19H5V5H19ZM21 3H3V21H21V3Z" fill="currentColor" />
                        <path d="M7 7H12V12H7V7Z" fill="currentColor" />
                        <path d="M14 7H17V9H14V7Z" fill="currentColor" />
                        <path d="M14 10H17V12H14V10Z" fill="currentColor" />
                        <path d="M7 13H17V15H7V13Z" fill="currentColor" />
                        <path d="M7 16H17V18H7V16Z" fill="currentColor" />
                     </svg>
                     <div className="absolute inset-0 bg-emerald-500 opacity-30 blur-md rounded-full"></div>
                  </div>
               </div>
               <h1 className="text-2xl font-medium text-gray-100 ml-10">Latest Articles</h1>
            </div>
            <div className="flex items-center space-x-2">
               <div className="relative flex-grow">
                  <input
                     type="text"
                     value={searchQuery}
                     onChange={e => setSearchQuery(e.target.value)}
                     placeholder="Search articles..."
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
                  className="space-y-4 md:space-y-0 md:grid md:grid-cols-3 md:gap-4"
               >
                  <div>
                     <SourceSelector
                        sources={sources}
                        selectedSource={selectedSource}
                        onSourceChange={setSelectedSource}
                     />
                  </div>
                  <div className="flex space-x-2">
                     <div className="w-1/2">
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
                     <div className="w-1/2">
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
                  <div className="flex items-end space-x-2">
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
         {(selectedSource || dateFrom || dateTo) && (
            <div className="flex flex-wrap items-center gap-2 mb-4">
               <span className="text-sm text-gray-400 font-medium">Active filters:</span>
               {selectedSource && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     Source: {selectedSource}
                     <button
                        onClick={() => setSelectedSource('')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label={`Remove ${selectedSource} filter`}
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
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border border-emerald-700 relative group">
                     From: {dateFrom}
                     <button
                        onClick={() => setDateFrom('')}
                        className="ml-1.5 text-emerald-500 hover:text-emerald-200 transition-colors duration-200"
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
                     <span className="absolute inset-0 rounded-sm bg-emerald-400 blur-sm opacity-0 group-hover:opacity-20 transition-opacity duration-300"></span>
                  </span>
               )}
               {dateTo && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border border-emerald-700 relative group">
                     To: {dateTo}
                     <button
                        onClick={() => setDateTo('')}
                        className="ml-1.5 text-emerald-500 hover:text-emerald-200 transition-colors duration-200"
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
                     <span className="absolute inset-0 rounded-sm bg-emerald-400 blur-sm opacity-0 group-hover:opacity-20 transition-opacity duration-300"></span>
                  </span>
               )}
            </div>
         )}
         {loading ? (
            <div className="flex items-center justify-center h-64">
               <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
         ) : error ? (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border-l-4 border-red-500 p-4 rounded-sm shadow-sm mb-6">
               <div className="flex">
                  <div className="flex-shrink-0">
                     <svg
                        className="h-5 w-5 text-red-500"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                     >
                        <path
                           fillRule="evenodd"
                           d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                           clipRule="evenodd"
                        />
                     </svg>
                  </div>
                  <div className="ml-3">
                     <p className="text-sm text-red-400">{error}</p>
                  </div>
               </div>
            </div>
         ) : articles.length === 0 ? (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm p-12 text-center border border-gray-700">
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-16 w-16 text-gray-600 mx-auto mb-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
               >
                  <path
                     strokeLinecap="round"
                     strokeLinejoin="round"
                     strokeWidth={1}
                     d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
                  />
               </svg>
               <p className="text-lg text-gray-300 font-medium">No articles found</p>
               <p className="text-gray-400 mt-1">Try adjusting your filters or search query</p>
            </div>
         ) : (
            <div className="grid grid-cols-1 gap-4">
               {articles.map((article, index) => (
                  <div
                     key={article.id}
                     className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg hover:shadow-xl transition-all duration-300 rounded-sm border-t border-gray-700 transform hover:scale-[1.01]"
                     onMouseEnter={() => setHoveredCard(article.id)}
                     onMouseLeave={() => setHoveredCard(null)}
                  >
                     <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
                     {index % 2 === 1 && (
                        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-emerald-400 via-emerald-600 to-transparent"></div>
                     )}
                     <Link
                        to={`/articles/${article.id}`}
                        className="block p-5 relative overflow-hidden"
                     >
                        {article.featured && (
                           <div
                              className="absolute top-0 right-0 w-16 h-16 opacity-5"
                              style={{
                                 backgroundImage:
                                    'repeating-linear-gradient(45deg, #10B981 0, #10B981 1px, transparent 0, transparent 10px)',
                                 clipPath: 'polygon(100% 0, 0% 0, 100% 100%)',
                              }}
                           ></div>
                        )}
                        <div className="flex flex-col sm:flex-row sm:items-start">
                           <div className="flex-1">
                              <div className="flex items-center text-xs text-gray-400 mb-2">
                                 <span className="px-2 py-1 bg-gradient-to-r from-gray-900 to-gray-800 text-emerald-300 rounded-sm font-medium">
                                    {article.source_name}
                                 </span>
                                 <span className="mx-2 text-gray-600">•</span>
                                 <span className="flex items-center">
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
                                    {formatDate(article.published_date)}
                                 </span>
                                 {article.categories && article.categories.length > 0 && (
                                    <>
                                       <span className="mx-2 text-gray-600">•</span>
                                       <span className="flex items-center">
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
                                                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                                             />
                                          </svg>
                                          {renderCategories(article.categories)}
                                       </span>
                                    </>
                                 )}
                              </div>
                              <h3
                                 className={`text-lg font-medium mb-2 ${
                                    hoveredCard === article.id
                                       ? 'text-emerald-300'
                                       : 'text-gray-200'
                                 } transition-colors duration-200`}
                              >
                                 {article.title}
                              </h3>
                              {article.summary && (
                                 <p className="text-sm text-gray-400 line-clamp-2 mt-1">
                                    {article.summary}
                                 </p>
                              )}
                              <div className="mt-3">
                                 <span
                                    className={`text-xs font-medium text-gray-300 border border-gray-600 px-3 py-1 rounded-sm hover:bg-gray-700 inline-block ${
                                       hoveredCard === article.id
                                          ? 'border-emerald-400 text-emerald-300'
                                          : ''
                                    } transition-colors duration-200`}
                                 >
                                    Read more
                                 </span>
                              </div>
                           </div>
                        </div>
                     </Link>
                  </div>
               ))}
            </div>
         )}
         {!loading && !error && articles.length > 0 && (
            <div className="mt-6 flex items-center justify-between bg-gradient-to-r from-gray-800 to-gray-900 p-3 rounded-sm border-t border-gray-700">
               <div className="flex items-center text-xs text-gray-400">
                  Showing <span className="font-medium text-gray-300 px-1">{articles.length}</span>{' '}
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
                        {/* Active page indicator with subtle glow */}
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

export default Articles;
