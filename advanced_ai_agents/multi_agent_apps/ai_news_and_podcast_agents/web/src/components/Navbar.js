import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';

const Navbar = () => {
   const location = useLocation();
   const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
   const isActive = path => location.pathname === path || location.pathname.startsWith(`${path}/`);

   return (
      <nav className="bg-black border-b border-gray-800 shadow-md relative overflow-hidden">
         <div
            className="absolute inset-0 opacity-5"
            style={{
               backgroundImage:
                  'repeating-linear-gradient(45deg, #333 0, #333 1px, transparent 0, transparent 10px)',
               zIndex: 0,
            }}
         ></div>
         <div className="container mx-auto px-4 relative z-10">
            <div className="flex justify-between items-center h-16">
               <div className="flex-shrink-0 flex items-center">
                  <div className="relative mr-2 group">
                     <span
                        className="text-2xl filter drop-shadow-lg"
                        style={{
                           textShadow: '0 0 10px rgba(16, 185, 129, 0.5)',
                           fontSize: '1.75rem',
                        }}
                     >
                        🦉
                     </span>
                     <span className="absolute -inset-1 bg-emerald-500 rounded-full blur-md opacity-0 group-hover:opacity-20 transition-opacity duration-300"></span>
                  </div>
                  <Link to="/" className="relative group">
                     <span className="text-xl font-bold text-gray-100">
                        <span className="text-emerald-400">Bei</span>fong
                     </span>
                     <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-emerald-400 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></span>
                     <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-emerald-400 blur-sm opacity-70 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></span>
                  </Link>
               </div>
               <div className="md:hidden">
                  <button
                     onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                     className="text-gray-400 hover:text-gray-200 focus:outline-none"
                  >
                     <svg
                        className="w-6 h-6"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                     >
                        <path
                           strokeLinecap="round"
                           strokeLinejoin="round"
                           strokeWidth={2}
                           d="M4 6h16M4 12h16M4 18h16"
                        />
                     </svg>
                  </button>
               </div>
               <div className="hidden md:block">
                  <div className="ml-10 flex items-baseline space-x-4">
                     <Link
                        to="/"
                        className={`px-3 py-2 text-sm font-medium relative ${
                           isActive('/')
                              ? 'text-gray-200 border-b-2 border-emerald-400'
                              : 'text-gray-400 hover:text-gray-200 border-b-2 border-transparent hover:border-gray-700'
                        } transition-colors duration-200`}
                     >
                        Home
                        {isActive('/') && (
                           <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-emerald-400 blur-sm opacity-70"></span>
                        )}
                     </Link>
                     <Link
                        to="/articles"
                        className={`px-3 py-2 text-sm font-medium relative ${
                           isActive('/articles')
                              ? 'text-gray-200 border-b-2 border-emerald-400'
                              : 'text-gray-400 hover:text-gray-200 border-b-2 border-transparent hover:border-gray-700'
                        } transition-colors duration-200`}
                     >
                        Articles
                        {isActive('/articles') && (
                           <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-emerald-400 blur-sm opacity-70"></span>
                        )}
                     </Link>
                     <Link
                        to="/podcasts"
                        className={`px-3 py-2 text-sm font-medium relative ${
                           isActive('/podcasts')
                              ? 'text-gray-200 border-b-2 border-emerald-400'
                              : 'text-gray-400 hover:text-gray-200 border-b-2 border-transparent hover:border-gray-700'
                        } transition-colors duration-200`}
                     >
                        Podcasts
                        {isActive('/podcasts') && (
                           <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-emerald-400 blur-sm opacity-70"></span>
                        )}
                     </Link>
                     <Link
                        to="/studio"
                        className={`px-3 py-2 text-sm font-medium relative ${
                           isActive('/studio')
                              ? 'text-gray-200 border-b-2 border-emerald-400'
                              : 'text-gray-400 hover:text-gray-200 border-b-2 border-transparent hover:border-gray-700'
                        } transition-colors duration-200`}
                     >
                        Studio
                        {isActive('/studio') && (
                           <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-emerald-400 blur-sm opacity-70"></span>
                        )}
                     </Link>
                     <Link
                        to="/social-media"
                        className={`px-3 py-2 text-sm font-medium relative ${
                           isActive('/social-media')
                              ? 'text-gray-200 border-b-2 border-emerald-400'
                              : 'text-gray-400 hover:text-gray-200 border-b-2 border-transparent hover:border-gray-700'
                        } transition-colors duration-200`}
                     >
                        Social
                        {isActive('/social-media') && (
                           <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-emerald-400 blur-sm opacity-70"></span>
                        )}
                     </Link>
                     <Link
                        to="/voyager"
                        className={`px-3 py-2 text-sm font-medium relative ${
                           isActive('/voyager')
                              ? 'text-gray-200 border-b-2 border-emerald-400'
                              : 'text-gray-400 hover:text-gray-200 border-b-2 border-transparent hover:border-gray-700'
                        } transition-colors duration-200`}
                     >
                        Voyager
                        {isActive('/voyager') && (
                           <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-emerald-400 blur-sm opacity-70"></span>
                        )}
                     </Link>
                     <Link
                        to="/sources"
                        className={`px-3 py-2 text-sm font-medium relative ${
                           isActive('/sources')
                              ? 'text-gray-200 border-b-2 border-emerald-400'
                              : 'text-gray-400 hover:text-gray-200 border-b-2 border-transparent hover:border-gray-700'
                        } transition-colors duration-200`}
                     >
                        Sources
                        {isActive('/sources') && (
                           <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-emerald-400 blur-sm opacity-70"></span>
                        )}
                     </Link>
                  </div>
               </div>
            </div>
         </div>
         <div
            className={`fixed inset-0 bg-black z-50 flex flex-col items-center justify-center transition-opacity duration-300 ${
               isMobileMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
         >
            <button
               onClick={() => setIsMobileMenuOpen(false)}
               className="absolute top-4 right-4 text-gray-400 hover:text-gray-200"
            >
               <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
               >
                  <path
                     strokeLinecap="round"
                     strokeLinejoin="round"
                     strokeWidth={2}
                     d="M6 18L18 6M6 6l12 12"
                  />
               </svg>
            </button>
            <div className="flex flex-col space-y-6 text-center">
               <Link
                  to="/"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`text-lg ${isActive('/') ? 'text-emerald-400' : 'text-gray-200'}`}
               >
                  Home
               </Link>
               <Link
                  to="/articles"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`text-lg ${
                     isActive('/articles') ? 'text-emerald-400' : 'text-gray-200'
                  }`}
               >
                  Articles
               </Link>
               <Link
                  to="/podcasts"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`text-lg ${
                     isActive('/podcasts') ? 'text-emerald-400' : 'text-gray-200'
                  }`}
               >
                  Podcasts
               </Link>
               <Link
                  to="/studio"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`text-lg ${
                     isActive('/studio') ? 'text-emerald-400' : 'text-gray-200'
                  }`}
               >
                  Studio
               </Link>
               <Link
                  to="/social-media"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`text-lg ${
                     isActive('/social-media') ? 'text-emerald-400' : 'text-gray-200'
                  }`}
               >
                  Social
               </Link>
               <Link
                  to="/voyager"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`text-lg ${
                     isActive('/voyager') ? 'text-emerald-400' : 'text-gray-200'
                  }`}
               >
                  Voyager
               </Link>
               <Link
                  to="/sources"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`text-lg ${
                     isActive('/sources') ? 'text-emerald-400' : 'text-gray-200'
                  }`}
               >
                  Sources
               </Link>
            </div>
         </div>
      </nav>
   );
};

export default Navbar;
