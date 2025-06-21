import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';

const SocialMediaDetail = () => {
   const { postId } = useParams();
   const [post, setPost] = useState(null);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [relatedPosts, setRelatedPosts] = useState([]);

   useEffect(() => {
      if (postId) {
         fetchPost();
      }
   }, [postId]);

   const fetchPost = async () => {
      try {
         setLoading(true);
         setError(null);
         const response = await api.socialMedia.getById(postId);
         setPost(response.data);
         if (response.data?.author_name) {
            fetchRelatedPosts(response.data.author_name, response.data.platform);
         }
      } catch (error) {
         console.error('Error fetching post:', error);
         setError('Failed to load social media post');
      } finally {
         setLoading(false);
      }
   };

   const fetchRelatedPosts = async (authorName, platform) => {
      try {
         const response = await api.socialMedia.getAll({
            author: authorName,
            platform: platform,
            per_page: 5,
         });
         const filteredPosts = response.data.items.filter(item => item.id !== parseInt(postId));
         setRelatedPosts(filteredPosts.slice(0, 4));
      } catch (error) {
         console.error('Error fetching related posts:', error);
      }
   };

   const formatDate = dateStr => {
      if (!dateStr) return 'N/A';
      try {
         const date = new Date(dateStr);
         return (
            date.toLocaleDateString() +
            ' ' +
            date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
         );
      } catch (e) {
         return 'Invalid Date';
      }
   };

   const getPlatformIcon = platform => {
      if (platform === 'x') {
         return (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
               <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
         );
      } else if (platform === 'facebook') {
         return (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
               <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
            </svg>
         );
      } else {
         return (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
               <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
            </svg>
         );
      }
   };

   return (
      <div className="max-w-4xl mx-auto">
         <div className="mb-6">
            <div className="flex items-center mb-2">
               <Link
                  to="/social-media"
                  className="mr-3 flex items-center text-gray-400 hover:text-emerald-400 transition-colors"
               >
                  <svg
                     className="w-5 h-5 mr-1"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 19l-7-7m0 0l7-7m-7 7h18"
                     />
                  </svg>
                  Back
               </Link>
               <div className="h-10 w-10 text-emerald-500 mr-4 relative">
                  <svg viewBox="0 0 24 24" fill="none" className="absolute">
                     <path
                        d="M2 9.5V4C2 2.89543 2.89543 2 4 2H20C21.1046 2 22 2.89543 22 4V9.5"
                        stroke="currentColor"
                        strokeWidth="1.5"
                     />
                     <path
                        d="M2 14.5V20C2 21.1046 2.89543 22 4 22H20C21.1046 22 22 21.1046 22 20V14.5"
                        stroke="currentColor"
                        strokeWidth="1.5"
                     />
                     <path d="M2 12H22" stroke="currentColor" strokeWidth="1.5" />
                     <path
                        d="M10 6H17"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                     <path
                        d="M7 6H8"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                     <path
                        d="M7 18H17"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                  </svg>
                  <div className="absolute inset-0 bg-emerald-500 opacity-30 blur-md rounded-full"></div>
               </div>
               <h1 className="text-2xl font-medium text-gray-100 relative">
                  Social Media Post
                  <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-500 to-transparent mt-1 opacity-60"></div>
               </h1>
            </div>
         </div>
         {loading ? (
            <div className="flex justify-center py-10">
               <div className="animate-spin w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full"></div>
            </div>
         ) : error ? (
            <div className="bg-red-900/30 border border-red-800 text-red-200 px-4 py-3 rounded-md">
               {error}
            </div>
         ) : post ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
               <div className="md:col-span-2 space-y-4">
                  <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md overflow-hidden">
                     <div className="p-4">
                        <div className="flex items-start mb-3">
                           <div className="mr-3">
                              <div className="flex items-center justify-center w-12 h-12 bg-gray-700/50 rounded-full border border-gray-600">
                                 {post.platform === 'facebook' ? (
                                    <div className="text-blue-500">
                                       {getPlatformIcon('facebook')}
                                    </div>
                                 ) : post.platform === 'x' ? (
                                    <div className="text-blue-400">{getPlatformIcon('x')}</div>
                                 ) : (
                                    <div className="text-gray-400">{getPlatformIcon('other')}</div>
                                 )}
                              </div>
                           </div>
                           <div>
                              <div className="flex items-center flex-wrap gap-2">
                                 <h2 className="text-lg font-semibold text-white">
                                    {post.author_name}
                                 </h2>
                                 {post.author_handle && (
                                    <span className="text-gray-400">@{post.author_handle}</span>
                                 )}
                                 {post.author_is_verified && (
                                    <span className="bg-blue-500/20 text-blue-300 text-xs px-1.5 py-0.5 rounded-md">
                                       Verified
                                    </span>
                                 )}
                              </div>
                              <div className="text-gray-400 text-sm">
                                 {formatDate(post.post_datetime)}
                              </div>
                           </div>

                           <div className="ml-auto">
                              <div
                                 className={`px-2 py-1 rounded-md text-xs font-medium ${
                                    post.platform === 'facebook'
                                       ? 'bg-blue-900/30 text-blue-300 border border-blue-800/30'
                                       : post.platform === 'x'
                                       ? 'bg-blue-500/20 text-blue-400 border border-blue-600/30'
                                       : 'bg-gray-800 text-gray-300 border border-gray-700'
                                 }`}
                              >
                                 {post.platform === 'x' ? 'X (Twitter)' : post.platform}
                              </div>
                           </div>
                        </div>

                        <div className="text-gray-200 text-lg mb-4">{post.message}</div>

                        {post.has_image && post.image_url && (
                           <div className="mb-4 rounded-md overflow-hidden border border-gray-700">
                              <img
                                 src={post.image_url}
                                 alt="Post"
                                 className="w-full h-auto max-h-96 object-contain bg-gray-900"
                                 onError={e => {
                                    e.target.onerror = null;
                                    e.target.src =
                                       'https://via.placeholder.com/800x400?text=Image+Not+Available';
                                 }}
                              />
                           </div>
                        )}
                        <div className="border-t border-gray-700 pt-3 mt-4">
                           <div className="flex flex-wrap gap-3 text-sm">
                              {post.likes_count > 0 && (
                                 <div className="px-3 py-1.5 bg-gray-800/50 text-gray-300 rounded-md flex items-center">
                                    <svg
                                       className="w-4 h-4 mr-2 text-red-400"
                                       fill="none"
                                       viewBox="0 0 24 24"
                                       stroke="currentColor"
                                    >
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth="2"
                                          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                                       />
                                    </svg>
                                    {post.likes_count} Likes
                                 </div>
                              )}
                              {post.comments_count > 0 && (
                                 <div className="px-3 py-1.5 bg-gray-800/50 text-gray-300 rounded-md flex items-center">
                                    <svg
                                       className="w-4 h-4 mr-2 text-blue-400"
                                       fill="none"
                                       viewBox="0 0 24 24"
                                       stroke="currentColor"
                                    >
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth="2"
                                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                                       />
                                    </svg>
                                    {post.comments_count} Comments
                                 </div>
                              )}
                              {post.shares_count > 0 && (
                                 <div className="px-3 py-1.5 bg-gray-800/50 text-gray-300 rounded-md flex items-center">
                                    <svg
                                       className="w-4 h-4 mr-2 text-green-400"
                                       fill="none"
                                       viewBox="0 0 24 24"
                                       stroke="currentColor"
                                    >
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth="2"
                                          d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                                       />
                                    </svg>
                                    {post.shares_count} Shares
                                 </div>
                              )}
                              {post.reactions_count > 0 && post.platform === 'facebook' && (
                                 <div className="px-3 py-1.5 bg-gray-800/50 text-gray-300 rounded-md flex items-center">
                                    <svg
                                       className="w-4 h-4 mr-2 text-yellow-400"
                                       fill="none"
                                       viewBox="0 0 24 24"
                                       stroke="currentColor"
                                    >
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth="2"
                                          d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                       />
                                    </svg>
                                    {post.reactions_count} Reactions
                                 </div>
                              )}
                              {post.views_count > 0 && (
                                 <div className="px-3 py-1.5 bg-gray-800/50 text-gray-300 rounded-md flex items-center">
                                    <svg
                                       className="w-4 h-4 mr-2 text-purple-400"
                                       fill="none"
                                       viewBox="0 0 24 24"
                                       stroke="currentColor"
                                    >
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth="2"
                                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                       />
                                       <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth="2"
                                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                                       />
                                    </svg>
                                    {post.views_count} Views
                                 </div>
                              )}
                           </div>
                        </div>
                     </div>
                     {post.post_url && (
                        <div className="border-t border-gray-700 px-4 py-3 bg-gray-900/30">
                           <a
                              href={post.post_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-emerald-400 hover:text-emerald-300 flex items-center transition-colors font-medium"
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
                                    strokeWidth="2"
                                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                 />
                              </svg>
                              View Original Post
                           </a>
                        </div>
                     )}
                  </div>
                  {post.extra_data && Object.keys(post.extra_data).length > 0 && (
                     <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md p-4">
                        <h3 className="text-lg font-semibold text-white mb-3">Additional Data</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                           {Object.entries(post.extra_data).map(([key, value]) => {
                              if (value === null || value === undefined || value === '')
                                 return null;
                              if (typeof value === 'object') return null;
                              return (
                                 <div
                                    key={key}
                                    className="bg-gray-800/50 border border-gray-700/50 rounded p-2"
                                 >
                                    <div className="text-gray-400 text-xs mb-1">
                                       {key
                                          .replace(/_/g, ' ')
                                          .replace(/\b\w/g, l => l.toUpperCase())}
                                    </div>
                                    <div className="text-gray-200">{String(value)}</div>
                                 </div>
                              );
                           })}
                        </div>
                     </div>
                  )}
               </div>
               <div className="space-y-4">
                  <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md p-4">
                     <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                        <svg
                           className="w-5 h-5 mr-2 text-emerald-400"
                           fill="none"
                           viewBox="0 0 24 24"
                           stroke="currentColor"
                        >
                           <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                           />
                        </svg>
                        Post Information
                     </h3>
                     <div className="space-y-2">
                        <div className="flex justify-between py-2 border-b border-gray-700">
                           <span className="text-gray-400">Platform</span>
                           <span className="text-white font-medium capitalize">
                              {post.platform}
                           </span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-gray-700">
                           <span className="text-gray-400">Date Posted</span>
                           <span className="text-white font-medium">
                              {formatDate(post.post_datetime)}
                           </span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-gray-700">
                           <span className="text-gray-400">First Seen</span>
                           <span className="text-white font-medium">
                              {formatDate(post.first_seen_timestamp)}
                           </span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-gray-700">
                           <span className="text-gray-400">Last Updated</span>
                           <span className="text-white font-medium">
                              {formatDate(post.last_updated_timestamp)}
                           </span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-gray-700">
                           <span className="text-gray-400">Total Engagement</span>
                           <span className="text-white font-medium">
                              {post.total_engagement ||
                                 post.comments_count +
                                    post.reactions_count +
                                    post.shares_count +
                                    post.reposts_count +
                                    post.likes_count +
                                    post.bookmarks_count}
                           </span>
                        </div>
                        <div className="flex justify-between py-2">
                           <span className="text-gray-400">Post ID</span>
                           <span className="text-white font-medium">{post.post_id}</span>
                        </div>
                     </div>
                  </div>
                  {relatedPosts.length > 0 && (
                     <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-md p-4">
                        <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                           <svg
                              className="w-5 h-5 mr-2 text-emerald-400"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                           >
                              <path
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                                 strokeWidth="2"
                                 d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                              />
                           </svg>
                           More from This Author
                        </h3>
                        <div className="space-y-3">
                           {relatedPosts.map(relatedPost => (
                              <Link
                                 key={relatedPost.id}
                                 to={`/social-media/${relatedPost.id}`}
                                 className="block bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700 hover:border-gray-600 rounded-md p-3 transition-all duration-200"
                              >
                                 <p className="text-gray-200 text-sm mb-1 line-clamp-2">
                                    {relatedPost.message}
                                 </p>
                                 <div className="flex justify-between items-center text-xs">
                                    <span className="text-gray-400">
                                       {formatDate(relatedPost.post_datetime)}
                                    </span>
                                    <div className="flex items-center space-x-2">
                                       {relatedPost.comments_count > 0 && (
                                          <span className="text-gray-400 flex items-center">
                                             <svg
                                                className="w-3 h-3 mr-1"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                             >
                                                <path
                                                   strokeLinecap="round"
                                                   strokeLinejoin="round"
                                                   strokeWidth="2"
                                                   d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                                                />
                                             </svg>
                                             {relatedPost.comments_count}
                                          </span>
                                       )}
                                       {relatedPost.likes_count > 0 && (
                                          <span className="text-gray-400 flex items-center">
                                             <svg
                                                className="w-3 h-3 mr-1"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                             >
                                                <path
                                                   strokeLinecap="round"
                                                   strokeLinejoin="round"
                                                   strokeWidth="2"
                                                   d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                                                />
                                             </svg>
                                             {relatedPost.likes_count}
                                          </span>
                                       )}
                                    </div>
                                 </div>
                              </Link>
                           ))}
                        </div>
                        <div className="mt-3 pt-3 border-t border-gray-700">
                           <Link
                              to={`/social-media?author=${encodeURIComponent(post.author_name)}`}
                              className="text-emerald-400 hover:text-emerald-300 text-sm flex items-center justify-center transition-colors"
                           >
                              View all posts by {post.author_name}
                              <svg
                                 className="w-4 h-4 ml-1"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                              >
                                 <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="M9 5l7 7-7 7"
                                 />
                              </svg>
                           </Link>
                        </div>
                     </div>
                  )}
               </div>
            </div>
         ) : (
            <div className="bg-gray-800/50 border border-gray-700 rounded-md p-6 text-center">
               <div className="w-16 h-16 mx-auto mb-4 bg-gray-700/50 rounded-full flex items-center justify-center">
                  <svg
                     className="w-8 h-8 text-gray-400"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="1.5"
                        d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                     />
                  </svg>
               </div>
               <h3 className="text-xl font-semibold text-gray-300 mb-2">Post not found</h3>
               <p className="text-gray-400 mb-4">
                  The post you're looking for doesn't exist or has been removed.
               </p>
               <Link
                  to="/social-media"
                  className="inline-flex items-center px-4 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-md transition-colors"
               >
                  <svg
                     className="w-5 h-5 mr-2"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M10 19l-7-7m0 0l7-7m-7 7h18"
                     />
                  </svg>
                  Back to Social Media
               </Link>
            </div>
         )}
      </div>
   );
};

export default SocialMediaDetail;
