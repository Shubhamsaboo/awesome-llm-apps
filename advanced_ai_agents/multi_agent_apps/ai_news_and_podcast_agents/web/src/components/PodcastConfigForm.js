import React, { useState, useEffect } from 'react';
import api from '../services/api';

const PodcastConfigForm = ({ config = null, onSubmit, onCancel }) => {
   const [name, setName] = useState('');
   const [description, setDescription] = useState('');
   const [prompt, setPrompt] = useState('');
   const [podcastScriptPrompt, setPodcastScriptPrompt] = useState('');
   const [imagePrompt, setImagePrompt] = useState('');
   const [timeRangeHours, setTimeRangeHours] = useState(24);
   const [limitArticles, setLimitArticles] = useState(20);
   const [ttsEngine, setTtsEngine] = useState('elevenlabs');
   const [languageCode, setLanguageCode] = useState('en');
   const [isActive, setIsActive] = useState(true);
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState(null);
   const [ttsEngines, setTtsEngines] = useState([]);
   const [languageCodes, setLanguageCodes] = useState([]);
   const [loadingOptions, setLoadingOptions] = useState(true);

   useEffect(() => {
      const fetchOptions = async () => {
         setLoadingOptions(true);
         try {
            const ttsResponse = await api.podcastConfigs.getTtsEngines();
            setTtsEngines(ttsResponse.data || []);
            const langResponse = await api.podcastConfigs.getLanguageCodes();
            setLanguageCodes(langResponse.data || []);
         } catch (err) {
            setError('Failed to load options for TTS engines and languages');
         } finally {
            setLoadingOptions(false);
         }
      };

      fetchOptions();
   }, []);

   useEffect(() => {
      if (config) {
         setName(config.name || '');
         setDescription(config.description || '');
         setPrompt(config.prompt || '');
         setPodcastScriptPrompt(config.podcast_script_prompt || '');
         setImagePrompt(config.image_prompt || '');
         setTimeRangeHours(config.time_range_hours || 24);
         setLimitArticles(config.limit_articles || 20);
         setTtsEngine(config.tts_engine || '');
         setLanguageCode(config.language_code || '');
         setIsActive(config.is_active !== undefined ? config.is_active : true);
      }
   }, [config]);

   const handleSubmit = async e => {
      e.preventDefault();
      setLoading(true);
      setError(null);
      try {
         if (!name.trim()) {
            throw new Error('Name is required');
         }
         if (!prompt.trim()) {
            throw new Error('Search prompt is required');
         }
         const configData = {
            name,
            description,
            prompt,
            podcast_script_prompt: podcastScriptPrompt,
            image_prompt: imagePrompt,
            time_range_hours: parseInt(timeRangeHours),
            limit_articles: parseInt(limitArticles),
            tts_engine: ttsEngine,
            language_code: languageCode,
            is_active: isActive,
         };
         await onSubmit(configData);
      } catch (err) {
         let errorMessage = 'Failed to save podcast configuration';
         if (err.response && err.response.data) {
            if (err.response.data.detail) {
               errorMessage = err.response.data.detail;
            } else if (typeof err.response.data === 'string') {
               errorMessage = err.response.data;
            }
         } else if (err.message) {
            errorMessage = err.message;
         }
         setError(errorMessage);
      } finally {
         setLoading(false);
      }
   };

   return (
      <form onSubmit={handleSubmit} className="space-y-4">
         {error && (
            <div className="bg-gradient-to-r from-red-900 to-red-800 text-red-300 p-3 rounded-sm">
               {error}
            </div>
         )}
         <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
               Configuration Name <span className="text-red-400">*</span>
            </label>
            <input
               type="text"
               id="name"
               value={name}
               onChange={e => setName(e.target.value)}
               required
               className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               placeholder="Daily Tech News Podcast"
            />
         </div>
         <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-1">
               Description
            </label>
            <textarea
               id="description"
               value={description}
               onChange={e => setDescription(e.target.value)}
               rows="2"
               className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               placeholder="Daily podcast covering the latest in technology news"
            />
         </div>
         <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-300 mb-1">
               Search Prompt <span className="text-red-400">*</span>
            </label>
            <textarea
               id="prompt"
               value={prompt}
               onChange={e => setPrompt(e.target.value)}
               rows="3"
               required
               className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               placeholder="Latest tech news about AI, cloud computing, and cybersecurity"
            />
            <p className="mt-1 text-xs text-gray-400">
               This prompt is used to search for relevant articles to include in the podcast.
            </p>
         </div>
         <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
               <label
                  htmlFor="timeRangeHours"
                  className="block text-sm font-medium text-gray-300 mb-1"
               >
                  Time Range (hours)
               </label>
               <input
                  type="number"
                  id="timeRangeHours"
                  value={timeRangeHours}
                  onChange={e => setTimeRangeHours(e.target.value)}
                  min="1"
                  max="168"
                  className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               />
               <p className="mt-1 text-xs text-gray-400">
                  How far back to look for articles (1-168 hours)
               </p>
            </div>
            <div>
               <label
                  htmlFor="limitArticles"
                  className="block text-sm font-medium text-gray-300 mb-1"
               >
                  Article Limit
               </label>
               <input
                  type="number"
                  id="limitArticles"
                  value={limitArticles}
                  onChange={e => setLimitArticles(e.target.value)}
                  min="5"
                  max="50"
                  className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               />
               <p className="mt-1 text-xs text-gray-400">
                  Maximum number of articles to include (5-50)
               </p>
            </div>
         </div>
         <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
               <label htmlFor="ttsEngine" className="block text-sm font-medium text-gray-300 mb-1">
                  TTS Engine
               </label>
               <select
                  id="ttsEngine"
                  value={ttsEngine}
                  onChange={e => setTtsEngine(e.target.value)}
                  className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                  disabled={loadingOptions}
               >
                  {loadingOptions ? (
                     <option value="">Loading...</option>
                  ) : (
                     ttsEngines.map(engine => (
                        <option key={engine} value={engine}>
                           {engine}
                        </option>
                     ))
                  )}
               </select>
            </div>
            <div>
               <label
                  htmlFor="languageCode"
                  className="block text-sm font-medium text-gray-300 mb-1"
               >
                  Language
               </label>
               <select
                  id="languageCode"
                  value={languageCode}
                  onChange={e => setLanguageCode(e.target.value)}
                  className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
                  disabled={loadingOptions}
               >
                  {loadingOptions ? (
                     <option value="">Loading...</option>
                  ) : (
                     languageCodes.map(lang => (
                        <option key={lang} value={lang}>
                           {lang}
                        </option>
                     ))
                  )}
               </select>
            </div>
         </div>
         <div>
            <label
               htmlFor="podcastScriptPrompt"
               className="block text-sm font-medium text-gray-300 mb-1"
            >
               Custom Podcast Script Prompt <span className="text-gray-500">(optional)</span>
            </label>
            <textarea
               id="podcastScriptPrompt"
               value={podcastScriptPrompt}
               onChange={e => setPodcastScriptPrompt(e.target.value)}
               rows="4"
               className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               placeholder="Custom prompt to guide the podcast script generation. Leave empty to use default."
            />
            <p className="mt-1 text-xs text-gray-400">
               Advanced: Custom prompt to override the default podcast script generation
               instructions.
            </p>
         </div>
         <div>
            <label htmlFor="imagePrompt" className="block text-sm font-medium text-gray-300 mb-1">
               Custom Image Prompt <span className="text-gray-500">(optional)</span>
            </label>
            <textarea
               id="imagePrompt"
               value={imagePrompt}
               onChange={e => setImagePrompt(e.target.value)}
               rows="2"
               className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               placeholder="Custom prompt for the podcast banner image generation. Leave empty to use default."
            />
            <p className="mt-1 text-xs text-gray-400">
               Advanced: Custom prompt to override the default podcast banner image generation.
            </p>
         </div>
         <div className="flex items-center">
            <input
               type="checkbox"
               id="isActive"
               checked={isActive}
               onChange={e => setIsActive(e.target.checked)}
               className="h-4 w-4 text-emerald-600 bg-gray-900 border-gray-700 rounded focus:ring-emerald-500 focus:ring-offset-gray-900"
            />
            <label htmlFor="isActive" className="ml-2 block text-sm text-gray-300">
               Active (will be processed by podcast generator)
            </label>
         </div>
         <div className="flex justify-end space-x-3 pt-4">
            <button
               type="button"
               onClick={onCancel}
               className="px-4 py-2 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-gray-300 rounded-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-sm transition-colors duration-200"
            >
               Cancel
            </button>
            <button
               type="submit"
               disabled={loading || loadingOptions}
               className="px-4 py-2 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-sm transition-colors duration-200 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
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
               {config ? 'Update Configuration' : 'Create Configuration'}
            </button>
         </div>
      </form>
   );
};

export default PodcastConfigForm;
