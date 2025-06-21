import React from 'react';

const Pagination = ({ 
   pagination, 
   handlePrevPage, 
   handleNextPage, 
   setPagination 
}) => {
   return (
      <div className="mt-6 flex items-center justify-between bg-gradient-to-r from-gray-800 to-gray-900 p-3 rounded-sm border-t border-gray-700 shadow-lg">
         <div className="flex items-center text-xs text-gray-400">
            Showing{' '}
            <span className="font-medium text-gray-300 px-1">{pagination.perPage}</span> of{' '}
            <span className="font-medium text-gray-300 px-1">{pagination.total}</span>{' '}
            results
         </div>
         <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-end">
            <nav
               className="inline-flex -space-x-px rounded-sm shadow-sm"
               aria-label="Pagination"
            >
               <button
                  onClick={() => setPagination(prev => ({ ...prev, page: 1 }))}
                  disabled={pagination.page === 1}
                  className={`relative inline-flex items-center rounded-l-sm px-2 py-1 ${
                     pagination.page > 1
                        ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                        : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-600 border border-gray-700 cursor-not-allowed opacity-70'
                  } transition-colors duration-200`}
               >
                  <span className="sr-only">First</span>
                  <svg
                     xmlns="http://www.w3.org/2000/svg"
                     className="h-5 w-5"
                     viewBox="0 0 20 20"
                     fill="currentColor"
                  >
                     <path
                        fillRule="evenodd"
                        d="M15.707 15.707a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 010 1.414zm-6 0a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 1.414L5.414 10l4.293 4.293a1 1 0 010 1.414z"
                        clipRule="evenodd"
                     />
                  </svg>
               </button>
               <button
                  onClick={handlePrevPage}
                  disabled={pagination.page === 1}
                  className={`relative inline-flex items-center px-2 py-1 ${
                     pagination.page > 1
                        ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                        : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-600 border border-gray-700 cursor-not-allowed opacity-70'
                  } transition-colors duration-200`}
               >
                  <span className="sr-only">Previous</span>
                  <svg
                     className="h-5 w-5"
                     xmlns="http://www.w3.org/2000/svg"
                     viewBox="0 0 20 20"
                     fill="currentColor"
                     aria-hidden="true"
                  >
                     <path
                        fillRule="evenodd"
                        d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
                        clipRule="evenodd"
                     />
                  </svg>
               </button>
               <span className="relative inline-flex items-center px-4 py-1 text-sm font-medium bg-gradient-to-b from-gray-700 to-gray-800 text-emerald-400 border border-gray-600">
                  Page {pagination.page} of {pagination.totalPages}
                  {/* Active page indicator with subtle glow */}
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400 opacity-70"></span>
               </span>
               <button
                  onClick={handleNextPage}
                  disabled={pagination.page === pagination.totalPages}
                  className={`relative inline-flex items-center px-2 py-1 ${
                     pagination.page < pagination.totalPages
                        ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                        : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-600 border border-gray-700 cursor-not-allowed opacity-70'
                  } transition-colors duration-200`}
               >
                  <span className="sr-only">Next</span>
                  <svg
                     className="h-5 w-5"
                     xmlns="http://www.w3.org/2000/svg"
                     viewBox="0 0 20 20"
                     fill="currentColor"
                     aria-hidden="true"
                  >
                     <path
                        fillRule="evenodd"
                        d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                        clipRule="evenodd"
                     />
                  </svg>
               </button>
               <button
                  onClick={() =>
                     setPagination(prev => ({ ...prev, page: pagination.totalPages }))
                  }
                  disabled={pagination.page === pagination.totalPages}
                  className={`relative inline-flex items-center rounded-r-sm px-2 py-1 ${
                     pagination.page < pagination.totalPages
                        ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                        : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-600 border border-gray-700 cursor-not-allowed opacity-70'
                  } transition-colors duration-200`}
               >
                  <span className="sr-only">Last</span>
                  <svg
                     xmlns="http://www.w3.org/2000/svg"
                     className="h-5 w-5"
                     viewBox="0 0 20 20"
                     fill="currentColor"
                  >
                     <path
                        fillRule="evenodd"
                        d="M10.293 15.707a1 1 0 010-1.414L14.586 10l-4.293-4.293a1 1 0 111.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z"
                        clipRule="evenodd"
                     />
                     <path
                        fillRule="evenodd"
                        d="M4.293 15.707a1 1 0 010-1.414L8.586 10 4.293 5.707a1 1 0 011.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z"
                        clipRule="evenodd"
                     />
                  </svg>
               </button>
            </nav>
         </div>
         <div className="flex flex-1 justify-between sm:hidden">
            <button
               onClick={handlePrevPage}
               disabled={pagination.page === 1}
               className={`relative inline-flex items-center rounded-sm px-4 py-2 text-sm font-medium ${
                  pagination.page > 1
                     ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-300 border border-gray-700 hover:bg-gray-700'
                     : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-500 border border-gray-700 cursor-not-allowed'
               } transition-colors duration-200`}
            >
               Previous
            </button>
            <button
               onClick={handleNextPage}
               disabled={pagination.page === pagination.totalPages}
               className={`relative ml-3 inline-flex items-center rounded-sm px-4 py-2 text-sm font-medium ${
                  pagination.page < pagination.totalPages
                     ? 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-300 border border-gray-700 hover:bg-gray-700'
                     : 'bg-gradient-to-b from-gray-800 to-gray-900 text-gray-500 border border-gray-700 cursor-not-allowed'
               } transition-colors duration-200`}
            >
               Next
            </button>
         </div>
      </div>
   );
};

export default Pagination;