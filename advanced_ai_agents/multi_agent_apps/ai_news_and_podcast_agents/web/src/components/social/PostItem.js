import React from 'react';
import {
   MessageCircle,
   Heart,
   Share2,
   Smile,
   Frown,
   AlertCircle,
   Minus,
   ExternalLink,
   Facebook,
} from 'lucide-react';

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
   if (number >= 1000000) {
      return (number / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
   }
   if (number >= 10000) {
      return Math.floor(number / 1000) + 'k';
   }
   if (number >= 1000) {
      return (number / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
   }
   return number.toString();
};

const getPlatformIcon = platform => {
   switch (platform?.toLowerCase()) {
      case 'x.com':
      case 'x':
         return (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
               <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
         );
      case 'facebook.com':
         return <Facebook className="w-4 h-4 text-blue-600" />;
      case 'instagram':
         return (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
               <path d="M12 2c2.717 0 3.056.01 4.122.06 1.065.05 1.79.217 2.428.465.66.254 1.216.598 1.772 1.153.509.5.902 1.105 1.153 1.772.247.637.415 1.363.465 2.428.047 1.066.06 1.405.06 4.122 0 2.717-.01 3.056-.06 4.122-.05 1.065-.218 1.79-.465 2.428a4.883 4.883 0 01-1.153 1.772c-.5.508-1.105.902-1.772 1.153-.637.247-1.363.415-2.428.465-1.066.047-1.405.06-4.122.06-2.717 0-3.056-.01-4.122-.06-1.065-.05-1.79-.218-2.428-.465a4.89 4.89 0 01-1.772-1.153 4.904 4.904 0 01-1.153-1.772c-.247-.637-.415-1.363-.465-2.428C2.013 15.056 2 14.717 2 12c0-2.717.01-3.056.06-4.122.05-1.066.217-1.79.465-2.428a4.88 4.88 0 011.153-1.772A4.897 4.897 0 015.45 2.525c.638-.247 1.362-.415 2.428-.465C8.944 2.013 9.283 2 12 2zm0 5a5 5 0 100 10 5 5 0 000-10zm6.5-.25a1.25 1.25 0 10-2.5 0 1.25 1.25 0 002.5 0zM12 9a3 3 0 110 6 3 3 0 010-6z" />
            </svg>
         );
      case 'linkedin':
         return (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
               <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
         );
      default:
         return (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
               <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
            </svg>
         );
   }
};

const getSentimentIcon = sentiment => {
   switch (sentiment?.toLowerCase()) {
      case 'positive':
         return <Smile className="w-3.5 h-3.5" />;
      case 'negative':
         return <Frown className="w-3.5 h-3.5" />;
      case 'critical':
         return <AlertCircle className="w-3.5 h-3.5" />;
      case 'neutral':
      default:
         return <Minus className="w-3.5 h-3.5" />;
   }
};

const getSentimentCardStyle = sentiment => {
   switch (sentiment?.toLowerCase()) {
      case 'positive':
         return 'border-emerald-500/30 hover:border-emerald-500/50 bg-gradient-to-br from-emerald-900/10 to-teal-900/10';
      case 'negative':
         return 'border-red-500/30 hover:border-red-500/50 bg-gradient-to-br from-red-900/10 to-red-800/10';
      case 'critical':
         return 'border-orange-500/30 hover:border-orange-500/50 bg-gradient-to-br from-orange-900/10 to-orange-800/10';
      case 'neutral':
      default:
         return 'border-gray-700/50 hover:border-gray-600/50 bg-gradient-to-br from-gray-800/50 to-gray-700/50 hover:from-gray-700/60 hover:to-gray-600/60';
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

const PostItem = ({ post, onPostClick }) => {
   if (!post) return null;
   const sentiment = post.sentiment || 'neutral';
   const engagement = post.engagement || {};
   const replyCount = engagement.replies || post.engagement_reply_count || 0;
   const retweetCount = engagement.retweets || post.engagement_retweet_count || 0;
   const likeCount = engagement.likes || post.engagement_like_count || 0;
   const viewCount = engagement.views || post.engagement_view_count || 0;
   const commentsCount = replyCount || 0;
   const likesCount = likeCount || 0;
   const sharesCount = retweetCount || 0;
   const hasVeryHighEngagement = commentsCount > 200 || sharesCount > 200 || likesCount > 1000;

   const handleClick = () => {
      if (onPostClick) {
         onPostClick(post);
      }
   };

   return (
      <div
         className="block h-full cursor-pointer transition-transform duration-200 hover:scale-[1.02] active:scale-[0.98]"
         onClick={handleClick}
      >
         <div
            className={`relative h-full flex flex-col overflow-hidden group backdrop-blur-sm rounded-lg transition-colors duration-300 shadow-md hover:shadow-md ${getSentimentCardStyle(
               sentiment
            )}`}
         >
            <div
               className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${
                  sentiment === 'positive'
                     ? 'from-emerald-500 to-teal-500'
                     : sentiment === 'negative'
                     ? 'from-red-500 to-red-600'
                     : sentiment === 'critical'
                     ? 'from-orange-500 to-orange-600'
                     : 'from-gray-600 to-gray-700'
               }`}
            ></div>
            <div
               className={`flex flex-col px-3.5 py-2.5 border-b ${
                  sentiment === 'positive'
                     ? 'border-emerald-500/30 bg-gradient-to-r from-gray-800/80 to-emerald-900/40'
                     : sentiment === 'negative'
                     ? 'border-red-500/30 bg-gradient-to-r from-gray-800/80 to-red-900/40'
                     : sentiment === 'critical'
                     ? 'border-orange-500/30 bg-gradient-to-r from-gray-800/80 to-orange-900/40'
                     : 'border-gray-700/30 bg-gradient-to-r from-gray-800/80 to-gray-900/80'
               } backdrop-blur`}
            >
               <div className="flex items-center gap-2.5 justify-between">
                  <div className="flex items-center gap-2.5">
                     <div className="min-w-8 w-8 h-8 bg-gradient-to-br from-gray-800 to-gray-900 rounded-full flex items-center justify-center border border-gray-700/50 shadow-inner overflow-hidden transition-all duration-300 group-hover:border-gray-600">
                        <div className="flex items-center justify-center w-full h-full">
                           <div
                              className={`text-${
                                 getPlatformColor(post.platform).split('-')[1]
                              } group-hover:text-opacity-90 transition-colors duration-300`}
                           >
                              {getPlatformIcon(post.platform)}
                           </div>
                        </div>
                     </div>
                     <div className="min-w-0">
                        <div className="flex items-center gap-1">
                           <span className="text-white font-medium text-sm truncate max-w-[700%] group-hover:text-emerald-50 transition-colors duration-300">
                              {post.user_display_name ||
                                 post.author_name ||
                                 (post.user_handle
                                    ? `@${post.user_handle.replace('@', '')}`
                                    : 'Unknown Author')}
                           </span>
                        </div>
                     </div>
                  </div>
               </div>
               <div className="flex items-center flex-wrap text-gray-400 text-xs mt-1">
                  <span className="truncate max-w-[100px] inline-block">
                     @{post.user_handle ? post.user_handle.replace('@', '') : 'unknown'}
                  </span>
                  <span className="text-gray-500 mx-1 flex-shrink-0">·</span>
                  <span
                     className={`text-xs ${getPlatformColor(
                        post.platform
                     )} flex-shrink-0 font-medium mr-0.5 group-hover:font-semibold transition-all duration-300`}
                  >
                     {post.platform?.replace('.com', '') || 'web'}
                  </span>
                  <span className="text-gray-500 mx-1 flex-shrink-0">·</span>
                  <span className="text-gray-500 flex-shrink-0">
                     {formatDate(post.post_timestamp)}
                  </span>
               </div>
               <div className="flex items-center mt-2">
                  <div
                     className={`flex items-center gap-1.5 px-2 py-1 rounded-full ${
                        sentiment === 'positive'
                           ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/50 text-emerald-400'
                           : sentiment === 'negative'
                           ? 'bg-gradient-to-r from-red-500/20 to-red-600/20 border border-red-500/50 text-red-400'
                           : sentiment === 'critical'
                           ? 'bg-gradient-to-r from-orange-500/20 to-orange-600/20 border border-orange-500/50 text-orange-400'
                           : 'bg-gradient-to-r from-gray-600/30 to-gray-700/30 border border-gray-600/40 text-gray-300'
                     } group-hover:shadow-sm transition-all duration-300`}
                     title={`${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)} sentiment`}
                  >
                     {getSentimentIcon(sentiment)}
                     <span className="text-xs font-medium capitalize">{sentiment}</span>
                  </div>
               </div>
            </div>
            <div className="px-4 py-3.5 flex-grow min-h-[80px] bg-gradient-to-br from-transparent to-gray-800/10">
               <p className="text-gray-200 text-sm leading-relaxed line-clamp-3 group-hover:text-white transition-colors duration-300">
                  {post.post_text || 'No content available'}
               </p>
            </div>
            <div className="border-t border-gray-700/30 bg-gradient-to-r from-gray-800/50 to-gray-700/50 backdrop-blur-sm">
               {hasVeryHighEngagement ? (
                  <div className="py-2 px-3.5">
                     <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-3">
                           {commentsCount > 0 && (
                              <div className="flex items-center px-2 py-1 rounded-full bg-gradient-to-r from-gray-700/40 to-gray-800/40 border border-gray-700/30 transition-colors duration-300">
                                 <MessageCircle className="w-3 h-3 text-gray-400 mr-1.5 group-hover:text-emerald-400 transition-colors duration-300" />
                                 <span className="text-xs text-gray-400 group-hover:text-emerald-100 transition-colors duration-300">
                                    {formatNumber(commentsCount)}
                                 </span>
                              </div>
                           )}
                           {sharesCount > 0 && (
                              <div className="flex items-center px-2 py-1 rounded-full bg-gradient-to-r from-gray-700/40 to-gray-800/40 border border-gray-700/30 transition-colors duration-300">
                                 <Share2 className="w-3 h-3 text-gray-400 mr-1.5 group-hover:text-emerald-400 transition-colors duration-300" />
                                 <span className="text-xs text-gray-400 group-hover:text-emerald-100 transition-colors duration-300">
                                    {formatNumber(sharesCount)}
                                 </span>
                              </div>
                           )}
                           {likesCount > 0 && (
                              <div className="flex items-center px-2 py-1 rounded-full bg-gradient-to-r from-gray-700/40 to-gray-800/40 border border-gray-700/30 transition-colors duration-300">
                                 <Heart className="w-3 h-3 text-gray-400 mr-1.5 group-hover:text-emerald-400 transition-colors duration-300" />
                                 <span className="text-xs text-gray-400 group-hover:text-emerald-100 transition-colors duration-300">
                                    {formatNumber(likesCount)}
                                 </span>
                              </div>
                           )}
                        </div>
                     </div>
                  </div>
               ) : (
                  <div className="py-2 px-3.5 flex items-center justify-between">
                     <div className="flex items-center gap-3">
                        {commentsCount > 0 && (
                           <div className="flex items-center transition-colors duration-300">
                              <MessageCircle className="w-3.5 h-3.5 text-gray-400 mr-1.5 group-hover:text-emerald-400 transition-colors duration-300" />
                              <span className="text-xs text-gray-400 group-hover:text-white transition-colors duration-300">
                                 {formatNumber(commentsCount)}
                              </span>
                           </div>
                        )}
                        {sharesCount > 0 && (
                           <div className="flex items-center transition-colors duration-300">
                              <Share2 className="w-3.5 h-3.5 text-gray-400 mr-1.5 group-hover:text-emerald-400 transition-colors duration-300" />
                              <span className="text-xs text-gray-400 group-hover:text-white transition-colors duration-300">
                                 {formatNumber(sharesCount)}
                              </span>
                           </div>
                        )}
                        {likesCount > 0 && (
                           <div className="flex items-center transition-colors duration-300">
                              <Heart className="w-3.5 h-3.5 text-gray-400 mr-1.5 group-hover:text-emerald-400 transition-colors duration-300" />
                              <span className="text-xs text-gray-400 group-hover:text-white transition-colors duration-300">
                                 {formatNumber(likesCount)}
                              </span>
                           </div>
                        )}
                        {viewCount > 0 && (
                           <div className="flex items-center transition-colors duration-300">
                              <svg
                                 className="w-3.5 h-3.5 text-gray-400 mr-1.5 group-hover:text-emerald-400 transition-colors duration-300"
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
                              <span className="text-xs text-gray-400 group-hover:text-white transition-colors duration-300">
                                 {formatNumber(viewCount)}
                              </span>
                           </div>
                        )}
                     </div>
                  </div>
               )}
               <div
                  className={`border-t py-1.5 px-3.5 ${
                     sentiment === 'positive'
                        ? 'border-emerald-500/30 bg-gradient-to-r from-gray-800/50 to-emerald-900/30'
                        : sentiment === 'negative'
                        ? 'border-red-500/30 bg-gradient-to-r from-gray-800/50 to-red-900/30'
                        : sentiment === 'critical'
                        ? 'border-orange-500/30 bg-gradient-to-r from-gray-800/50 to-orange-900/30'
                        : 'border-gray-700/20 bg-gradient-to-r from-gray-800/50 to-gray-900/50'
                  }`}
               >
                  <div
                     className={`flex items-center justify-center gap-1.5 ${
                        sentiment === 'positive'
                           ? 'text-emerald-400'
                           : sentiment === 'negative'
                           ? 'text-red-400'
                           : sentiment === 'critical'
                           ? 'text-orange-400'
                           : 'text-gray-400 group-hover:text-emerald-400'
                     } transition-colors duration-300 text-xs`}
                  >
                     <ExternalLink className="w-3 h-3" />
                     <span>View details</span>
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
};

export default PostItem;
