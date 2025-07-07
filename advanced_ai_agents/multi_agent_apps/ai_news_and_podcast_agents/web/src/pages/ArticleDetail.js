import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

const ArticleDetail = () => {
   const { articleId } = useParams();
   const navigate = useNavigate();
   const [article, setArticle] = useState(null);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [isExpanded, setIsExpanded] = useState(false);
   const CHAR_LIMIT = 500;

   useEffect(() => {
      const fetchArticleDetail = async () => {
         setLoading(true);
         setError(null);
         try {
            const response = await api.articles.getById(articleId);
            setArticle(response.data);
         } catch (err) {
            setError('Failed to fetch article: ' + (err.response?.data?.detail || err.message));
         } finally {
            setLoading(false);
         }
      };
      fetchArticleDetail();
   }, [articleId]);

   const handleGoBack = () => {
      navigate(-1);
   };

   const truncateHtml = (html, limit) => {
      if (!html) return '';
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;
      const textContent = tempDiv.textContent || tempDiv.innerText;
      if (textContent.length <= limit) {
         return html;
      }
      return textContent.substring(0, limit) + '...';
   };

   const renderCategories = categories => {
      if (!categories || !Array.isArray(categories) || categories.length === 0) {
         return null;
      }
      return (
         <div className="flex flex-wrap gap-2 mt-3">
            {categories.map((category, index) => (
               <span
                  key={index}
                  className="px-2 py-1 bg-gray-800 text-emerald-300 rounded-sm text-xs font-medium border border-gray-700"
               >
                  {category}
               </span>
            ))}
         </div>
      );
   };

   if (loading) {
      return (
         <div className="max-w-3xl mx-auto py-16 text-center">
            <div className="w-12 h-12 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-400">Loading article...</p>
         </div>
      );
   }

   if (error) {
      return (
         <div className="max-w-3xl mx-auto py-8">
            <div className="bg-gray-800 border-l-4 border-red-500 p-4 rounded-sm mb-6 text-red-400">
               {error}
            </div>
            <button
               onClick={handleGoBack}
               className="text-gray-300 hover:text-emerald-300 flex items-center transition-colors duration-200"
            >
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 mr-2"
                  viewBox="0 0 20 20"
                  fill="currentColor"
               >
                  <path
                     fillRule="evenodd"
                     d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                     clipRule="evenodd"
                  />
               </svg>
               Back to articles
            </button>
         </div>
      );
   }

   if (!article) {
      return (
         <div className="max-w-3xl mx-auto py-8">
            <div className="bg-gray-800 border-l-4 border-yellow-500 p-4 rounded-sm mb-6 text-yellow-300">
               Article not found
            </div>
            <Link
               to="/articles"
               className="text-gray-300 hover:text-emerald-300 flex items-center transition-colors duration-200"
            >
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 mr-2"
                  viewBox="0 0 20 20"
                  fill="currentColor"
               >
                  <path
                     fillRule="evenodd"
                     d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                     clipRule="evenodd"
                  />
               </svg>
               Back to articles
            </Link>
         </div>
      );
   }

   const shouldTruncate = article.content && !isExpanded;
   const contentToDisplay = shouldTruncate
      ? truncateHtml(article.content, CHAR_LIMIT)
      : article.content;

   return (
      <div className="max-w-3xl mx-auto py-8">
         <button
            onClick={handleGoBack}
            className="text-gray-300 hover:text-emerald-300 flex items-center mb-8 transition-colors duration-200 group"
         >
            <svg
               xmlns="http://www.w3.org/2000/svg"
               className="h-5 w-5 mr-2 group-hover:transform group-hover:-translate-x-1 transition-transform duration-200"
               viewBox="0 0 20 20"
               fill="currentColor"
            >
               <path
                  fillRule="evenodd"
                  d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                  clipRule="evenodd"
               />
            </svg>
            Back to articles
         </button>
         <article className="bg-gray-800 shadow-lg rounded-sm overflow-hidden">
            <div className="p-6 border-b border-gray-700">
               {article.source_name && (
                  <div className="mb-3">
                     <span className="px-3 py-1 bg-gray-900 text-emerald-300 rounded-sm text-sm font-medium">
                        {article.source_name}
                     </span>
                  </div>
               )}
               <h1 className="text-2xl font-medium text-gray-100 mb-4">{article.title}</h1>
               <div className="flex items-center text-sm text-gray-400 mb-1">
                  <span className="flex items-center">
                     <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4 mr-1 text-gray-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                     >
                        <path
                           strokeLinecap="round"
                           strokeLinejoin="round"
                           strokeWidth={2}
                           d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                     </svg>
                     <span>{new Date(article.published_date).toLocaleDateString()}</span>
                  </span>
                  {article.categories && article.categories.length > 0 && (
                     <div className="flex items-center ml-4">
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-4 w-4 mr-1 text-gray-500"
                           fill="none"
                           viewBox="0 0 24 24"
                           stroke="currentColor"
                        >
                           <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                           />
                        </svg>
                        <span>Categories</span>
                     </div>
                  )}
               </div>
               {renderCategories(article.categories)}
            </div>
            {article.summary && (
               <div className="px-6 py-5 bg-gray-750 border-b border-gray-700">
                  <h2 className="text-lg font-medium text-emerald-300 mb-3">Summary</h2>
                  <p className="text-gray-300 leading-relaxed">{article.summary}</p>
               </div>
            )}
            {article.content && (
               <div className="p-6">
                  <h2 className="text-lg font-medium text-emerald-300 mb-4">Content</h2>
                  <div className="text-gray-300 leading-relaxed">
                     {shouldTruncate ? (
                        <p className="mb-4">{contentToDisplay}</p>
                     ) : (
                        <div
                           dangerouslySetInnerHTML={{ __html: contentToDisplay }}
                           className="article-content"
                        ></div>
                     )}
                  </div>
                  {article.content.length > CHAR_LIMIT && (
                     <div className="mt-6">
                        {shouldTruncate ? (
                           <button
                              onClick={() => setIsExpanded(true)}
                              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-sm flex items-center transition-colors duration-200"
                           >
                              <svg
                                 xmlns="http://www.w3.org/2000/svg"
                                 className="h-5 w-5 mr-2"
                                 viewBox="0 0 20 20"
                                 fill="currentColor"
                              >
                                 <path
                                    fillRule="evenodd"
                                    d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                    clipRule="evenodd"
                                 />
                              </svg>
                              Show full content
                           </button>
                        ) : (
                           <button
                              onClick={() => setIsExpanded(false)}
                              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-sm flex items-center transition-colors duration-200"
                           >
                              <svg
                                 xmlns="http://www.w3.org/2000/svg"
                                 className="h-5 w-5 mr-2"
                                 viewBox="0 0 20 20"
                                 fill="currentColor"
                              >
                                 <path
                                    fillRule="evenodd"
                                    d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                                    clipRule="evenodd"
                                 />
                              </svg>
                              Show less
                           </button>
                        )}
                     </div>
                  )}
               </div>
            )}
            {article.url && (
               <div className="px-6 py-5 bg-gray-750 border-t border-gray-700">
                  <a
                     href={article.url}
                     target="_blank"
                     rel="noopener noreferrer"
                     className="inline-flex items-center px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-sm transition-colors duration-200"
                  >
                     <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5 mr-2"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                     >
                        <path
                           fillRule="evenodd"
                           d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z"
                           clipRule="evenodd"
                        />
                     </svg>
                     Read Full Article
                  </a>
               </div>
            )}
         </article>
         <style jsx>{`
            .article-content h1,
            .article-content h2,
            .article-content h3 {
               color: #8dd5c6;
               margin-top: 1.5em;
               margin-bottom: 0.75em;
               font-weight: 500;
            }

            .article-content h1 {
               font-size: 1.5rem;
               padding-bottom: 0.5rem;
               border-bottom: 1px solid #4b5563;
            }

            .article-content h2 {
               font-size: 1.25rem;
            }

            .article-content h3 {
               font-size: 1.125rem;
            }

            .article-content p {
               margin-bottom: 1rem;
               line-height: 1.6;
            }

            .article-content a {
               color: #10b981;
               text-decoration: underline;
            }

            .article-content ul,
            .article-content ol {
               margin: 1rem 0;
               padding-left: 1.5rem;
            }

            .article-content li {
               margin-bottom: 0.5rem;
            }

            .article-content blockquote {
               border-left: 3px solid #10b981;
               padding-left: 1rem;
               margin: 1rem 0;
               color: #9ca3af;
            }
         `}</style>
      </div>
   );
};

export default ArticleDetail;
