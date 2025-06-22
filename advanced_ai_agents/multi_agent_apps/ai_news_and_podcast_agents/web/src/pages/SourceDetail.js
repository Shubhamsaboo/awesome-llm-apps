import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

const SourceDetail = () => {
   const { sourceId } = useParams();
   const navigate = useNavigate();
   const [source, setSource] = useState(null);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [hoveredFeed, setHoveredFeed] = useState(null);
   const [isAddFeedModalOpen, setIsAddFeedModalOpen] = useState(false);
   const [newFeed, setNewFeed] = useState({
      feed_url: '',
      feed_type: 'main',
      description: '',
      is_active: true,
   });

   const fetchSourceDetail = async () => {
      setLoading(true);
      setError(null);
      try {
         const response = await api.sources.getById(sourceId);
         setSource(response.data);
      } catch (err) {
         setError('Failed to fetch source: ' + (err.response?.data?.detail || err.message));
      } finally {
         setLoading(false);
      }
   };

   useEffect(() => {
      fetchSourceDetail();
   }, [sourceId]);

   const handleGoBack = () => {
      navigate(-1);
   };

   const handleAddFeed = async e => {
      e.preventDefault();
      try {
         await api.sources.addFeed(sourceId, newFeed);
         setNewFeed({
            feed_url: '',
            feed_type: 'main',
            description: '',
            is_active: true,
         });
         setIsAddFeedModalOpen(false);
         await fetchSourceDetail();
      } catch (err) {
         alert('Failed to add feed: ' + (err.response?.data?.detail || err.message));
         console.error('Error adding feed:', err);
      }
   };

   const handleDeleteFeed = async feedId => {
      if (window.confirm('Are you sure you want to delete this feed?')) {
         try {
            await api.sources.deleteFeed(feedId);
            await fetchSourceDetail();
         } catch (err) {
            alert('Failed to delete feed: ' + (err.response?.data?.detail || err.message));
         }
      }
   };

   const handleToggleSourceStatus = async () => {
      try {
         await api.sources.update(sourceId, {
            is_active: !source.is_active,
         });
         await fetchSourceDetail();
      } catch (err) {
         alert('Failed to update source status: ' + (err.response?.data?.detail || err.message));
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

   if (loading) {
      return (
         <div className="max-w-4xl mx-auto py-20 text-center">
            <div className="w-16 h-16 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-400">Loading source details...</p>
         </div>
      );
   }

   if (error) {
      return (
         <div className="max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border-l-4 border-red-500 p-4 rounded-sm shadow-sm mb-4 text-red-400">
               {error}
            </div>
            <button
               onClick={handleGoBack}
               className="text-gray-300 hover:text-emerald-300 flex items-center transition-colors duration-200"
            >
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 mr-1"
                  viewBox="0 0 20 20"
                  fill="currentColor"
               >
                  <path
                     fillRule="evenodd"
                     d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                     clipRule="evenodd"
                  />
               </svg>
               Back to sources
            </button>
         </div>
      );
   }

   if (!source) {
      return (
         <div className="max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border-l-4 border-yellow-500 p-4 rounded-sm shadow-sm mb-4 text-yellow-300">
               Source not found
            </div>
            <Link
               to="/sources"
               className="text-gray-300 hover:text-emerald-300 flex items-center transition-colors duration-200"
            >
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 mr-1"
                  viewBox="0 0 20 20"
                  fill="currentColor"
               >
                  <path
                     fillRule="evenodd"
                     d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                     clipRule="evenodd"
                  />
               </svg>
               Back to sources
            </Link>
         </div>
      );
   }

   const sourceCategories =
      source.categories && Array.isArray(source.categories)
         ? source.categories
         : source.category
         ? Array.isArray(source.category)
            ? source.category
            : [source.category]
         : [];

   return (
      <div className="max-w-4xl mx-auto">
         <button
            onClick={handleGoBack}
            className="text-gray-300 hover:text-emerald-300 flex items-center mb-6 transition-colors duration-200 group"
         >
            <svg
               xmlns="http://www.w3.org/2000/svg"
               className="h-5 w-5 mr-1 group-hover:transform group-hover:-translate-x-1 transition-transform duration-200"
               viewBox="0 0 20 20"
               fill="currentColor"
            >
               <path
                  fillRule="evenodd"
                  d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                  clipRule="evenodd"
               />
            </svg>
            Back to sources
         </button>
         <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4">
            <h1 className="text-1xl font-medium text-gray-100 flex items-center">
               <div className="h-10 w-10 mr-3 flex items-center justify-center rounded-full bg-gradient-to-r from-gray-800 to-gray-900 border border-gray-700 text-emerald-400">
                  {source.name.substring(0, 2).toUpperCase()}
               </div>
               {source.name}
               {source.is_active ? (
                  <span className="ml-3 px-2 py-1 text-xs rounded-sm bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border border-emerald-700">
                     Active
                  </span>
               ) : (
                  <span className="ml-3 px-2 py-1 text-xs rounded-sm bg-gradient-to-r from-gray-800 to-gray-900 text-gray-400 border border-gray-700">
                     Inactive
                  </span>
               )}
            </h1>
            <div className="flex mt-4 md:mt-0 space-x-2">
               <button
                  onClick={handleToggleSourceStatus}
                  className={`px-3 py-1.5 text-sm rounded-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 ${
                     source.is_active
                        ? 'bg-gradient-to-r from-gray-700 to-gray-800 text-gray-300 border border-gray-600 hover:bg-gray-700 focus:ring-gray-500'
                        : 'bg-gradient-to-r from-emerald-700 to-emerald-800 text-white border border-emerald-600 hover:from-emerald-600 hover:to-emerald-700 focus:ring-emerald-500'
                  }`}
               >
                  {source.is_active ? 'Deactivate' : 'Activate'}
               </button>
               <Link
                  to={`/sources/${sourceId}/edit`}
                  className="px-3 py-1.5 text-sm rounded-sm bg-gradient-to-r from-blue-700 to-blue-800 text-white border border-blue-600 hover:from-blue-600 hover:to-blue-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900"
               >
                  Edit Source
               </Link>
            </div>
         </div>
         <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-gray-700 mb-6">
            <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
            <div className="p-6">
               <h2 className="text-lg font-medium text-gray-200 mb-4 border-b border-gray-700 pb-2">
                  Source Information
               </h2>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                     <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-400 mb-1">Categories</h3>
                        {sourceCategories && sourceCategories.length > 0 ? (
                           <div className="flex flex-wrap gap-2">
                              {sourceCategories.map((cat, index) => (
                                 <span
                                    key={index}
                                    className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-gradient-to-r from-gray-900 to-gray-800 text-emerald-300 border border-gray-700"
                                 >
                                    {cat}
                                 </span>
                              ))}
                           </div>
                        ) : (
                           <p className="text-gray-500 italic">No categories</p>
                        )}
                     </div>
                     <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-400 mb-1">Website</h3>
                        {source.website || source.url ? (
                           <a
                              href={source.website || source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-emerald-400 hover:text-emerald-300 transition-colors duration-200"
                           >
                              {source.website || source.url}
                           </a>
                        ) : (
                           <p className="text-gray-500 italic">No website</p>
                        )}
                     </div>
                  </div>
                  <div>
                     <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-400 mb-1">Created</h3>
                        <p className="text-gray-300">{formatDate(source.created_at)}</p>
                     </div>
                     <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-400 mb-1">Last Crawled</h3>
                        {source.last_crawled ? (
                           <p className="text-gray-300">{formatDate(source.last_crawled)}</p>
                        ) : (
                           <p className="text-gray-500 italic">Never</p>
                        )}
                     </div>
                  </div>
               </div>
               {source.description && (
                  <div className="mt-2">
                     <h3 className="text-sm font-medium text-gray-400 mb-1">Description</h3>
                     <p className="text-gray-300">{source.description}</p>
                  </div>
               )}
            </div>
         </div>
         <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-gray-700">
            <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
            <div className="p-6">
               <div className="flex justify-between items-center mb-4 border-b border-gray-700 pb-2">
                  <h2 className="text-lg font-medium text-gray-200">Feeds</h2>
                  <button
                     onClick={() => setIsAddFeedModalOpen(true)}
                     className="px-3 py-1.5 text-sm rounded-sm bg-gradient-to-r from-emerald-700 to-emerald-800 text-white border border-emerald-600 hover:from-emerald-600 hover:to-emerald-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 flex items-center"
                  >
                     <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4 mr-1"
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
                     Add Feed
                  </button>
               </div>
               {!source.feeds || source.feeds.length === 0 ? (
                  <div className="text-center py-8">
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
                           strokeWidth={1.5}
                           d="M6 5c7.18 0 13 5.82 13 13M6 11a7 7 0 017 7m-6 0a1 1 0 11-2 0 1 1 0 012 0z"
                        />
                     </svg>
                     <p className="text-gray-400">No feeds found for this source</p>
                     <button
                        onClick={() => setIsAddFeedModalOpen(true)}
                        className="mt-2 text-emerald-400 hover:text-emerald-300 transition-colors duration-200"
                     >
                        Add a new feed
                     </button>
                  </div>
               ) : (
                  <div className="overflow-x-auto">
                     <table className="min-w-full divide-y divide-gray-700">
                        <thead>
                           <tr>
                              <th
                                 scope="col"
                                 className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                              >
                                 URL
                              </th>
                              <th
                                 scope="col"
                                 className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                              >
                                 Type
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
                           {source.feeds.map(feed => (
                              <tr
                                 key={feed.id}
                                 className={`transition-all duration-200 hover:bg-gray-800 ${
                                    !feed.is_active ? 'opacity-60' : ''
                                 }`}
                                 onMouseEnter={() => setHoveredFeed(feed.id)}
                                 onMouseLeave={() => setHoveredFeed(null)}
                              >
                                 <td className="px-6 py-4 text-sm">
                                    <div className="text-gray-300 truncate max-w-xs">
                                       {feed.feed_url}
                                    </div>
                                    {feed.description && (
                                       <div className="text-xs text-gray-500 mt-1 truncate max-w-xs">
                                          {feed.description}
                                       </div>
                                    )}
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="px-2 py-1 inline-flex text-xs leading-5 font-medium rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-emerald-300 border border-gray-700">
                                       {feed.feed_type}
                                    </span>
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap">
                                    {feed.is_active ? (
                                       <span className="px-2 py-1 inline-flex text-xs leading-5 font-medium rounded-sm bg-gradient-to-r from-emerald-900 to-emerald-800 text-emerald-300 border border-emerald-700">
                                          Active
                                       </span>
                                    ) : (
                                       <span className="px-2 py-1 inline-flex text-xs leading-5 font-medium rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-gray-400 border border-gray-700">
                                          Inactive
                                       </span>
                                    )}
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                                    {feed.last_crawled ? formatDate(feed.last_crawled) : 'Never'}
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <div className="flex justify-end space-x-2">
                                       <button
                                          onClick={() => handleDeleteFeed(feed.id)}
                                          className={`text-gray-400 hover:text-red-400 transition-colors duration-200 ${
                                             hoveredFeed === feed.id ? 'text-gray-300' : ''
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
               )}
            </div>
         </div>
         {isAddFeedModalOpen && (
            <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50">
               <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-sm max-w-md w-full p-6 shadow-2xl border border-gray-700 relative">
                  <button
                     onClick={() => setIsAddFeedModalOpen(false)}
                     className="absolute top-3 right-3 text-gray-400 hover:text-gray-200 transition-colors duration-200"
                  >
                     <svg
                        xmlns="http://www.w3.org/2000/svg"
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
                  </button>
                  <h2 className="text-xl font-medium text-gray-200 mb-4">Add New Feed</h2>
                  <form onSubmit={handleAddFeed}>
                     <div className="mb-4">
                        <label
                           htmlFor="feed_url"
                           className="block text-sm font-medium text-gray-300 mb-1"
                        >
                           Feed URL <span className="text-red-400">*</span>
                        </label>
                        <input
                           id="feed_url"
                           type="text"
                           required
                           value={newFeed.feed_url}
                           onChange={e => setNewFeed({ ...newFeed, feed_url: e.target.value })}
                           placeholder="https://example.com/feed.rss"
                           className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                        />
                     </div>
                     <div className="mb-4">
                        <label
                           htmlFor="feed_type"
                           className="block text-sm font-medium text-gray-300 mb-1"
                        >
                           Feed Type
                        </label>
                        <select
                           id="feed_type"
                           value={newFeed.feed_type}
                           onChange={e => setNewFeed({ ...newFeed, feed_type: e.target.value })}
                           className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                        >
                           <option value="main">Main</option>
                           <option value="alternate">Alternate</option>
                           <option value="category">Category</option>
                           <option value="tag">Tag</option>
                        </select>
                     </div>
                     <div className="mb-4">
                        <label
                           htmlFor="description"
                           className="block text-sm font-medium text-gray-300 mb-1"
                        >
                           Description
                        </label>
                        <textarea
                           id="description"
                           value={newFeed.description}
                           onChange={e => setNewFeed({ ...newFeed, description: e.target.value })}
                           rows="3"
                           placeholder="Feed description (optional)"
                           className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                        ></textarea>
                     </div>
                     <div className="mb-4 flex items-center">
                        <input
                           id="is_active"
                           type="checkbox"
                           checked={newFeed.is_active}
                           onChange={e => setNewFeed({ ...newFeed, is_active: e.target.checked })}
                           className="h-4 w-4 text-emerald-600 bg-gray-900 border-gray-700 rounded focus:ring-emerald-500 focus:ring-offset-gray-900"
                        />
                        <label htmlFor="is_active" className="ml-2 block text-sm text-gray-300">
                           Active
                        </label>
                     </div>
                     <div className="mt-6 flex justify-end space-x-3">
                        <button
                           type="button"
                           onClick={() => setIsAddFeedModalOpen(false)}
                           className="px-4 py-2 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-gray-300 rounded-sm focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-sm transition-colors duration-200"
                        >
                           Cancel
                        </button>
                        <button
                           type="submit"
                           className="px-4 py-2 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-sm transition-colors duration-200"
                        >
                           Add Feed
                        </button>
                     </div>
                  </form>
               </div>
            </div>
         )}
      </div>
   );
};

export default SourceDetail;
