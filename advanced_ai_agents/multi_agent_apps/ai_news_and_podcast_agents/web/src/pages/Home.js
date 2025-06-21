import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BrainCircuit, ShieldCheck } from 'lucide-react';

const Home = () => {
   const [hoverArticles, setHoverArticles] = useState(false);
   const [hoverPodcasts, setHoverPodcasts] = useState(false);
   const [hoverSources, setHoverSources] = useState(false);
   const [hoverStudio, setHoverStudio] = useState(false);
   const [hoverVoyager, setHoverVoyager] = useState(false);
   const [hoverSocial, setHoverSocial] = useState(false);
   const [showWelcome, setShowWelcome] = useState(false);

   useEffect(() => {
      const timer = setTimeout(() => {
         setShowWelcome(true);
      }, 300);
      return () => clearTimeout(timer);
   }, []);

   const cardBaseClasses =
      'bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 p-4 rounded-sm hover:shadow-lg transition-all duration-300 transform hover:scale-[1.01] group relative overflow-hidden';
   const cardFlexContainerClasses = 'flex items-start mb-3';
   const cardIconContainerClasses = 'mr-3 text-emerald-400 transition-transform duration-300';
   const cardIconClasses = 'w-8 h-8';
   const cardTitleClasses =
      'text-base font-medium text-gray-200 mb-1 group-hover:text-emerald-300 transition-colors duration-200';
   const cardDescriptionClasses = 'text-sm text-gray-400 mb-3';
   const cardButtonClasses =
      'inline-block px-4 py-1.5 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white text-sm rounded-sm hover:shadow-md hover:shadow-emerald-900/50 transition-all duration-300';

   return (
      <div className="max-w-4xl mx-auto px-4 py-6">
         {' '}
         <div className="relative mb-6">
            {' '}
            <div className="flex items-center mb-2">
               <div className="h-10 w-10 text-emerald-500 mr-4 relative">
                  <svg
                     viewBox="0 0 24 24"
                     fill="none"
                     xmlns="http://www.w3.org/2000/svg"
                     className="absolute"
                  >
                     <path
                        d="M3 5a2 2 0 012-2h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5z"
                        stroke="currentColor"
                        strokeWidth="1.5"
                     />
                     <path
                        d="M8 6v12M16 6v12M3 12h18M8 12a1 1 0 100-2 1 1 0 000 2zM8 16a1 1 0 100-2 1 1 0 000 2zM16 12a1 1 0 100-2 1 1 0 000 2zM16 16a1 1 0 100-2 1 1 0 000 2z"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                     />
                  </svg>
                  <div className="absolute inset-0 bg-emerald-500 opacity-30 blur-md rounded-full"></div>
               </div>
               <h1 className="text-3xl font-medium text-gray-100 relative">
                  Hub
                  <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-500 to-transparent mt-1 opacity-60"></div>
               </h1>
            </div>
            <div
               className={`ml-14 text-gray-400 transition-opacity duration-700 ease-in-out ${
                  showWelcome ? 'opacity-100' : 'opacity-0'
               }`}
            >
               Welcome to Beifong's: Your Junk-Free, Personalized Informations and Podcasts.
            </div>
         </div>
         <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm relative overflow-hidden">
            <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
            <div
               className="absolute top-0 right-0 w-24 h-24 opacity-5"
               style={{
                  backgroundImage:
                     'repeating-linear-gradient(45deg, #10B981 0, #10B981 1px, transparent 0, transparent 8px)',
                  clipPath: 'polygon(100% 0, 70% 0, 100% 30%)', // Adjusted clip path
               }}
            ></div>
            <div className="p-4">
               {' '}
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div
                     className={cardBaseClasses}
                     onMouseEnter={() => setHoverArticles(true)}
                     onMouseLeave={() => setHoverArticles(false)}
                  >
                     <div className="absolute bottom-0 right-0 h-16 w-16 opacity-10">
                        {' '}
                        <svg
                           viewBox="0 0 100 100"
                           xmlns="http://www.w3.org/2000/svg"
                           fill="none"
                           stroke="currentColor"
                           className="text-emerald-500"
                        >
                           <path d="M10,30 L90,30" strokeWidth="1" />{' '}
                           <path d="M20,50 L80,50" strokeWidth="1" />{' '}
                           <path d="M30,70 L70,70" strokeWidth="1" />{' '}
                           <circle cx="20" cy="30" r="3" fill="currentColor" />{' '}
                           <circle cx="40" cy="50" r="3" fill="currentColor" />{' '}
                           <circle cx="60" cy="70" r="3" fill="currentColor" />
                        </svg>
                     </div>
                     <div className={cardFlexContainerClasses}>
                        <div
                           className={`${cardIconContainerClasses} ${
                              hoverArticles ? 'scale-110' : ''
                           }`}
                        >
                           <svg
                              className={cardIconClasses}
                              viewBox="0 0 24 24"
                              fill="none"
                              xmlns="http://www.w3.org/2000/svg"
                           >
                              <path d="M19 5V19H5V5H19ZM21 3H3V21H21V3Z" fill="currentColor" />{' '}
                              <path d="M7 7H12V12H7V7Z" fill="currentColor" />{' '}
                              <path d="M14 7H17V9H14V7Z" fill="currentColor" />{' '}
                              <path d="M14 10H17V12H14V10Z" fill="currentColor" />{' '}
                              <path d="M7 13H17V15H7V13Z" fill="currentColor" />{' '}
                              <path d="M7 16H17V18H7V16Z" fill="currentColor" />
                           </svg>
                        </div>
                        <div>
                           <h3 className={cardTitleClasses}>Browse Articles</h3>
                           <p className={cardDescriptionClasses}>
                              Latest articles from your curated sources.
                           </p>
                        </div>
                     </div>
                     <Link to="/articles" className={cardButtonClasses}>
                        View Articles
                     </Link>
                  </div>
                  <div
                     className={cardBaseClasses}
                     onMouseEnter={() => setHoverPodcasts(true)}
                     onMouseLeave={() => setHoverPodcasts(false)}
                  >
                     <div className="absolute bottom-0 right-0 h-16 w-16 opacity-10">
                        {' '}
                        <svg
                           viewBox="0 0 100 100"
                           xmlns="http://www.w3.org/2000/svg"
                           fill="none"
                           stroke="currentColor"
                           className="text-emerald-500"
                        >
                           <path
                              d="M10,30 Q25,10 40,30 Q55,50 70,30 Q85,10 100,30"
                              strokeWidth="1"
                           />{' '}
                           <path
                              d="M10,50 Q25,30 40,50 Q55,70 70,50 Q85,30 100,50"
                              strokeWidth="1"
                           />{' '}
                           <path
                              d="M10,70 Q25,50 40,70 Q55,90 70,70 Q85,50 100,70"
                              strokeWidth="1"
                           />
                        </svg>
                     </div>
                     <div className={cardFlexContainerClasses}>
                        <div
                           className={`${cardIconContainerClasses} ${
                              hoverPodcasts ? 'scale-110' : ''
                           }`}
                        >
                           <svg
                              className={cardIconClasses}
                              viewBox="0 0 24 24"
                              fill="none"
                              xmlns="http://www.w3.org/2000/svg"
                           >
                              <path
                                 d="M12 1C8.14 1 5 4.14 5 8V11C5 14.86 8.14 18 12 18C15.86 18 19 14.86 19 11V8C19 4.14 15.86 1 12 1Z"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                              />{' '}
                              <path
                                 d="M12 18V23"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                              />{' '}
                              <path
                                 d="M8 23H16"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                              />{' '}
                              <path
                                 d="M13.5 6.5C13.5 7.33 12.83 8 12 8C11.17 8 10.5 7.33 10.5 6.5C10.5 5.67 11.17 5 12 5C12.83 5 13.5 5.67 13.5 6.5Z"
                                 fill="currentColor"
                              />{' '}
                              <path
                                 d="M16 11V11.25C16 13.32 14.32 15 12.25 15H11.75C9.68 15 8 13.32 8 11.25V11"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                              />
                           </svg>
                        </div>
                        <div>
                           <h3 className={cardTitleClasses}>Listen to Podcasts</h3>
                           <p className={cardDescriptionClasses}>
                              Podcasts from your curated sources.
                           </p>{' '}
                        </div>
                     </div>
                     <Link to="/podcasts" className={cardButtonClasses}>
                        Browse Podcasts
                     </Link>
                  </div>

                  <div
                     className={cardBaseClasses}
                     onMouseEnter={() => setHoverStudio(true)}
                     onMouseLeave={() => setHoverStudio(false)}
                  >
                     <div className="absolute bottom-0 right-0 h-16 w-16 opacity-10">
                        {' '}
                        <svg
                           viewBox="0 0 100 100"
                           xmlns="http://www.w3.org/2000/svg"
                           fill="none"
                           stroke="currentColor"
                           className="text-emerald-500"
                        >
                           <rect x="20" y="20" width="60" height="60" rx="5" strokeWidth="1" />{' '}
                           <line
                              x1="35"
                              y1="30"
                              x2="35"
                              y2="70"
                              strokeWidth="3"
                              strokeLinecap="round"
                           />{' '}
                           <line
                              x1="50"
                              y1="30"
                              x2="50"
                              y2="70"
                              strokeWidth="3"
                              strokeLinecap="round"
                           />{' '}
                           <line
                              x1="65"
                              y1="30"
                              x2="65"
                              y2="70"
                              strokeWidth="3"
                              strokeLinecap="round"
                           />{' '}
                           <circle cx="35" cy="40" r="4" fill="currentColor" />{' '}
                           <circle cx="50" cy="60" r="4" fill="currentColor" />{' '}
                           <circle cx="65" cy="50" r="4" fill="currentColor" />
                        </svg>
                     </div>
                     <div className={cardFlexContainerClasses}>
                        <div
                           className={`${cardIconContainerClasses} ${
                              hoverStudio ? 'scale-110' : ''
                           }`}
                        >
                           <svg
                              className={cardIconClasses}
                              viewBox="0 0 24 24"
                              fill="none"
                              xmlns="http://www.w3.org/2000/svg"
                           >
                              <path
                                 d="M5 3H19C20.1046 3 21 3.89543 21 5V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3Z"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                              />{' '}
                              <path
                                 d="M8 8V16"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                              />{' '}
                              <path
                                 d="M12 8V16"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                              />{' '}
                              <path
                                 d="M16 8V16"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                              />{' '}
                              <circle cx="8" cy="11" r="1.5" fill="currentColor" />{' '}
                              <circle cx="12" cy="13" r="1.5" fill="currentColor" />{' '}
                              <circle cx="16" cy="9" r="1.5" fill="currentColor" />
                           </svg>
                        </div>
                        <div>
                           <h3 className={cardTitleClasses}>Studio</h3>
                           <p className={cardDescriptionClasses}>
                              Craft custom podcast from your sources.
                           </p>{' '}
                        </div>
                     </div>
                     <Link to="/studio" className={cardButtonClasses}>
                        Open Studio
                     </Link>
                  </div>
                  <div
                     className={cardBaseClasses}
                     onMouseEnter={() => setHoverVoyager(true)}
                     onMouseLeave={() => setHoverVoyager(false)}
                  >
                     <div className="absolute bottom-0 right-0 h-16 w-16 opacity-10">
                        {' '}
                        <svg
                           viewBox="0 0 100 100"
                           xmlns="http://www.w3.org/2000/svg"
                           fill="none"
                           stroke="currentColor"
                           className="text-emerald-500"
                        >
                           <circle cx="50" cy="50" r="35" strokeWidth="1" />{' '}
                           <path d="M30 70 A 35 35 0 0 1 70 70" strokeWidth="1" />{' '}
                           <line
                              x1="50"
                              y1="50"
                              x2="35"
                              y2="35"
                              strokeWidth="2"
                              strokeLinecap="round"
                           />{' '}
                           <circle cx="50" cy="50" r="5" fill="currentColor" />
                        </svg>
                     </div>
                     <div className={cardFlexContainerClasses}>
                        <div
                           className={`${cardIconContainerClasses} ${
                              hoverVoyager ? 'scale-110' : ''
                           }`}
                        >
                           <svg
                              className="w-10 h-10 text-emerald-500 relative z-10"
                              viewBox="0 0 100 100"
                              fill="none"
                              xmlns="http://www.w3.org/2000/svg"
                              stroke="currentColor"
                              strokeWidth="4.5"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                           >
                              <circle cx="50" cy="50" r="35" />
                              <path d="M30 70 A 35 35 0 0 1 70 70" />
                              <line x1="50" y1="50" x2="35" y2="35" strokeWidth="1.5" />
                              <circle cx="50" cy="50" r="5" fill="currentColor" />
                           </svg>
                        </div>
                        <div>
                           <h3 className={cardTitleClasses}>Voyager</h3>
                           <p className={cardDescriptionClasses}>
                              Monitor system processes, manage tasks etc...
                           </p>
                        </div>
                     </div>
                     <Link to="/voyager" className={cardButtonClasses}>
                        Launch Voyager
                     </Link>
                  </div>

                  <div
                     className={cardBaseClasses}
                     onMouseEnter={() => setHoverSocial(true)}
                     onMouseLeave={() => setHoverSocial(false)}
                  >
                     <div className="absolute bottom-0 right-0 h-16 w-16 opacity-10">
                        <BrainCircuit
                           strokeWidth={0.7}
                           className="w-3/4 h-3/4 text-emerald-500"
                        />
                     </div>
                     <div className={cardFlexContainerClasses}>
                        <div
                           className={`${cardIconContainerClasses} ${
                              hoverSocial ? 'scale-110' : ''
                           }`}
                        >
                           <ShieldCheck className={cardIconClasses} />
                        </div>
                        <div>
                           <h3 className={cardTitleClasses}>Social</h3>
                           <p className={cardDescriptionClasses}>
                              Monitor and analyze your social media accounts.
                           </p>
                        </div>
                     </div>
                     <Link to="/social-media" className={cardButtonClasses}>
                        Your Social
                     </Link>
                  </div>

                  <div
                     className={cardBaseClasses}
                     onMouseEnter={() => setHoverSources(true)}
                     onMouseLeave={() => setHoverSources(false)}
                  >
                     <div className="absolute bottom-0 right-0 h-23 w-23 opacity-10">
                        {' '}
                        <svg
                           viewBox="0 0 100 100"
                           xmlns="http://www.w3.org/2000/svg"
                           fill="none"
                           stroke="currentColor"
                           className="text-emerald-500"
                        >
                           <circle cx="30" cy="30" r="8" strokeWidth="1" />{' '}
                           <circle cx="70" cy="30" r="8" strokeWidth="1" />{' '}
                           <circle cx="30" cy="70" r="8" strokeWidth="1" />{' '}
                           <circle cx="70" cy="70" r="8" strokeWidth="1" />{' '}
                           <circle cx="50" cy="50" r="10" strokeWidth="1" />{' '}
                           <line x1="30" y1="30" x2="70" y2="30" strokeWidth="1" />{' '}
                           <line x1="30" y1="30" x2="30" y2="70" strokeWidth="1" />{' '}
                           <line x1="30" y1="70" x2="70" y2="70" strokeWidth="1" />{' '}
                           <line x1="70" y1="30" x2="70" y2="70" strokeWidth="1" />{' '}
                           <line x1="30" y1="30" x2="50" y2="50" strokeWidth="1" />{' '}
                           <line x1="70" y1="30" x2="50" y2="50" strokeWidth="1" />{' '}
                           <line x1="30" y1="70" x2="50" y2="50" strokeWidth="1" />{' '}
                           <line x1="70" y1="70" x2="50" y2="50" strokeWidth="1" />
                        </svg>
                     </div>
                     <div className={cardFlexContainerClasses}>
                        <div
                           className={`${cardIconContainerClasses} ${
                              hoverSources ? 'scale-110' : ''
                           }`}
                        >
                           <svg
                              className={cardIconClasses}
                              viewBox="0 0 24 24"
                              fill="none"
                              xmlns="http://www.w3.org/2000/svg"
                           >
                              <path
                                 d="M12 8C16.4183 8 20 6.65685 20 5C20 3.34315 16.4183 2 12 2C7.58172 2 4 3.34315 4 5C4 6.65685 7.58172 8 12 8Z"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                              />{' '}
                              <path
                                 d="M4 5V12C4 13.66 7.58 15 12 15C16.42 15 20 13.66 20 12V5"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                              />{' '}
                              <path
                                 d="M4 12V19C4 20.66 7.58 22 12 22C16.42 22 20 20.66 20 19V12"
                                 stroke="currentColor"
                                 strokeWidth="1.5"
                                 strokeLinecap="round"
                                 strokeLinejoin="round"
                              />
                           </svg>
                        </div>
                        <div>
                           <h3 className={cardTitleClasses}>Manage Sources</h3>
                           <p className={cardDescriptionClasses}>
                              Organize content sources, settings etc...
                           </p>{' '}
                        </div>
                     </div>
                     <Link to="/sources" className={cardButtonClasses}>
                        Manage Sources
                     </Link>
                  </div>
               </div>{' '}
            </div>{' '}
         </div>{' '}
      </div>
   );
};

export default Home;
