import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

const Sources = () => {
   const navigate = useNavigate();
   const [sources, setSources] = useState([]);
   const [categories, setCategories] = useState([]);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [hoveredCard, setHoveredCard] = useState(null);
   const [page, setPage] = useState(1);
   const [perPage, setPerPage] = useState(10);
   const [totalPages, setTotalPages] = useState(0);
   const [totalItems, setTotalItems] = useState(0);
   const [hasNext, setHasNext] = useState(false);
   const [hasPrev, setHasPrev] = useState(false);
   const [selectedCategory, setSelectedCategory] = useState('');
   const [searchQuery, setSearchQuery] = useState('');
   const [showOnlyActive, setShowOnlyActive] = useState(false);
   const [isFilterOpen, setIsFilterOpen] = useState(false);
   const [updatingSourceId, setUpdatingSourceId] = useState(null);

   useEffect(() => {
      const fetchCategories = async () => {
         try {
            const response = await api.sources.getCategories();
            setCategories(response.data || []);
         } catch (err) {
            console.error('Error fetching categories:', err);
         }
      };
      fetchCategories();
   }, []);

   useEffect(() => {
      const fetchSources = async () => {
         setLoading(true);
         setError(null);
         try {
            const params = {
               page,
               per_page: perPage,
            };
            if (selectedCategory) params.category = selectedCategory;
            if (searchQuery) params.search = searchQuery;
            params.include_inactive = !showOnlyActive;
            const response = await api.sources.getAll(params);
            const data = response.data;
            setSources(data.items || []);
            setTotalPages(data.total_pages || 0);
            setTotalItems(data.total || 0);
            setHasNext(data.has_next || false);
            setHasPrev(data.has_prev || false);
         } catch (err) {
            setError(`Failed to fetch sources: ${err.message}`);
            console.error('Error fetching sources:', err);
         } finally {
            setLoading(false);
         }
      };

      fetchSources();
   }, [page, perPage, selectedCategory, searchQuery, showOnlyActive]);

   const handleFilterSubmit = e => {
      e.preventDefault();
      setPage(1);
      setIsFilterOpen(false);
   };

   const handleResetFilters = () => {
      setSelectedCategory('');
      setSearchQuery('');
      setShowOnlyActive(false);
      setPage(1);
      setIsFilterOpen(false);
   };

   const handleDeleteSource = async sourceId => {
      if (
         window.confirm(
            'Are you sure you want to delete this source? This action cannot be undone.'
         )
      ) {
         try {
            await api.sources.delete(sourceId);
            setSources(sources.filter(source => source.id !== sourceId));
            if (sources.length === 1 && page > 1) {
               setPage(page - 1);
            }
         } catch (err) {
            console.error('Error deleting source:', err);
            alert(`Failed to delete source: ${err.message}`);
         }
      }
   };

   const handleToggleSourceStatus = async (sourceId, currentStatus) => {
      setUpdatingSourceId(sourceId);
      try {
         const updatedSource = await api.sources.update(sourceId, {
            is_active: !currentStatus,
         });
         setSources(
            sources.map(source =>
               source.id === sourceId
                  ? { ...source, is_active: updatedSource.data.is_active }
                  : source
            )
         );
      } catch (err) {
         console.error('Error updating source status:', err);
         alert(`Failed to update source status: ${err.message}`);
      } finally {
         setUpdatingSourceId(null);
      }
   };

   const formatDate = dateString => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString(undefined, {
         year: 'numeric',
         month: 'short',
         day: 'numeric',
      });
   };

   const renderCategories = categories => {
      if (!categories || categories.length === 0) {
         return <span className="text-gray-500 text-xs">Uncategorized</span>;
      }
      if (categories.length > 1) {
         return (
            <div className="flex flex-col space-y-1">
               <div className="flex items-center">
                  <span className="px-2 py-1 inline-flex text-xs leading-5 font-medium rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-emerald-300 border border-gray-700">
                     {categories[0]}
                  </span>
                  <span className="ml-2 text-xs text-gray-400">+{categories.length - 1} more</span>
               </div>
               <div className="hidden group-hover:block absolute z-10 mt-1 ml-4 bg-gray-800 shadow-lg rounded-sm p-2 border border-gray-700">
                  <div className="flex flex-wrap gap-1">
                     {categories.map((cat, idx) => (
                        <span
                           key={idx}
                           className="px-2 py-1 text-xs leading-5 font-medium rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-emerald-300 border border-gray-700"
                        >
                           {cat}
                        </span>
                     ))}
                  </div>
               </div>
            </div>
         );
      }
      return (
         <span className="px-2 py-1 inline-flex text-xs leading-5 font-medium rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-emerald-300 border border-gray-700">
            {categories[0]}
         </span>
      );
   };

   const ToggleSwitch = ({ isActive, isUpdating, onChange }) => {
      return (
         <button
            onClick={onChange}
            disabled={isUpdating}
            className={`relative inline-flex h-5 w-10 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 ${
               isUpdating ? 'cursor-wait opacity-70' : ''
            } ${
               isActive
                  ? 'bg-emerald-600 focus:ring-emerald-500'
                  : 'bg-gray-700 focus:ring-gray-500'
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
                           d="M12 8C16.4183 8 20 6.65685 20 5C20 3.34315 16.4183 2 12 2C7.58172 2 4 3.34315 4 5C4 6.65685 7.58172 8 12 8Z"
                           stroke="currentColor"
                           strokeWidth="1.5"
                           strokeLinecap="round"
                           strokeLinejoin="round"
                        />
                        <path
                           d="M4 5V12C4 13.66 7.58 15 12 15C16.42 15 20 13.66 20 12V5"
                           stroke="currentColor"
                           strokeWidth="1.5"
                           strokeLinecap="round"
                           strokeLinejoin="round"
                        />
                        <path
                           d="M4 12V19C4 20.66 7.58 22 12 22C16.42 22 20 20.66 20 19V12"
                           stroke="currentColor"
                           strokeWidth="1.5"
                           strokeLinecap="round"
                           strokeLinejoin="round"
                        />
                     </svg>
                     <div className="absolute inset-0 bg-emerald-500 opacity-30 blur-md rounded-full"></div>
                  </div>
               </div>
               <h1 className="text-2xl font-medium text-gray-100 ml-10">Sources</h1>
            </div>
            <div className="flex items-center space-x-2">
               <div className="relative flex-grow">
                  <input
                     type="text"
                     value={searchQuery}
                     onChange={e => setSearchQuery(e.target.value)}
                     placeholder="Search sources..."
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
               <button
                  onClick={() => navigate('/sources/new')}
                  className="flex items-center justify-center p-2 bg-gradient-to-r from-emerald-700 to-emerald-800 border border-emerald-600 rounded-sm shadow-sm hover:from-emerald-600 hover:to-emerald-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-colors duration-200 group"
               >
                  <svg
                     xmlns="http://www.w3.org/2000/svg"
                     className="h-5 w-5 text-gray-200 group-hover:text-white transition-colors duration-200"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                     />
                  </svg>
                  <span className="ml-1 text-sm font-medium text-gray-200 group-hover:text-white transition-colors duration-200">
                     Add Source
                  </span>
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
                     <label
                        htmlFor="category"
                        className="block text-sm font-medium text-gray-300 mb-1"
                     >
                        Category
                     </label>
                     <select
                        id="category"
                        value={selectedCategory}
                        onChange={e => setSelectedCategory(e.target.value)}
                        className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                     >
                        <option value="">All Categories</option>
                        {categories.map(category => (
                           <option key={category.id} value={category.name}>
                              {category.name}
                           </option>
                        ))}
                     </select>
                  </div>
                  <div className="flex h-full items-center">
                     <div className="flex items-center justify-center h-full">
                        <div className="mt-5">
                           <label
                              htmlFor="showOnlyActive"
                              className="ml-0 block text-sm text-gray-300"
                           >
                              Show only active sources
                           </label>
                           <ToggleSwitch
                              isActive={showOnlyActive}
                              isUpdating={false}
                              onChange={() => setShowOnlyActive(!showOnlyActive)}
                           />
                        </div>
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
         {(selectedCategory || showOnlyActive) && (
            <div className="flex flex-wrap items-center gap-2 mb-4">
               <span className="text-sm text-gray-400 font-medium">Active filters:</span>
               {selectedCategory && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 border border-gray-700">
                     Category: {selectedCategory}
                     <button
                        onClick={() => setSelectedCategory('')}
                        className="ml-1.5 text-gray-500 hover:text-emerald-300 transition-colors duration-200"
                        aria-label={`Remove ${selectedCategory} filter`}
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
               {showOnlyActive && (
                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border border-emerald-700 relative group">
                     Active sources only
                     <button
                        onClick={() => setShowOnlyActive(false)}
                        className="ml-1.5 text-emerald-500 hover:text-emerald-200 transition-colors duration-200"
                        aria-label="Remove active only filter"
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
         ) : sources.length === 0 ? (
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
               <p className="text-lg text-gray-300 font-medium">No sources found</p>
               <p className="text-gray-400 mt-1">Try adjusting your filters or search query</p>
               <Link
                  to="/sources/new"
                  className="mt-4 inline-block px-4 py-2 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-sm hover:shadow-md hover:shadow-emerald-900/50 transition-all duration-300"
               >
                  Add New Source
               </Link>
            </div>
         ) : (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-gray-700">
               <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
               <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-700">
                     <thead className="bg-gradient-to-r from-gray-900 to-gray-800">
                        <tr>
                           <th
                              scope="col"
                              className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                           >
                              Name
                           </th>
                           <th
                              scope="col"
                              className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                           >
                              Category
                           </th>
                           <th
                              scope="col"
                              className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                           >
                              Status
                           </th>
                           <th
                              scope="col"
                              className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                           >
                              Last Crawled
                           </th>
                           <th
                              scope="col"
                              className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider"
                           >
                              Actions
                           </th>
                        </tr>
                     </thead>
                     <tbody className="divide-y divide-gray-700">
                        {sources.map(source => (
                           <tr
                              key={source.id}
                              className={`hover:bg-gray-800 transition-all duration-200 group ${
                                 !source.is_active ? 'bg-gray-900/60' : ''
                              }`}
                              onMouseEnter={() => setHoveredCard(source.id)}
                              onMouseLeave={() => setHoveredCard(null)}
                           >
                              <td className="px-6 py-4 whitespace-nowrap">
                                 <div className="flex items-center">
                                    <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-full bg-gradient-to-r from-gray-800 to-gray-900 border border-gray-700 text-emerald-400">
                                       {source.name.substring(0, 2).toUpperCase()}
                                    </div>
                                    <div className="ml-4">
                                       <div className="text-sm font-medium text-gray-200">
                                          {source.name}
                                       </div>
                                       <div className="text-xs text-gray-400 truncate max-w-xs">
                                          {source.website || source.url || 'No website provided'}
                                       </div>
                                    </div>
                                 </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap relative">
                                 {renderCategories(source.categories)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                 <div className="flex items-center space-x-3">
                                    <ToggleSwitch
                                       isActive={source.is_active}
                                       isUpdating={updatingSourceId === source.id}
                                       onChange={() =>
                                          handleToggleSourceStatus(source.id, source.is_active)
                                       }
                                    />
                                    <span
                                       className={`text-xs ${
                                          source.is_active ? 'text-emerald-400' : 'text-gray-500'
                                       }`}
                                    >
                                       {source.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                 </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                                 {source.last_crawled ? formatDate(source.last_crawled) : 'Never'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                 <div className="flex justify-end space-x-2">
                                    <Link
                                       to={`/sources/${source.id}`}
                                       className={`text-gray-400 hover:text-emerald-400 transition-colors duration-200 ${
                                          hoveredCard === source.id ? 'text-emerald-400' : ''
                                       }`}
                                    >
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
                                             d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                          />
                                          <path
                                             strokeLinecap="round"
                                             strokeLinejoin="round"
                                             strokeWidth={2}
                                             d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                                          />
                                       </svg>
                                    </Link>
                                    <Link
                                       to={`/sources/${source.id}/edit`}
                                       className="text-gray-400 hover:text-blue-400 transition-colors duration-200"
                                    >
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
                                             d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                          />
                                       </svg>
                                    </Link>
                                    <button
                                       onClick={() => handleDeleteSource(source.id)}
                                       className="text-gray-400 hover:text-red-400 transition-colors duration-200"
                                    >
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
                                             d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                          />
                                       </svg>
                                    </button>
                                 </div>
                              </td>
                           </tr>
                        ))}
                     </tbody>
                  </table>
               </div>
            </div>
         )}
         {!loading && !error && sources.length > 0 && (
            <div className="mt-6 flex items-center justify-between bg-gradient-to-r from-gray-800 to-gray-900 p-3 rounded-sm border-t border-gray-700">
               <div className="flex items-center text-xs text-gray-400">
                  Showing <span className="font-medium text-gray-300 px-1">{sources.length}</span>{' '}
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

export default Sources;
