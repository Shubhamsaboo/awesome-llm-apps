import React, { useState, useEffect } from 'react';
import api from '../services/api';
import FeedTab from '../components/social/FeedTab';
import StatsTab from '../components/social/StatsTab';
import SessionSetupTab from '../components/social/SessionSetupTab';
import PostDetailPanel from '../components/social/PostDetailPanel';
import { ShieldCheck, Key } from 'lucide-react';

const SocialMedia = () => {
   const [posts, setPosts] = useState([]);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [stats, setStats] = useState(null);
   const [platforms, setPlatforms] = useState([]);
   const [sentiments, setSentiments] = useState([]);
   const [categories, setCategories] = useState([]);
   const [activeTab, setActiveTab] = useState('feed');
   const [filters, setFilters] = useState({
      platform: '',
      sentiment: 'positive',
      category: '',
      dateFrom: '',
      dateTo: '',
      search: '',
   });
   const [pagination, setPagination] = useState({
      page: 1,
      perPage: 10,
      totalPages: 1,
      total: 0,
   });
   const [isFilterOpen, setIsFilterOpen] = useState(false);
   const [selectedPost, setSelectedPost] = useState(null);
   const [isDetailPanelOpen, setIsDetailPanelOpen] = useState(false);

   useEffect(() => {
      fetchPosts();
      fetchPlatforms();
      fetchSentiments();
      fetchCategories();
   }, []);
   useEffect(() => {
      fetchPosts();
   }, [pagination.page, filters]);

   const fetchPosts = async () => {
      try {
         setLoading(true);
         const response = await api.socialMedia.getAll({
            page: pagination.page,
            per_page: pagination.perPage,
            platform: filters.platform || undefined,
            sentiment: filters.sentiment || undefined,
            category: filters.category || undefined,
            date_from: filters.dateFrom || undefined,
            date_to: filters.dateTo || undefined,
            search: filters.search || undefined,
         });
         setPosts(response.data.items || []);
         setPagination({
            page: response.data.page || 1,
            perPage: response.data.per_page || 10,
            totalPages: response.data.total_pages || 1,
            total: response.data.total || 0,
         });
      } catch (error) {
         console.error('Error fetching social media posts:', error);
         setError('Failed to load social media posts');
      } finally {
         setLoading(false);
      }
   };
   const fetchPlatforms = async () => {
      try {
         const response = await api.socialMedia.getPlatforms();
         setPlatforms(response.data || []);
      } catch (error) {
         console.error('Error fetching platforms:', error);
      }
   };
   const fetchSentiments = async () => {
      try {
         const response = await api.socialMedia.getSentiments();
         setSentiments(response.data || []);
         const sentimentData = response.data || [];
         const statsData = {
            sentiments: sentimentData.reduce((acc, item) => {
               acc[item.sentiment] = item.post_count;
               return acc;
            }, {}),
         };
         setStats(statsData);
      } catch (error) {
         console.error('Error fetching sentiments:', error);
      }
   };
   const fetchCategories = async () => {
      try {
         const response = await api.socialMedia.getCategories();
         setCategories(response.data || []);
      } catch (error) {
         console.error('Error fetching categories:', error);
      }
   };
   const resetFilters = () => {
      setFilters({
         platform: '',
         sentiment: '',
         category: '',
         dateFrom: '',
         dateTo: '',
         search: '',
      });
      setPagination(prev => ({ ...prev, page: 1 }));
   };
   const handleFilterChange = (name, value) => {
      setFilters(prev => ({
         ...prev,
         [name]: value,
      }));
      setPagination(prev => ({ ...prev, page: 1 }));
   };
   const handlePrevPage = () => {
      if (pagination.page > 1) {
         setPagination(prev => ({ ...prev, page: prev.page - 1 }));
      }
   };
   const handleNextPage = () => {
      if (pagination.page < pagination.totalPages) {
         setPagination(prev => ({ ...prev, page: prev.page + 1 }));
      }
   };
   const handleTabChange = tab => {
      setActiveTab(tab);
   };
   const handlePostClick = post => {
      setSelectedPost(post);
      setIsDetailPanelOpen(true);
      const url = new URL(window.location);
      url.searchParams.set('postId', post.post_id);
      window.history.pushState({}, '', url);
   };

   const handleCloseDetailPanel = () => {
      setIsDetailPanelOpen(false);
      const url = new URL(window.location);
      url.searchParams.delete('postId');
      window.history.pushState({}, '', url);
   };

   useEffect(() => {
      const url = new URL(window.location);
      const postId = url.searchParams.get('postId');
      if (postId) {
         const loadPostFromUrl = async () => {
            try {
               const response = await api.socialMedia.getById(postId);
               setSelectedPost(response.data);
               setIsDetailPanelOpen(true);
            } catch (error) {
               console.error('Error loading post from URL:', error);
               url.searchParams.delete('postId');
               window.history.pushState({}, '', url);
            }
         };
         loadPostFromUrl();
      }
   }, []);
   useEffect(() => {
      const handlePopState = event => {
         const url = new URL(window.location);
         const postId = url.searchParams.get('postId');
         if (postId) {
            if (!selectedPost || selectedPost.post_id !== postId) {
               const loadPostFromUrl = async () => {
                  try {
                     const response = await api.socialMedia.getById(postId);
                     setSelectedPost(response.data);
                     setIsDetailPanelOpen(true);
                  } catch (error) {
                     console.error('Error loading post from URL:', error);
                  }
               };
               loadPostFromUrl();
            } else {
               setIsDetailPanelOpen(true);
            }
         } else {
            setIsDetailPanelOpen(false);
         }
      };
      window.addEventListener('popstate', handlePopState);
      return () => window.removeEventListener('popstate', handlePopState);
   }, [selectedPost]);

   return (
      <div className="max-w-7xl mx-auto">
         <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 relative">
            <div className="relative mb-4 md:mb-0">
               <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-10 h-10">
                  <div className="relative w-10 h-10">
                     <ShieldCheck className="text-emerald-500 w-10 h-10 relative z-10" />
                     <div className="absolute inset-0 bg-emerald-500 opacity-30 blur-md rounded-full"></div>
                  </div>
               </div>
               <h1 className="text-2xl font-medium text-gray-100 ml-14">Your Social</h1>
            </div>
            {activeTab !== 'stats' && activeTab !== 'setup' && (
               <div className="flex items-center space-x-2">
                  <div className="relative flex-grow">
                     <input
                        type="text"
                        value={filters.search}
                        onChange={e => handleFilterChange('search', e.target.value)}
                        placeholder="Search posts..."
                        className="w-full pl-10 pr-4 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-md focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 text-gray-300 transition-all"
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
                     className="flex items-center justify-center p-2 bg-gradient-to-r from-gray-800 to-gray-900 border border-gray-700 rounded-sm shadow-md hover:border-gray-600 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-colors duration-200"
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
            )}
         </div>
         <div className="mb-6">
            <div className="border-b border-gray-700">
               <nav className="flex -mb-px space-x-6">
                  <button
                     onClick={() => handleTabChange('feed')}
                     className={`py-2.5 px-1 inline-flex items-center whitespace-nowrap font-medium text-sm border-b-2 ${
                        activeTab === 'feed'
                           ? 'border-emerald-500 text-emerald-400'
                           : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-700'
                     } transition-colors duration-200`}
                  >
                     <svg
                        className="w-4 h-4 mr-2"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                     >
                        <path
                           strokeLinecap="round"
                           strokeLinejoin="round"
                           strokeWidth="1.5"
                           d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
                        />
                     </svg>
                     Feed
                  </button>
                  <button
                     onClick={() => handleTabChange('stats')}
                     className={`py-2.5 px-1 inline-flex items-center whitespace-nowrap font-medium text-sm border-b-2 ${
                        activeTab === 'stats'
                           ? 'border-emerald-500 text-emerald-400'
                           : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-700'
                     } transition-colors duration-200`}
                  >
                     <svg
                        className="w-4 h-4 mr-2"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                     >
                        <path
                           strokeLinecap="round"
                           strokeLinejoin="round"
                           strokeWidth="1.5"
                           d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        />
                     </svg>
                     Insights
                  </button>
                  <button
                     onClick={() => handleTabChange('setup')}
                     className={`py-2.5 px-1 inline-flex items-center whitespace-nowrap font-medium text-sm border-b-2 ${
                        activeTab === 'setup'
                           ? 'border-emerald-500 text-emerald-400'
                           : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-700'
                     } transition-colors duration-200`}
                  >
                     <Key className="w-4 h-4 mr-2" />
                     Setup
                  </button>
               </nav>
            </div>
         </div>
         {activeTab === 'feed' && (
            <FeedTab
               posts={posts}
               loading={loading}
               error={error}
               filters={filters}
               pagination={pagination}
               isFilterOpen={isFilterOpen}
               platforms={platforms}
               sentiments={sentiments.map(item => item.sentiment)}
               categories={categories.map(item => item.category)}
               handleFilterChange={handleFilterChange}
               resetFilters={resetFilters}
               handlePrevPage={handlePrevPage}
               handleNextPage={handleNextPage}
               setIsFilterOpen={setIsFilterOpen}
               setPagination={setPagination}
               onPostClick={handlePostClick}
            />
         )}
         {activeTab === 'stats' && (
            <StatsTab
               platforms={platforms}
               sentiments={sentiments}
               categories={categories}
               stats={stats}
               onPostClick={handlePostClick}
            />
         )}
         {activeTab === 'setup' && <SessionSetupTab />}
         <PostDetailPanel
            post={selectedPost}
            isOpen={isDetailPanelOpen}
            onClose={handleCloseDetailPanel}
         />
      </div>
   );
};

export default SocialMedia;
