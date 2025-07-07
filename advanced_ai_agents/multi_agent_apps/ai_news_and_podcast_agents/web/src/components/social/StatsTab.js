import React, { useState, useEffect, useMemo, useCallback, useRef, useId } from 'react';
import {
   XAxis,
   YAxis,
   CartesianGrid,
   Tooltip,
   Legend,
   ResponsiveContainer,
   PieChart,
   Pie,
   Cell,
   AreaChart,
   Area,
} from 'recharts';
import {
   MessageCircle,
   Heart,
   Share2,
   BarChart2,
   Smile,
   Frown,
   AlertCircle,
   Minus,
   ExternalLink,
   TrendingUp,
   Calendar,
   RefreshCw,
   PieChart as PieChartIcon,
   Activity,
   Facebook,
} from 'lucide-react';
import api from '../../services/api';
import AnalyticsCards from './AnalyticsCards';
import DateRangeFilter from './DateRangeFilter';

const ANALYTICS_CONFIG = {
   DEFAULT_DATE_RANGE_DAYS: 7,
   MAX_TRENDING_TOPICS: 10,
   MAX_USER_SENTIMENT: 10,
   MAX_INFLUENTIAL_POSTS: 5,
   MAX_CATEGORIES_DISPLAYED: 7,
   ANIMATION_DURATION: { CHART: 1000, HOVER: 200, SKELETON: 1500 },
   API_DEBOUNCE_MS: 500,
};
const PLATFORM_COLORS = {
   'x.com': 'blue-400',
   x: 'blue-400',
   twitter: 'blue-400',
   facebook: 'blue-600',
   instagram: 'pink-500',
   default: 'gray-400',
};
const COLORS = {
   positive: '#10b981',
   negative: '#ef4444',
   critical: '#f97316',
   neutral: '#6b7280',
   background: { dark: '#111827', medium: '#1f2937', light: '#374151' },
   border: { dark: '#1f2937', medium: '#374151', light: '#4b5563' },
   text: { primary: '#ffffff', secondary: '#9ca3af', tertiary: '#6b7280' },
};

const formatNumber = number => {
   if (!number || isNaN(number)) return '0';
   if (number >= 1000000) return (number / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
   if (number >= 10000) return Math.floor(number / 1000) + 'k';
   if (number >= 1000) return (number / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
   return number.toString();
};

const formatPercentage = (value, total) => {
   if (!total || total === 0) return '0.0';
   return ((value / total) * 100).toFixed(1);
};

const formatDate = (dateString, format = 'short') => {
   try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid date';
      return format === 'short'
         ? date.toLocaleDateString()
         : date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
   } catch {
      return 'Invalid date';
   }
};

const getPlatformIcon = platform => {
   switch (platform?.toLowerCase()) {
      case 'twitter':
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
      default:
         return (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
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

const getPlatformColor = platform =>
   PLATFORM_COLORS[platform?.toLowerCase()] || PLATFORM_COLORS.default;

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

class AnalyticsError extends Error {
   constructor(message, code, endpoint, originalError) {
      super(message);
      this.name = 'AnalyticsError';
      this.code = code;
      this.endpoint = endpoint;
      this.originalError = originalError;
   }
}

const errorHandler = {
   wrap: (fn, errorContext) => {
      return (...args) => {
         return fn(...args).catch(error => {
            console.error(`Error in ${errorContext}:`, error);
            throw new AnalyticsError(`Failed to ${errorContext}`, 'API_ERROR', errorContext, error);
         });
      };
   },
   getUserMessage: error => {
      if (error instanceof AnalyticsError) {
         switch (error.code) {
            case 'API_ERROR':
               return 'Unable to load data. Please check your connection and try again.';
            case 'RATE_LIMIT':
               return 'Too many requests. Please wait a moment and try again.';
            case 'UNAUTHORIZED':
               return 'Session expired. Please log in again.';
            default:
               return 'Something went wrong. Please try again.';
         }
      }
      return 'An unexpected error occurred.';
   },
};

const analyticsAPI = {
   sentiments: errorHandler.wrap(
      (startDate, endDate) => api.socialMedia.getSentiments(startDate, endDate),
      'fetch sentiment data'
   ),
   userSentiment: errorHandler.wrap(
      (limit, platform, startDate, endDate) =>
         api.socialMedia.getUserSentiment(limit, platform, startDate, endDate),
      'fetch user sentiment data'
   ),
   categorySentiment: errorHandler.wrap(
      (startDate, endDate) => api.socialMedia.getCategorySentiment(startDate, endDate),
      'fetch category sentiment data'
   ),
   trendingTopics: errorHandler.wrap(
      (startDate, endDate, limit) => api.socialMedia.getTrendingTopics(startDate, endDate, limit),
      'fetch trending topics'
   ),
   sentimentOverTime: errorHandler.wrap(
      (startDate, endDate, platform) =>
         api.socialMedia.getSentimentOverTime(startDate, endDate, platform),
      'fetch sentiment over time'
   ),
   influentialPosts: errorHandler.wrap(
      (sentiment, limit, startDate, endDate) =>
         api.socialMedia.getInfluentialPosts(sentiment, limit, startDate, endDate),
      'fetch influential posts'
   ),
   engagementStats: errorHandler.wrap(
      (startDate, endDate) => api.socialMedia.getEngagementStats(startDate, endDate),
      'fetch engagement stats'
   ),
};

const useAnalyticsData = (dateRange, platforms) => {
   const [data, setData] = useState({
      sentimentData: [],
      userSentiment: [],
      categorySentiment: [],
      trendingTopics: [],
      sentimentOverTime: [],
      influentialPosts: [],
      engagementStats: null,
   });
   const [loading, setLoading] = useState(true);
   const [errors, setErrors] = useState({});

   const fetchData = useCallback(async () => {
      if (!platforms?.length) return;
      setLoading(true);
      setErrors({});

      try {
         const [
            sentiments,
            userSent,
            categorySent,
            trending,
            sentimentTime,
            influential,
            engagement,
         ] = await Promise.allSettled([
            analyticsAPI.sentiments(dateRange.startDate, dateRange.endDate),
            analyticsAPI.userSentiment(
               ANALYTICS_CONFIG.MAX_USER_SENTIMENT,
               null,
               dateRange.startDate,
               dateRange.endDate
            ),
            analyticsAPI.categorySentiment(dateRange.startDate, dateRange.endDate),
            analyticsAPI.trendingTopics(
               dateRange.startDate,
               dateRange.endDate,
               ANALYTICS_CONFIG.MAX_TRENDING_TOPICS
            ),
            analyticsAPI.sentimentOverTime(dateRange.startDate, dateRange.endDate, null),
            analyticsAPI.influentialPosts(
               null,
               ANALYTICS_CONFIG.MAX_INFLUENTIAL_POSTS,
               dateRange.startDate,
               dateRange.endDate
            ),
            analyticsAPI.engagementStats(dateRange.startDate, dateRange.endDate),
         ]);

         const newData = { ...data };
         const newErrors = {};

         if (sentiments.status === 'fulfilled') {
            const sentimentsData = sentiments.value.data || [];
            const totalPosts = sentimentsData.reduce((sum, item) => sum + item.post_count, 0);
            newData.sentimentData = sentimentsData.map(item => ({
               ...item,
               name: item.sentiment,
               value: item.post_count,
               percentage: formatPercentage(item.post_count, totalPosts),
            }));
         } else newErrors.sentiments = sentiments.reason;

         if (userSent.status === 'fulfilled') newData.userSentiment = userSent.value.data || [];
         else newErrors.userSentiment = userSent.reason;

         if (categorySent.status === 'fulfilled')
            newData.categorySentiment = categorySent.value.data || [];
         else newErrors.categorySentiment = categorySent.reason;

         if (trending.status === 'fulfilled') newData.trendingTopics = trending.value.data || [];
         else newErrors.trendingTopics = trending.reason;

         if (sentimentTime.status === 'fulfilled') {
            const timeData = sentimentTime.value.data || [];
            newData.sentimentOverTime = timeData.map(item => ({
               date: formatDate(item.post_date),
               positive: item.positive_count,
               negative: item.negative_count,
               critical: item.critical_count,
               neutral: item.neutral_count,
               total: item.total_count,
            }));
         } else newErrors.sentimentOverTime = sentimentTime.reason;

         if (influential.status === 'fulfilled')
            newData.influentialPosts = influential.value.data || [];
         else newErrors.influentialPosts = influential.reason;

         if (engagement.status === 'fulfilled')
            newData.engagementStats = engagement.value.data || null;
         else newErrors.engagementStats = engagement.reason;

         setData(newData);
         setErrors(newErrors);
      } catch (error) {
         setErrors({ general: error });
      } finally {
         setLoading(false);
      }
   }, [dateRange, platforms]);

   useEffect(() => {
      fetchData();
   }, [fetchData]);

   return { data, loading, errors, refetch: fetchData };
};

const useDebouncedCallback = (callback, delay) => {
   const timeoutRef = useRef();
   return useCallback(
      (...args) => {
         if (timeoutRef.current) clearTimeout(timeoutRef.current);
         timeoutRef.current = setTimeout(() => callback(...args), delay);
      },
      [callback, delay]
   );
};

const useScreenReaderAnnouncement = () => {
   const announce = useCallback(message => {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.className = 'sr-only';
      announcement.textContent = message;
      document.body.appendChild(announcement);
      setTimeout(() => document.body.removeChild(announcement), 1000);
   }, []);
   return announce;
};

const LoadingSpinner = () => (
   <div className="flex justify-center items-center py-16">
      <div className="relative flex flex-col items-center">
         <div className="animate-spin w-12 h-12 border-3 border-t-transparent rounded-full border-emerald-500 shadow-md"></div>
         <div className="absolute inset-0 flex items-center justify-center">
            <Activity className="h-5 w-5 text-emerald-400" />
         </div>
         <p className="mt-4 text-emerald-400 text-sm animate-pulse">Loading analytics data...</p>
      </div>
   </div>
);

const ChartSkeleton = ({ height = 'h-64' }) => (
   <div className={`${height} bg-gray-800/50 rounded-lg animate-pulse relative overflow-hidden`}>
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-gray-700/20 to-transparent animate-shimmer"></div>
      <div className="flex items-center justify-center h-full">
         <div className="text-gray-400 flex items-center gap-2">
            <div className="w-8 h-8 border-2 border-gray-600 border-t-emerald-500 rounded-full animate-spin"></div>
            <span className="text-sm">Loading chart...</span>
         </div>
      </div>
   </div>
);

const PostCardSkeleton = () => (
   <div className="bg-gray-800/50 rounded-lg p-4 animate-pulse">
      <div className="flex items-center gap-3 mb-3">
         <div className="w-8 h-8 bg-gray-700 rounded-full"></div>
         <div className="flex-1">
            <div className="w-24 h-3 bg-gray-700 rounded mb-1"></div>
            <div className="w-16 h-2 bg-gray-700 rounded"></div>
         </div>
      </div>
      <div className="space-y-2 mb-3">
         <div className="w-full h-3 bg-gray-700 rounded"></div>
         <div className="w-3/4 h-3 bg-gray-700 rounded"></div>
         <div className="w-1/2 h-3 bg-gray-700 rounded"></div>
      </div>
      <div className="flex justify-between">
         <div className="w-12 h-2 bg-gray-700 rounded"></div>
         <div className="w-12 h-2 bg-gray-700 rounded"></div>
         <div className="w-12 h-2 bg-gray-700 rounded"></div>
      </div>
   </div>
);

const ErrorBoundary = ({ errors, onRetry, children }) => {
   if (Object.keys(errors).length > 0) {
      return (
         <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 my-4">
            <div className="flex items-center gap-2 mb-2">
               <AlertCircle className="w-5 h-5 text-red-400" />
               <h3 className="text-red-400 font-medium">Data Loading Issues</h3>
            </div>
            <div className="space-y-2 text-sm text-red-300">
               {Object.entries(errors).map(([key, error]) => (
                  <div key={key} className="flex items-start gap-2">
                     <span className="font-medium capitalize">{key}:</span>
                     <span>{errorHandler.getUserMessage(error)}</span>
                  </div>
               ))}
            </div>
            <button
               onClick={onRetry}
               className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors duration-200"
               aria-label="Retry loading analytics data"
            >
               <RefreshCw className="w-4 h-4 inline mr-2" />
               Retry
            </button>
         </div>
      );
   }
   return children;
};

const AnalyticsCard = ({ title, icon, children, className = '' }) => (
   <div
      className={`bg-gradient-to-br from-gray-900 via-gray-850 to-gray-800 rounded-lg overflow-hidden shadow-xl border border-gray-700/50 transition-all duration-300 hover:shadow-2xl ${className}`}
   >
      <div className="relative px-3 py-2 bg-gradient-to-r from-gray-800/80 to-gray-900/80 backdrop-blur border-b border-gray-700/30">
         <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5" />
         <div className="relative flex items-center gap-2">
            <div className="p-1 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-md">
               {icon}
            </div>
            <h3 className="text-sm font-semibold text-white">{title}</h3>
         </div>
      </div>
      <div className="p-4">{children}</div>
   </div>
);

const CustomTooltip = ({ active, payload, label }) => {
   if (active && payload && payload.length) {
      return (
         <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-3 border border-gray-700/50 shadow-lg rounded-lg">
            <p className="text-white text-xs font-medium mb-1">{label}</p>
            {payload.map((entry, index) => (
               <p
                  key={index}
                  className="text-xs flex items-center gap-1.5 my-0.5"
                  style={{ color: entry.color }}
               >
                  <span
                     className="w-2 h-2 rounded-full"
                     style={{ backgroundColor: entry.color }}
                  ></span>
                  <span className="font-medium">{entry.name}:</span> {entry.value}
               </p>
            ))}
         </div>
      );
   }
   return null;
};

const SentimentLabelsOverlay = ({ data, colorMap }) => (
   <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
      {data.map((item, index) => {
         const sentimentType = item.name.toLowerCase();
         let offsetX = 0,
            offsetY = 0;

         if (sentimentType === 'positive') {
            offsetX = -70;
            offsetY = 65;
         } else if (sentimentType === 'negative') {
            offsetX = 65;
            offsetY = 65;
         } else if (sentimentType === 'critical') {
            offsetX = 75;
            offsetY = -50;
         } else if (sentimentType === 'neutral') {
            offsetX = -75;
            offsetY = -50;
         }

         return (
            <div
               key={item.name}
               className="absolute flex flex-col items-center text-center"
               style={{
                  transform: `translate(${offsetX}px, ${offsetY}px)`,
                  color: colorMap[sentimentType],
               }}
            >
               <span className="text-xs capitalize">{item.name}</span>
               <span className="text-sm font-bold tracking-tight">{item.percentage}%</span>
            </div>
         );
      })}
   </div>
);

const SentimentLegend = ({ data, colorMap }) => (
   <div className="flex flex-wrap justify-center gap-2 mt-3 bg-gray-800/50 p-2 rounded-md border border-gray-700/30 w-full">
      {data.map(item => {
         const sentimentType = item.name.toLowerCase();
         return (
            <div key={item.name} className="flex items-center bg-gray-900/70 px-2 py-1 rounded-md">
               <div
                  className="w-2 h-2 rounded-sm mr-1.5"
                  style={{ backgroundColor: colorMap[sentimentType] }}
               ></div>
               <span className="text-xs text-gray-300 capitalize">{item.name}</span>
               <span className="text-xs font-medium text-white ml-1.5 px-1 py-0.5 bg-gray-800 rounded-md">
                  {item.percentage}%
               </span>
            </div>
         );
      })}
   </div>
);

const SentimentPieChart = React.memo(({ data, colorMap }) => {
   const chartId = useId();
   return (
      <div role="img" aria-labelledby={`${chartId}-title`} aria-describedby={`${chartId}-desc`}>
         <div id={`${chartId}-title`} className="sr-only">
            Sentiment Distribution Pie Chart
         </div>
         <div id={`${chartId}-desc`} className="sr-only">
            A pie chart showing the distribution of sentiments:{' '}
            {data
               .map(
                  (item, index) =>
                     `${item.name} ${item.percentage}%${index < data.length - 1 ? ', ' : ''}`
               )
               .join('')}
         </div>
         <div className="flex flex-col items-center">
            <div className="h-56 w-full relative">
               <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                     <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        outerRadius={76}
                        innerRadius={35}
                        stroke="#2d3748"
                        strokeWidth={1}
                        dataKey="value"
                        animationDuration={ANALYTICS_CONFIG.ANIMATION_DURATION.CHART}
                        animationBegin={200}
                        paddingAngle={2}
                     >
                        {data.map((entry, index) => (
                           <Cell
                              key={`cell-${index}`}
                              fill={colorMap[entry.name.toLowerCase()]}
                              className="hover:opacity-90 transition-opacity cursor-pointer"
                              stroke="rgba(255,255,255,0.05)"
                              strokeWidth={1}
                              tabIndex={0}
                              role="button"
                              aria-label={`${entry.name} sentiment: ${entry.percentage}% (${entry.value} posts)`}
                           />
                        ))}
                     </Pie>
                     <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
                  </PieChart>
               </ResponsiveContainer>
               <SentimentLabelsOverlay data={data} colorMap={colorMap} />
            </div>
            <SentimentLegend data={data} colorMap={colorMap} />
         </div>
      </div>
   );
});

const CategoryHeatmap = ({ data }) => {
   const categoryChartData = useMemo(
      () =>
         data.slice(0, ANALYTICS_CONFIG.MAX_CATEGORIES_DISPLAYED).map(cat => ({
            name: cat.category,
            positive: cat.positive_count,
            negative: cat.negative_count,
            critical: cat.critical_count,
            neutral: cat.neutral_count,
            total: cat.total_count,
         })),
      [data]
   );

   return (
      <div className="flex flex-col h-64 px-2">
         <div className="flex flex-col h-full">
            <div className="flex mb-2 pl-24">
               <div className="flex-1 text-center text-xs text-emerald-400 font-medium">
                  Positive
               </div>
               <div className="flex-1 text-center text-xs text-red-400 font-medium">Negative</div>
               <div className="flex-1 text-center text-xs text-orange-400 font-medium">
                  Critical
               </div>
               <div className="flex-1 text-center text-xs text-gray-400 font-medium">Neutral</div>
            </div>
            <div className="flex flex-col flex-grow justify-between">
               {categoryChartData.map((cat, idx) => (
                  <div key={idx} className="flex h-8 mb-1 last:mb-0">
                     <div className="w-24 pr-2 flex items-center justify-end">
                        <span className="text-right text-gray-300 text-sm truncate">
                           {cat.name}
                        </span>
                     </div>
                     <div className="flex-1 flex gap-1">
                        {['positive', 'negative', 'critical', 'neutral'].map((sentiment, sidx) => (
                           <div
                              key={sidx}
                              className="flex-1 rounded-sm flex items-center justify-center relative overflow-hidden group cursor-pointer"
                              style={{
                                 backgroundColor: `rgba(${
                                    sentiment === 'positive'
                                       ? '16, 185, 129'
                                       : sentiment === 'negative'
                                       ? '239, 68, 68'
                                       : sentiment === 'critical'
                                       ? '249, 115, 22'
                                       : '107, 114, 128'
                                 }, ${Math.min(
                                    (cat[sentiment] / (cat.total || 1)) * 0.8 + 0.1,
                                    0.9
                                 )})`,
                              }}
                           >
                              <span className="text-white text-xs font-medium">
                                 {cat[sentiment] > 0 ? cat[sentiment] : ''}
                              </span>
                              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-black/50 flex items-center justify-center transition-opacity">
                                 <div className="bg-gray-900/90 px-2 py-1 rounded-sm">
                                    <div
                                       className={`text-xs ${
                                          sentiment === 'positive'
                                             ? 'text-emerald-400'
                                             : sentiment === 'negative'
                                             ? 'text-red-400'
                                             : sentiment === 'critical'
                                             ? 'text-orange-400'
                                             : 'text-gray-400'
                                       } font-medium flex items-center gap-1`}
                                    >
                                       {getSentimentIcon(sentiment, 10)}
                                       <span>{formatPercentage(cat[sentiment], cat.total)}%</span>
                                    </div>
                                 </div>
                              </div>
                           </div>
                        ))}
                     </div>
                  </div>
               ))}
            </div>
         </div>
      </div>
   );
};

const SentimentAreaChart = ({ data, colorMap }) => (
   <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
         <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
               {Object.entries(colorMap).map(([key, color]) => (
                  <linearGradient key={key} id={`${key}Gradient`} x1="0" y1="0" x2="0" y2="1">
                     <stop offset="5%" stopColor={color} stopOpacity={0.5} />
                     <stop offset="95%" stopColor={color} stopOpacity={0} />
                  </linearGradient>
               ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border.medium} vertical={false} />
            <XAxis
               dataKey="date"
               stroke={COLORS.text.secondary}
               fontSize={9}
               tick={{ fill: COLORS.text.secondary }}
               axisLine={false}
               tickLine={false}
            />
            <YAxis
               stroke={COLORS.text.secondary}
               fontSize={9}
               tick={{ fill: COLORS.text.secondary }}
               tickFormatter={value => value.toLocaleString()}
               axisLine={false}
               tickLine={false}
            />
            <Tooltip
               content={<CustomTooltip />}
               cursor={{ stroke: 'rgba(255, 255, 255, 0.1)', strokeWidth: 1 }}
            />
            <Legend
               iconType="circle"
               iconSize={6}
               wrapperStyle={{ fontSize: '9px', color: COLORS.text.secondary }}
            />
            {Object.keys(colorMap).map((sentiment, index) => (
               <Area
                  key={sentiment}
                  type="monotone"
                  dataKey={sentiment}
                  stackId="1"
                  stroke={colorMap[sentiment]}
                  strokeWidth={2}
                  fill={`url(#${sentiment}Gradient)`}
                  name={sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                  animationDuration={ANALYTICS_CONFIG.ANIMATION_DURATION.CHART}
                  animationBegin={300 + index * 300}
               />
            ))}
         </AreaChart>
      </ResponsiveContainer>
   </div>
);

const InfluentialPostCard = React.memo(({ post, onPostClick, index }) => {
   const sentiment = post.sentiment || 'neutral';
   const platform = post.platform || 'web';
   const engagement = post.engagement || {};
   const replyCount = engagement.replies || 0;
   const retweetCount = engagement.retweets || 0;
   const likeCount = engagement.likes || 0;
   const viewCount = engagement.views || 0;
   const commentsCount = replyCount || 0;
   const likesCount = likeCount || 0;
   const sharesCount = retweetCount || 0;
   const hasVeryHighEngagement = commentsCount > 200 || sharesCount > 200 || likesCount > 1000;

   const handleClick = useCallback(() => onPostClick?.(post), [post, onPostClick]);
   const handleKeyDown = useCallback(
      e => {
         switch (e.key) {
            case 'Enter':
            case ' ':
               e.preventDefault();
               handleClick();
               break;
            case 'ArrowRight':
               const nextCard =
                  e.target?.parentElement?.nextElementSibling?.querySelector('[role="button"]');
               nextCard?.focus();
               break;
            case 'ArrowLeft':
               const prevCard =
                  e.target?.parentElement?.previousElementSibling?.querySelector('[role="button"]');
               prevCard?.focus();
               break;
            default:
               break;
         }
      },
      [handleClick]
   );

   return (
      <div
         role="button"
         tabIndex={0}
         className="block h-full cursor-pointer transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 rounded-lg"
         onClick={handleClick}
         onKeyDown={handleKeyDown}
         aria-label={`Post ${index + 1}: ${
            post.user_display_name || 'Unknown author'
         }, ${sentiment} sentiment. Press Enter to view details.`}
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
                                 getPlatformColor(platform).split('-')[1]
                              } group-hover:text-opacity-90 transition-colors duration-300`}
                           >
                              {getPlatformIcon(platform)}
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
                        platform
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
});

const getInitialDateRange = () => {
   const endDate = new Date();
   const startDate = new Date();
   startDate.setDate(startDate.getDate() - ANALYTICS_CONFIG.DEFAULT_DATE_RANGE_DAYS);
   return {
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
   };
};

const StatsTab = ({ platforms, onPostClick }) => {
   const [dateRange, setDateRange] = useState(getInitialDateRange());
   const { data, loading, errors, refetch } = useAnalyticsData(dateRange, platforms);
   const announce = useScreenReaderAnnouncement();
   const sentimentColorMap = useMemo(
      () => ({
         positive: COLORS.positive,
         negative: COLORS.negative,
         critical: COLORS.critical,
         neutral: COLORS.neutral,
      }),
      []
   );

   const debouncedDateChange = useDebouncedCallback(newDateRange => {
      setDateRange(newDateRange);
      announce(
         `Analytics data updated for ${formatDate(newDateRange.startDate, 'long')} to ${formatDate(
            newDateRange.endDate,
            'long'
         )}`
      );
   }, ANALYTICS_CONFIG.API_DEBOUNCE_MS);
   const handleDateRangeChange = useCallback(
      newDateRange => {
         debouncedDateChange(newDateRange);
      },
      [debouncedDateChange]
   );
   if (loading) return <LoadingSpinner />;

   return (
      <div className="space-y-5">
         <DateRangeFilter onDateRangeChange={handleDateRangeChange} initialDateRange={dateRange} />
         <ErrorBoundary errors={errors} onRetry={refetch}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
               <AnalyticsCard
                  title="Sentiment Distribution"
                  icon={<PieChartIcon size={16} className="text-emerald-400" />}
                  className="md:col-span-1"
               >
                  {data.sentimentData.length > 0 ? (
                     <SentimentPieChart data={data.sentimentData} colorMap={sentimentColorMap} />
                  ) : (
                     <ChartSkeleton height="h-56" />
                  )}
               </AnalyticsCard>
               <AnalyticsCard
                  title="Categories by Sentiment"
                  icon={<BarChart2 size={16} className="text-emerald-400" />}
                  className="md:col-span-2"
               >
                  {data.categorySentiment.length > 0 ? (
                     <CategoryHeatmap data={data.categorySentiment} />
                  ) : (
                     <ChartSkeleton />
                  )}
               </AnalyticsCard>
            </div>
            <AnalyticsCard
               title="Sentiment Trends Over Time"
               icon={<Calendar size={16} className="text-emerald-400" />}
            >
               {data.sentimentOverTime.length > 0 ? (
                  <SentimentAreaChart data={data.sentimentOverTime} colorMap={sentimentColorMap} />
               ) : (
                  <ChartSkeleton />
               )}
            </AnalyticsCard>
            <AnalyticsCards
               userSentiment={data.userSentiment}
               trendingTopics={data.trendingTopics}
               loading={loading}
            />
            <AnalyticsCard
               title="Most Influential Posts"
               icon={<TrendingUp size={16} className="text-emerald-400" />}
            >
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 max-h-[32rem] overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800">
                  {data.influentialPosts.length > 0
                     ? data.influentialPosts.map((post, index) => (
                          <InfluentialPostCard
                             key={post.post_id}
                             post={post}
                             onPostClick={onPostClick}
                             index={index}
                          />
                       ))
                     : Array.from({ length: 4 }, (_, i) => <PostCardSkeleton key={i} />)}
               </div>
            </AnalyticsCard>
            <div
               className="h-0.5 w-full bg-gradient-to-r from-emerald-600/0 via-emerald-500/30 to-emerald-600/0 rounded-full animate-pulse"
               style={{ animationDuration: '3s' }}
            ></div>
         </ErrorBoundary>
      </div>
   );
};

export default StatsTab;
