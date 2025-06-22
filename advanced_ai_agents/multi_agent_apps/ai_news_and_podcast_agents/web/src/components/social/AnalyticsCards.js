import React, { useMemo } from 'react';
import {
   Users, TrendingUp, Smile, Frown, AlertCircle, Minus, Hash
} from 'lucide-react';

const SENTIMENT_CONFIG = {
   positive: { 
      icon: Smile, 
      color: '#10b981', 
      bgClass: 'bg-emerald-500/10', 
      borderClass: 'border-emerald-500/30',
      textClass: 'text-emerald-400',
      barClass: 'bg-gradient-to-r from-emerald-500 to-emerald-400'
   },
   negative: { 
      icon: Frown, 
      color: '#ef4444', 
      bgClass: 'bg-red-500/10', 
      borderClass: 'border-red-500/30',
      textClass: 'text-red-400',
      barClass: 'bg-gradient-to-r from-red-500 to-red-400'
   },
   critical: { 
      icon: AlertCircle, 
      color: '#f97316', 
      bgClass: 'bg-orange-500/10', 
      borderClass: 'border-orange-500/30',
      textClass: 'text-orange-400',
      barClass: 'bg-gradient-to-r from-orange-500 to-orange-400'
   },
   neutral: { 
      icon: Minus, 
      color: '#6b7280', 
      bgClass: 'bg-gray-500/10', 
      borderClass: 'border-gray-500/30',
      textClass: 'text-gray-400',
      barClass: 'bg-gradient-to-r from-gray-500 to-gray-400'
   }
};

const formatNumber = (num) => {
   if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
   if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
   return num.toString();
};

const getDominantSentiment = (item) => {
   const sentiments = [
      { type: 'positive', value: item.positive_percent || 0 },
      { type: 'negative', value: item.negative_percent || 0 },
      { type: 'critical', value: item.critical_percent || 0 },
      { type: 'neutral', value: item.neutral_percent || 0 }
   ];
   return sentiments.reduce((max, current) => current.value > max.value ? current : max).type;
};

const CompactSentimentBadge = ({ sentiment, percentage }) => {
   const config = SENTIMENT_CONFIG[sentiment];
   const Icon = config.icon;
   
   return (
      <div className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full border ${config.bgClass} ${config.borderClass}`}>
         <Icon size={10} className={config.textClass} />
         <span className={`text-xs font-medium ${config.textClass}`}>
            {Math.round(percentage)}%
         </span>
      </div>
   );
};

const MiniSentimentBar = ({ sentiment, percentage, count }) => {
   const config = SENTIMENT_CONFIG[sentiment];
   const Icon = config.icon;
   
   return (
      <div className="flex items-center gap-2">
         <div className="flex items-center gap-1 min-w-0">
            <Icon size={10} className={config.textClass} />
            <span className={`text-xs ${config.textClass} font-medium`}>
               {Math.round(percentage)}%
            </span>
         </div>
         <div className="flex-1 h-1 bg-gray-800 rounded-full overflow-hidden">
            <div 
               className={`h-full ${config.barClass} rounded-full transition-all duration-300`}
               style={{ width: `${Math.max(percentage, 2)}%` }}
            />
         </div>
         <span className="text-xs text-gray-500 min-w-0">
            {formatNumber(count)}
         </span>
      </div>
   );
};

const CompactAvatar = ({ user }) => {
   const displayName = user.user_display_name || user.user_handle?.replace('@', '') || 'U';
   const initials = displayName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
   
   return (
      <div className="w-7 h-7 bg-gradient-to-br from-gray-700 to-gray-800 rounded-full flex items-center justify-center border border-gray-600/50">
         <span className="text-xs font-medium text-white">{initials}</span>
      </div>
   );
};

const LoadingSkeleton = () => (
   <div className="space-y-2 p-3">
      {Array.from({ length: 4 }, (_, i) => (
         <div key={i} className="animate-pulse flex items-center gap-2">
            <div className="w-7 h-7 bg-gray-700 rounded-full"></div>
            <div className="flex-1">
               <div className="w-20 h-3 bg-gray-700 rounded mb-1"></div>
               <div className="w-16 h-2 bg-gray-700 rounded"></div>
            </div>
         </div>
      ))}
   </div>
);

const UserSentimentCard = ({ userSentiment = [], loading = false }) => {
   const sortedUsers = useMemo(() => 
      userSentiment.slice(0, 8).sort((a, b) => b.total_posts - a.total_posts), 
      [userSentiment]
   );

   return (
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg shadow-xl border border-gray-700/50 overflow-hidden">
         <div className="relative px-3 py-2 bg-gradient-to-r from-gray-800/90 to-gray-900/90 border-b border-gray-700/50">
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5"></div>
            <div className="relative flex items-center justify-between">
               <div className="flex items-center gap-2">
                  <div className="p-1 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-md">
                     <Users size={14} className="text-emerald-400" />
                  </div>
                  <div>
                     <h3 className="text-sm font-semibold text-white">Users Sentiment</h3>
                  </div>
               </div>
               <div className="px-2 py-1 bg-gray-800/60 rounded-full border border-gray-700/50">
                  <span className="text-xs font-medium text-gray-300">{sortedUsers.length}</span>
               </div>
            </div>
         </div>

         <div className="p-3">
            {loading ? (
               <LoadingSkeleton />
            ) : sortedUsers.length === 0 ? (
               <div className="flex flex-col items-center justify-center py-6 text-gray-400">
                  <Users size={24} className="mb-2 opacity-50" />
                  <p className="text-sm font-medium">No user data</p>
               </div>
            ) : (
               <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800">
                  {sortedUsers.map((user, index) => {
                     const dominantSentiment = getDominantSentiment(user);
                     const topSentiments = Object.entries(SENTIMENT_CONFIG)
                        .map(([sentiment]) => ({
                           sentiment,
                           percentage: user[`${sentiment}_percent`] || 0,
                           count: user[`${sentiment}_count`] || 0
                        }))
                        .filter(s => s.percentage > 0)
                        .sort((a, b) => b.percentage - a.percentage)
                        .slice(0, 2);
                     
                     return (
                        <div 
                           key={user.user_handle || index} 
                           className="group p-2.5 bg-gray-800/30 hover:bg-gray-800/50 rounded-md border border-gray-700/40 hover:border-gray-600/50 transition-all duration-200"
                        >
                           <div className="flex items-center gap-2.5 mb-2">
                              <CompactAvatar user={user} />
                              <div className="flex-1 min-w-0">
                                 <div className="flex items-center justify-between">
                                    <h4 className="text-sm font-medium text-white truncate max-w-24">
                                       {user.user_display_name || user.user_handle?.replace('@', '') || 'Unknown'}
                                    </h4>
                                    <CompactSentimentBadge 
                                       sentiment={dominantSentiment} 
                                       percentage={user[`${dominantSentiment}_percent`]} 
                                    />
                                 </div>
                                 <div className="flex items-center gap-1 text-xs text-gray-400">
                                    <span className="truncate max-w-16">{user.user_handle || '@unknown'}</span>
                                    <span>•</span>
                                    <span>{formatNumber(user.total_posts)} posts</span>
                                 </div>
                              </div>
                           </div>
                           
                           <div className="space-y-1">
                              {topSentiments.map(({ sentiment, percentage, count }) => (
                                 <MiniSentimentBar
                                    key={sentiment}
                                    sentiment={sentiment}
                                    percentage={percentage}
                                    count={count}
                                 />
                              ))}
                           </div>
                        </div>
                     );
                  })}
               </div>
            )}
         </div>
      </div>
   );
};

const TrendingTopicsCard = ({ trendingTopics = [], loading = false }) => {
   const sortedTopics = useMemo(() => 
      trendingTopics.slice(0, 8).sort((a, b) => b.total_count - a.total_count), 
      [trendingTopics]
   );

   return (
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg shadow-xl border border-gray-700/50 overflow-hidden">
         <div className="relative px-3 py-2 bg-gradient-to-r from-gray-800/90 to-gray-900/90 border-b border-gray-700/50">
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5"></div>
            <div className="relative flex items-center justify-between">
               <div className="flex items-center gap-2">
                  <div className="p-1 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-md">
                     <TrendingUp size={14} className="text-emerald-400" />
                  </div>
                  <div>
                     <h3 className="text-sm font-semibold text-white">Topics Sentiment</h3>
                  </div>
               </div>
               <div className="px-2 py-1 bg-gray-800/60 rounded-full border border-gray-700/50">
                  <span className="text-xs font-medium text-gray-300">{sortedTopics.length}</span>
               </div>
            </div>
         </div>

         <div className="p-3">
            {loading ? (
               <LoadingSkeleton />
            ) : sortedTopics.length === 0 ? (
               <div className="flex flex-col items-center justify-center py-6 text-gray-400">
                  <TrendingUp size={24} className="mb-2 opacity-50" />
                  <p className="text-sm font-medium">No trending topics</p>
               </div>
            ) : (
               <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800">
                  {sortedTopics.map((topic, index) => {
                     const dominantSentiment = getDominantSentiment(topic);
                     const topSentiments = Object.entries(SENTIMENT_CONFIG)
                        .map(([sentiment]) => ({
                           sentiment,
                           percentage: topic[`${sentiment}_percent`] || 0,
                           count: topic[`${sentiment}_count`] || 0
                        }))
                        .filter(s => s.percentage > 0)
                        .sort((a, b) => b.percentage - a.percentage)
                        .slice(0, 2);
                     
                     return (
                        <div 
                           key={topic.topic || index} 
                           className="group p-2.5 bg-gray-800/30 hover:bg-gray-800/50 rounded-md border border-gray-700/40 hover:border-gray-600/50 transition-all duration-200"
                        >
                           <div className="flex items-center gap-2.5 mb-2">
                              <div className="w-7 h-7 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-full flex items-center justify-center border border-emerald-500/30">
                                 <Hash size={12} className="text-emerald-400" />
                              </div>
                              <div className="flex-1 min-w-0">
                                 <div className="flex items-center justify-between">
                                    <h4 className="text-sm font-medium text-white truncate max-w-24">
                                       {topic.topic}
                                    </h4>
                                    <CompactSentimentBadge 
                                       sentiment={dominantSentiment} 
                                       percentage={topic[`${dominantSentiment}_percent`]} 
                                    />
                                 </div>
                                 <div className="flex items-center gap-1 text-xs text-gray-400">
                                    <span className="text-emerald-400">Trending</span>
                                    <span>•</span>
                                    <span>{formatNumber(topic.total_count)} mentions</span>
                                 </div>
                              </div>
                           </div>
                           
                           <div className="space-y-1">
                              {topSentiments.map(({ sentiment, percentage, count }) => (
                                 <MiniSentimentBar
                                    key={sentiment}
                                    sentiment={sentiment}
                                    percentage={percentage}
                                    count={count}
                                 />
                              ))}
                           </div>
                        </div>
                     );
                  })}
               </div>
            )}
         </div>
      </div>
   );
};

const AnalyticsCards = ({ userSentiment, trendingTopics, loading }) => {
   return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full">
         <UserSentimentCard userSentiment={userSentiment} loading={loading} />
         <TrendingTopicsCard trendingTopics={trendingTopics} loading={loading} />
      </div>
   );
};

export default AnalyticsCards;