import React from 'react';

const Filters = ({
   isOpen,
   filters,
   platforms,
   sentiments,
   categories,
   handleFilterChange,
   resetFilters,
   setIsFilterOpen,
}) => {
   return (
      <>
         {isOpen && (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm p-4 mb-4 border border-gray-700">
               <form
                  onSubmit={e => {
                     e.preventDefault();
                     setIsFilterOpen(false);
                  }}
                  className="space-y-4 md:space-y-0 md:grid md:grid-cols-3 md:gap-4"
               >
                  <div>
                     <label
                        htmlFor="platform"
                        className="block text-xs font-medium text-gray-300 mb-1"
                     >
                        Platform
                     </label>
                     <select
                        id="platform"
                        className="w-full px-3 py-1.5 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 text-xs text-gray-300 transition-all"
                        value={filters.platform}
                        onChange={e => handleFilterChange('platform', e.target.value)}
                     >
                        <option value="">All Platforms</option>
                        {platforms.map(platform => (
                           <option key={platform} value={platform}>
                              {platform.charAt(0).toUpperCase() + platform.slice(1)}
                           </option>
                        ))}
                     </select>
                  </div>
                  <div>
                     <label
                        htmlFor="sentiment"
                        className="block text-xs font-medium text-gray-300 mb-1"
                     >
                        Sentiment
                     </label>
                     <select
                        id="sentiment"
                        className="w-full px-3 py-1.5 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 text-xs text-gray-300 transition-all"
                        value={filters.sentiment}
                        onChange={e => handleFilterChange('sentiment', e.target.value)}
                     >
                        <option value="">All Sentiments</option>
                        {sentiments.map(sentiment => (
                           <option key={sentiment} value={sentiment}>
                              {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                           </option>
                        ))}
                     </select>
                  </div>
                  <div>
                     <label
                        htmlFor="category"
                        className="block text-xs font-medium text-gray-300 mb-1"
                     >
                        Category
                     </label>
                     <select
                        id="category"
                        className="w-full px-3 py-1.5 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 text-xs text-gray-300 transition-all"
                        value={filters.category}
                        onChange={e => handleFilterChange('category', e.target.value)}
                     >
                        <option value="">All Categories</option>
                        {categories.map(category => (
                           <option key={category} value={category}>
                              {category.charAt(0).toUpperCase() + category.slice(1)}
                           </option>
                        ))}
                     </select>
                  </div>
                  <div className="flex space-x-2">
                     <div className="w-1/2">
                        <label
                           htmlFor="dateFrom"
                           className="block text-xs font-medium text-gray-300 mb-1"
                        >
                           From Date
                        </label>
                        <input
                           type="date"
                           id="dateFrom"
                           value={filters.dateFrom}
                           onChange={e => handleFilterChange('dateFrom', e.target.value)}
                           className="w-full px-2 py-1.5 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 text-xs text-gray-300 transition-all"
                        />
                     </div>
                     <div className="w-1/2">
                        <label
                           htmlFor="dateTo"
                           className="block text-xs font-medium text-gray-300 mb-1"
                        >
                           To Date
                        </label>
                        <input
                           type="date"
                           id="dateTo"
                           value={filters.dateTo}
                           onChange={e => handleFilterChange('dateTo', e.target.value)}
                           className="w-full px-2 py-1.5 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 text-xs text-gray-300 transition-all"
                        />
                     </div>
                  </div>
                  <div className="md:col-span-3 flex items-end space-x-2 mt-3 md:mt-0">
                     <button
                        type="submit"
                        className="flex-1 px-4 py-1.5 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-sm hover:shadow-md hover:shadow-emerald-900/50 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-xs font-medium transition-all duration-300"
                     >
                        Apply Filters
                     </button>
                     <button
                        type="button"
                        onClick={resetFilters}
                        className="flex-1 px-4 py-1.5 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-gray-300 rounded-sm hover:shadow-md focus:outline-none focus:ring-1 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-xs font-medium transition-all duration-300 border border-gray-700"
                     >
                        Reset
                     </button>
                  </div>
               </form>
            </div>
         )}
         {(filters.platform ||
            filters.sentiment ||
            filters.category ||
            filters.dateFrom ||
            filters.dateTo) && (
            <div className="flex flex-wrap items-center gap-2 mb-4">
               <span className="text-xs text-gray-400 font-medium">Active filters:</span>
               {filters.platform && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     Platform: {filters.platform}
                     <button
                        onClick={() => handleFilterChange('platform', '')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label={`Remove ${filters.platform} filter`}
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
               {filters.sentiment && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     Sentiment: {filters.sentiment}
                     <button
                        onClick={() => handleFilterChange('sentiment', '')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label={`Remove ${filters.sentiment} filter`}
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
               {filters.category && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     Category: {filters.category}
                     <button
                        onClick={() => handleFilterChange('category', '')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label={`Remove ${filters.category} filter`}
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
               {filters.dateFrom && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border border-emerald-700 relative group">
                     From: {filters.dateFrom}
                     <button
                        onClick={() => handleFilterChange('dateFrom', '')}
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
                  </span>
               )}
               {filters.dateTo && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border border-emerald-700 relative group">
                     To: {filters.dateTo}
                     <button
                        onClick={() => handleFilterChange('dateTo', '')}
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
                  </span>
               )}
            </div>
         )}
      </>
   );
};

export default Filters;
