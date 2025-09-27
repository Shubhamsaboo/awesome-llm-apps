import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';

const SourceEdit = () => {
   const { sourceId } = useParams();
   const navigate = useNavigate();
   const location = useLocation();
   const isNewSource = location.pathname === '/sources/new';
   const [loading, setLoading] = useState(!isNewSource);
   const [error, setError] = useState(null);
   const [categories, setCategories] = useState([]);
   const [source, setSource] = useState({
      name: '',
      url: '',
      categories: [],
      description: '',
      is_active: true,
      feeds: [],
   });
   const [newCategory, setNewCategory] = useState('');
   const [customCategory, setCustomCategory] = useState('');
   const [showCustomInput, setShowCustomInput] = useState(false);

   useEffect(() => {
      const fetchCategories = async () => {
         try {
            const response = await api.sources.getCategories();
            setCategories(response.data || []);
         } catch (err) {
            console.error('Error fetching categories:', err);
            setError('Failed to load categories. Please try again later.');
         }
      };
      fetchCategories();
   }, []);

   useEffect(() => {
      if (!isNewSource && sourceId) {
         const fetchSourceData = async () => {
            setLoading(true);
            setError(null);
            try {
               const response = await api.sources.getById(sourceId);
               const sourceData = response.data;
               if (sourceData.website && !sourceData.url) {
                  sourceData.url = sourceData.website;
               }
               if (!sourceData.categories) {
                  sourceData.categories = sourceData.category
                     ? Array.isArray(sourceData.category)
                        ? sourceData.category
                        : [sourceData.category]
                     : [];
               } else if (!Array.isArray(sourceData.categories)) {
                  sourceData.categories = [sourceData.categories];
               }
               setSource(sourceData);
            } catch (err) {
               setError('Failed to fetch source: ' + (err.response?.data?.detail || err.message));
               console.error('Error fetching source:', err);
            } finally {
               setLoading(false);
            }
         };
         fetchSourceData();
      }
   }, [sourceId, isNewSource]);

   const handleInputChange = e => {
      const { name, value, type, checked } = e.target;
      setSource({
         ...source,
         [name]: type === 'checkbox' ? checked : value,
      });
   };

   const handleAddCategory = () => {
      if (showCustomInput && customCategory.trim()) {
         if (!source.categories.includes(customCategory.trim())) {
            setSource({
               ...source,
               categories: [...source.categories, customCategory.trim()],
            });
         }
         setCustomCategory('');
         setShowCustomInput(false);
      } else if (newCategory && !showCustomInput) {
         if (!source.categories.includes(newCategory)) {
            setSource({
               ...source,
               categories: [...source.categories, newCategory],
            });
         }
         setNewCategory('');
      }
   };

   const handleRemoveCategory = category => {
      setSource({
         ...source,
         categories: source.categories.filter(c => c !== category),
      });
   };

   const handleSubmit = async e => {
      e.preventDefault();
      setLoading(true);
      setError(null);
      try {
         let response;

         if (isNewSource) {
            response = await api.sources.create(source);
            navigate(`/sources/${response.data.id}`);
         } else {
            response = await api.sources.update(sourceId, source);
            navigate(`/sources/${sourceId}`, { replace: true });
         }
      } catch (err) {
         setError('Failed to save source: ' + (err.response?.data?.detail || err.message));
         console.error('Error saving source:', err);
         setLoading(false);
      }
   };

   const handleCancel = () => {
      if (isNewSource) {
         navigate('/sources');
      } else {
         navigate(-1);
      }
   };

   const handleCategoryChange = e => {
      const value = e.target.value;
      if (value === 'new') {
         setShowCustomInput(true);
         setNewCategory('');
      } else {
         setNewCategory(value);
         setShowCustomInput(false);
      }
   };

   if (loading && !isNewSource) {
      return (
         <div className="max-w-4xl mx-auto py-20 text-center">
            <div className="w-16 h-16 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-400">Loading source data...</p>
         </div>
      );
   }

   return (
      <div className="max-w-4xl mx-auto">
         <h1 className="text-2xl font-medium text-gray-100 mb-6">
            {isNewSource ? 'Create New Source' : 'Edit Source'}
         </h1>
         {error && (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border-l-4 border-red-500 p-4 rounded-sm shadow-sm mb-6 text-red-400">
               {error}
            </div>
         )}
         <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-gray-700">
            <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
            <form onSubmit={handleSubmit} className="p-6">
               <div className="grid grid-cols-1 gap-6">
                  <div>
                     <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
                        Name <span className="text-red-400">*</span>
                     </label>
                     <input
                        type="text"
                        id="name"
                        name="name"
                        required
                        value={source.name}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                        placeholder="Source name"
                     />
                  </div>
                  <div>
                     <label htmlFor="url" className="block text-sm font-medium text-gray-300 mb-1">
                        Website URL
                     </label>
                     <input
                        type="url"
                        id="url"
                        name="url"
                        value={source.url || ''}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                        placeholder="https://example.com"
                     />
                  </div>
                  <div>
                     <label className="block text-sm font-medium text-gray-300 mb-1">
                        Categories
                     </label>
                     <div className="flex flex-wrap gap-2 mb-2">
                        {source.categories &&
                           source.categories.map((category, index) => (
                              <div
                                 key={index}
                                 className="flex items-center px-2 py-1 bg-gradient-to-r from-gray-900 to-gray-800 text-gray-300 rounded-sm border border-gray-700"
                              >
                                 <span className="text-sm">{category}</span>
                                 <button
                                    type="button"
                                    onClick={() => handleRemoveCategory(category)}
                                    className="ml-1.5 text-gray-500 hover:text-red-400 transition-colors duration-200"
                                 >
                                    <svg
                                       xmlns="http://www.w3.org/2000/svg"
                                       className="h-4 w-4"
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
                              </div>
                           ))}
                     </div>
                     <div className="space-y-2">
                        <div className="flex">
                           <select
                              value={newCategory}
                              onChange={handleCategoryChange}
                              className="flex-1 px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-l-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                           >
                              <option value="">-- Select Category --</option>
                              {categories.map(category => (
                                 <option
                                    key={category.id}
                                    value={category.name}
                                    disabled={source.categories.includes(category.name)}
                                 >
                                    {category.name}{' '}
                                    {source.categories.includes(category.name) ? '(Added)' : ''}
                                 </option>
                              ))}
                              <option value="new">➕ Create new category</option>
                           </select>
                           <button
                              type="button"
                              onClick={handleAddCategory}
                              disabled={
                                 (!newCategory && !showCustomInput) ||
                                 (showCustomInput && !customCategory)
                              }
                              className="px-3 py-2 bg-gradient-to-r from-emerald-700 to-emerald-800 text-white rounded-r-sm border border-emerald-600 hover:from-emerald-600 hover:to-emerald-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                           >
                              Add
                           </button>
                        </div>
                        {showCustomInput && (
                           <div className="flex mt-2">
                              <input
                                 type="text"
                                 value={customCategory}
                                 onChange={e => setCustomCategory(e.target.value)}
                                 placeholder="Enter new category name"
                                 className="flex-1 px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                              />
                           </div>
                        )}
                     </div>
                     <p className="text-xs text-gray-500 mt-2">
                        You can select multiple categories for this source or create new ones.
                     </p>
                  </div>
                  <div>
                     <label
                        htmlFor="description"
                        className="block text-sm font-medium text-gray-300 mb-1"
                     >
                        Description
                     </label>
                     <textarea
                        id="description"
                        name="description"
                        value={source.description || ''}
                        onChange={handleInputChange}
                        rows="4"
                        className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                        placeholder="Brief description of the source"
                     ></textarea>
                  </div>
                  <div className="flex items-center">
                     <input
                        id="is_active"
                        name="is_active"
                        type="checkbox"
                        checked={source.is_active}
                        onChange={handleInputChange}
                        className="h-4 w-4 text-emerald-600 bg-gray-900 border-gray-700 rounded focus:ring-emerald-500 focus:ring-offset-gray-900"
                     />
                     <label htmlFor="is_active" className="ml-2 block text-sm text-gray-300">
                        Active
                     </label>
                  </div>
                  {isNewSource && (
                     <div className="border-t border-gray-700 pt-4 mt-2">
                        <h3 className="text-lg font-medium text-gray-200 mb-3">Initial Feed</h3>
                        <p className="text-sm text-gray-400 mb-4">
                           You can add a feed URL to start collecting content from this source. More
                           feeds can be added later.
                        </p>
                        <div>
                           <label
                              htmlFor="feed_url"
                              className="block text-sm font-medium text-gray-300 mb-1"
                           >
                              Feed URL
                           </label>
                           <input
                              type="url"
                              id="feed_url"
                              name="feed_url"
                              value={source.feeds[0]?.feed_url || ''}
                              onChange={e => {
                                 const updatedFeeds =
                                    source.feeds.length > 0
                                       ? source.feeds.map((feed, idx) =>
                                            idx === 0 ? { ...feed, feed_url: e.target.value } : feed
                                         )
                                       : [
                                            {
                                               feed_url: e.target.value,
                                               feed_type: 'main',
                                               is_active: true,
                                            },
                                         ];

                                 setSource({
                                    ...source,
                                    feeds: updatedFeeds,
                                 });
                              }}
                              className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                              placeholder="https://example.com/feed.rss"
                           />
                        </div>
                     </div>
                  )}
                  <div className="flex justify-end space-x-3 mt-4">
                     <button
                        type="button"
                        onClick={handleCancel}
                        className="px-4 py-2 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-gray-300 rounded-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-sm transition-colors duration-200"
                     >
                        Cancel
                     </button>
                     <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-sm transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                     >
                        {loading && (
                           <svg
                              className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                        )}
                        {isNewSource ? 'Create Source' : 'Save Changes'}
                     </button>
                  </div>
               </div>
            </form>
         </div>
      </div>
   );
};

export default SourceEdit;
