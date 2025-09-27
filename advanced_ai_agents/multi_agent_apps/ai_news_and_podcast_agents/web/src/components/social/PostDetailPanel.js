import React, { useEffect } from 'react';
import {
   X,
   MessageCircle,
   Heart,
   Share2,
   ExternalLink,
   Smile,
   Frown,
   AlertCircle,
   Minus,
   Calendar,
   Clock,
   Facebook,
} from 'lucide-react';
import api from '../../services/api';

const formatDate = dateStr => {
   if (!dateStr) return 'N/A';
   try {
      const date = new Date(dateStr);
      return date.toLocaleDateString();
   } catch (e) {
      return 'Invalid Date';
   }
};
const formatNumber = number => {
   if (!number || isNaN(number)) return '0';
   if (number >= 1000000) return (number / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
   if (number >= 10000) return Math.floor(number / 1000) + 'k';
   if (number >= 1000) return (number / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
   return number.toString();
};
const getPlatformIcon = platform => {
   switch (platform?.toLowerCase()) {
      case 'x.com':
      case 'x':
         return (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
               <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
         );
      case 'facebook.com':
         return <Facebook className="w-5 h-5 text-blue-600" />;
      case 'instagram':
         return (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
               <path d="M12 2c2.717 0 3.056.01 4.122.06 1.065.05 1.79.217 2.428.465.66.254 1.216.598 1.772 1.153.509.5.902 1.105 1.153 1.772.247.637.415 1.363.465 2.428.047 1.066.06 1.405.06 4.122 0 2.717-.01 3.056-.06 4.122-.05 1.065-.218 1.79-.465 2.428a4.883 4.883 0 01-1.153 1.772c-.5.508-1.105.902-1.772 1.153-.637.247-1.363.415-2.428.465-1.066.047-1.405.06-4.122.06-2.717 0-3.056-.01-4.122-.06-1.065-.05-1.79-.218-2.428-.465a4.89 4.89 0 01-1.772-1.153 4.904 4.904 0 01-1.153-1.772c-.247-.637-.415-1.363-.465-2.428C2.013 15.056 2 14.717 2 12c0-2.717.01-3.056.06-4.122.05-1.066.217-1.79.465-2.428a4.88 4.88 0 011.153-1.772A4.897 4.897 0 015.45 2.525c.638-.247 1.362-.415 2.428-.465C8.944 2.013 9.283 2 12 2zm0 5a5 5 0 100 10 5 5 0 000-10zm6.5-.25a1.25 1.25 0 10-2.5 0 1.25 1.25 0 002.5 0zM12 9a3 3 0 110 6 3 3 0 010-6z" />
            </svg>
         );
      default:
         return (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
               <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
            </svg>
         );
   }
};
const getSentimentIcon = (sentiment, size = 16) => {
   switch (sentiment?.toLowerCase()) {
      case 'positive':
         return <Smile size={size} className="text-emerald-400" />;
      case 'negative':
         return <Frown size={size} className="text-red-400" />;
      case 'critical':
         return <AlertCircle size={size} className="text-orange-400" />;
      case 'neutral':
      default:
         return <Minus size={size} className="text-gray-400" />;
   }
};
const getSentimentColor = sentiment => {
   switch (sentiment?.toLowerCase()) {
      case 'positive':
         return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
      case 'negative':
         return 'text-red-400 border-red-500/30 bg-red-500/10';
      case 'critical':
         return 'text-orange-400 border-orange-500/30 bg-orange-500/10';
      case 'neutral':
      default:
         return 'text-gray-400 border-gray-600/30 bg-gray-600/10';
   }
};
const getPlatformColor = platform => {
   switch (platform?.toLowerCase()) {
      case 'x.com':
      case 'x':
         return 'text-blue-400';
      case 'facebook':
         return 'text-blue-600';
      case 'instagram':
         return 'text-pink-500';
      case 'linkedin':
         return 'text-blue-700';
      default:
         return 'text-gray-400';
   }
};
const PostDetailPanel = ({ post, isOpen, onClose }) => {
   const [loading, setLoading] = React.useState(false);
   const [fullPost, setFullPost] = React.useState(null);

   useEffect(() => {
      if (isOpen && post) {
         loadFullPostDetails(post.post_id);
      }
   }, [isOpen, post]);

   const loadFullPostDetails = async postId => {
      if (!postId) return;
      try {
         setLoading(true);
         const response = await api.socialMedia.getById(postId);
         setFullPost(response.data);
      } catch (error) {
         console.error('Error loading post details:', error);
      } finally {
         setLoading(false);
      }
   };

   const displayPost = fullPost || post;
   if (!displayPost) return null;
   const sentiment = displayPost.sentiment || 'neutral';
   const engagement = displayPost.engagement || {};
   const commentsCount = engagement.replies || 0;
   const likesCount = engagement.likes || 0;
   const sharesCount = engagement.retweets || 0;
   const bookmarkCount = engagement.bookmarks || 0;
   const viewCount = engagement.views || 0;
   const hasMedia = displayPost.media && displayPost.media.length > 0;

   return (
      <>
         {isOpen && (
            <div
               className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
               onClick={onClose}
            ></div>
         )}
         <div
            className={`fixed inset-y-0 right-0 w-full md:w-2/3 lg:w-1/2 xl:w-2/5 bg-gradient-to-b from-gray-900 to-gray-800 shadow-xl z-50 transition-transform duration-300 transform ${
               isOpen ? 'translate-x-0' : 'translate-x-full'
            } flex flex-col`}
         >
            <div className="border-b border-gray-700 p-4 flex items-center justify-between sticky top-0 bg-gray-900 z-10 shadow-md">
               <div className="flex items-center gap-3">
                  <button
                     onClick={onClose}
                     className="p-1.5 rounded-md hover:bg-gray-700 transition-colors text-gray-400 hover:text-white"
                  >
                     <X size={20} />
                  </button>
                  <h2 className="text-lg font-medium text-white">Post Details</h2>
               </div>
               {sentiment && (
                  <div
                     className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full ${getSentimentColor(
                        sentiment
                     )}`}
                  >
                     {getSentimentIcon(sentiment)}
                     <span className="text-sm font-medium capitalize">{sentiment}</span>
                  </div>
               )}
            </div>
            {loading ? (
               <div className="flex-grow flex items-center justify-center">
                  <div className="animate-spin w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full"></div>
               </div>
            ) : (
               <div className="flex-grow overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                  <div className="p-4 border-b border-gray-700/50 bg-gradient-to-r from-gray-900 to-gray-800">
                     <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-800 to-gray-700 border border-gray-600/50 flex items-center justify-center overflow-hidden">
                           {displayPost.user_profile_pic_url ? (
                              <img
                                 src={displayPost.user_profile_pic_url}
                                 alt={displayPost.user_display_name || displayPost.user_handle}
                                 className="w-full h-full object-cover"
                              />
                           ) : (
                              <div className={`${getPlatformColor(displayPost.platform)}`}>
                                 {getPlatformIcon(displayPost.platform)}
                              </div>
                           )}
                        </div>
                        <div>
                           <div className="font-medium text-white">
                              {displayPost.user_display_name ||
                                 (displayPost.user_handle
                                    ? displayPost.user_handle.replace('@', '')
                                    : 'Unknown User')}
                           </div>
                           <div className="flex items-center text-sm text-gray-400 gap-2">
                              <span>{displayPost.user_handle || '@unknown'}</span>
                              <span className="text-gray-500">•</span>
                              <span
                                 className={`${getPlatformColor(displayPost.platform)} font-medium`}
                              >
                                 {displayPost.platform?.replace('.com', '')}
                              </span>
                           </div>
                        </div>
                     </div>
                     <div className="flex items-center mt-3 text-gray-400 text-sm gap-3">
                        <div className="flex items-center gap-1.5">
                           <Calendar size={14} />
                           <span>{formatDate(displayPost.post_timestamp)}</span>
                        </div>
                        {displayPost.post_display_time && (
                           <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-gray-800/80 border border-gray-700/50">
                              <Clock size={12} />
                              <span className="text-xs">{displayPost.post_display_time}</span>
                           </div>
                        )}
                        {displayPost.post_url && (
                           <a
                              href={displayPost.post_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-emerald-400 hover:text-emerald-300 transition-colors text-xs flex items-center gap-1"
                           >
                              <ExternalLink size={12} />
                              <span>Original post</span>
                           </a>
                        )}
                     </div>
                  </div>
                  <div className="p-4">
                     <p className="text-gray-100 whitespace-pre-line text-base leading-relaxed">
                        {displayPost.post_text}
                     </p>
                     {hasMedia && (
                        <div className="mt-4">
                           <div className="flex items-center justify-between mb-2">
                              <h3 className="text-sm font-medium text-gray-300">Media</h3>
                              {displayPost.media_count > 0 && (
                                 <span className="bg-gray-800 px-2 py-0.5 rounded-full text-xs text-gray-400">
                                    {displayPost.media_count}{' '}
                                    {displayPost.media_count === 1 ? 'item' : 'items'}
                                 </span>
                              )}
                           </div>
                           <div
                              className={`grid ${
                                 displayPost.media.length > 1 ? 'grid-cols-2 gap-2' : 'grid-cols-1'
                              }`}
                           >
                              {displayPost.media.map((item, index) => (
                                 <div
                                    key={index}
                                    className="rounded-lg overflow-hidden border border-gray-700 bg-gray-800/50 hover:bg-gray-800 transition-colors"
                                 >
                                    {item.type === 'image' ? (
                                       <div className="relative group">
                                          <img
                                             src={item.url}
                                             alt="Post media"
                                             className="w-full h-auto object-contain hover:opacity-95 transition-opacity cursor-pointer"
                                             onClick={() => window.open(item.url, '_blank')}
                                          />
                                          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/30">
                                             <button
                                                onClick={() => window.open(item.url, '_blank')}
                                                className="p-2 bg-gray-900/80 rounded-full"
                                             >
                                                <ExternalLink size={16} className="text-white" />
                                             </button>
                                          </div>
                                       </div>
                                    ) : item.type === 'video' ? (
                                       <div className="relative">
                                          <video src={item.url} controls className="w-full" />
                                       </div>
                                    ) : (
                                       <div className="bg-gray-800 p-4 text-gray-400 text-center">
                                          Unsupported media type: {item.type}
                                       </div>
                                    )}
                                 </div>
                              ))}
                           </div>
                        </div>
                     )}
                     <div className="mt-6 space-y-4">
                        {displayPost.categories && displayPost.categories.length > 0 && (
                           <div>
                              <h3 className="text-sm font-medium text-gray-300 mb-2 flex items-center">
                                 <svg
                                    className="w-4 h-4 mr-1.5"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                 >
                                    <path
                                       strokeLinecap="round"
                                       strokeLinejoin="round"
                                       strokeWidth="2"
                                       d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                                    />
                                 </svg>
                                 Categories
                              </h3>
                              <div className="flex flex-wrap gap-2">
                                 {displayPost.categories.map((category, index) => (
                                    <span
                                       key={index}
                                       className="bg-gray-800/80 border border-gray-700/80 px-2.5 py-1 rounded-md text-xs text-gray-300 hover:bg-gray-700/90 hover:text-white transition-colors cursor-default"
                                    >
                                       {category}
                                    </span>
                                 ))}
                              </div>
                           </div>
                        )}
                        {displayPost.tags && displayPost.tags.length > 0 && (
                           <div>
                              <h3 className="text-sm font-medium text-gray-300 mb-2 flex items-center">
                                 <svg
                                    className="w-4 h-4 mr-1.5"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                 >
                                    <path
                                       strokeLinecap="round"
                                       strokeLinejoin="round"
                                       strokeWidth="2"
                                       d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
                                    />
                                 </svg>
                                 Tags
                              </h3>
                              <div className="flex flex-wrap gap-2">
                                 {displayPost.tags.map((tag, index) => (
                                    <span
                                       key={index}
                                       className="bg-gradient-to-r from-emerald-900/60 to-emerald-800/60 border border-emerald-700/50 px-2.5 py-1 rounded-md text-xs text-emerald-300 hover:from-emerald-800/70 hover:to-emerald-700/70 hover:text-emerald-200 transition-colors cursor-default"
                                    >
                                       #{tag}
                                    </span>
                                 ))}
                              </div>
                           </div>
                        )}
                     </div>
                     {displayPost.analysis_reasoning && (
                        <div className="mt-6 p-4 bg-gradient-to-r from-gray-800/80 to-gray-900/80 border border-gray-700 rounded-lg">
                           <h3 className="text-sm font-medium text-emerald-400 mb-2 flex items-center gap-1.5">
                              <svg
                                 className="w-4 h-4"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                              >
                                 <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                                 />
                              </svg>
                              Sentiment Analysis
                           </h3>
                           <div className="flex items-center gap-2 mb-2">
                              <div
                                 className={`flex items-center gap-1.5 px-2 py-1 rounded-full ${getSentimentColor(
                                    sentiment
                                 )}`}
                              >
                                 {getSentimentIcon(sentiment, 14)}
                                 <span className="text-xs font-medium capitalize">{sentiment}</span>
                              </div>
                           </div>
                           <p className="text-sm text-gray-300 border-t border-gray-700/50 pt-2">
                              {displayPost.analysis_reasoning}
                           </p>
                        </div>
                     )}
                  </div>
               </div>
            )}
            <div className="border-t border-gray-700 p-4 bg-gray-900">
               <div className="flex flex-col space-y-3">
                  <div className="flex items-center justify-between">
                     <h3 className="text-xs font-medium text-gray-400">Engagement</h3>
                     {displayPost.is_ad && (
                        <span className="bg-blue-900/40 text-blue-300 px-2 py-0.5 rounded-full text-xs border border-blue-800/50">
                           Sponsored
                        </span>
                     )}
                  </div>
                  <div className="flex items-center justify-between">
                     <div className="flex items-center gap-4">
                        {commentsCount > 0 && (
                           <div className="flex items-center gap-1.5">
                              <MessageCircle size={18} className="text-gray-400" />
                              <span className="text-sm text-gray-300">
                                 {formatNumber(commentsCount)}
                              </span>
                           </div>
                        )}

                        {likesCount > 0 && (
                           <div className="flex items-center gap-1.5">
                              <Heart size={18} className="text-gray-400" />
                              <span className="text-sm text-gray-300">
                                 {formatNumber(likesCount)}
                              </span>
                           </div>
                        )}

                        {sharesCount > 0 && (
                           <div className="flex items-center gap-1.5">
                              <Share2 size={18} className="text-gray-400" />
                              <span className="text-sm text-gray-300">
                                 {formatNumber(sharesCount)}
                              </span>
                           </div>
                        )}
                        {viewCount > 0 && (
                           <div className="flex items-center gap-1.5">
                              <svg
                                 className="w-4.5 h-4.5 text-gray-400"
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
                              <span className="text-sm text-gray-300">
                                 {formatNumber(viewCount)}
                              </span>
                           </div>
                        )}
                     </div>
                     {displayPost.post_url && (
                        <a
                           href={displayPost.post_url}
                           target="_blank"
                           rel="noopener noreferrer"
                           className="flex items-center gap-1.5 bg-emerald-800/60 hover:bg-emerald-700/70 px-3 py-1.5 rounded-md text-emerald-300 text-sm transition-colors"
                        >
                           <ExternalLink size={14} />
                           <span>View Original</span>
                        </a>
                     )}
                  </div>
               </div>
            </div>
         </div>
      </>
   );
};

export default PostDetailPanel;
