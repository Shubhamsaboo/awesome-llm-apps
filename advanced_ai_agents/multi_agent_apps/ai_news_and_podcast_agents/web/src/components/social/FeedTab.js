import React from 'react';
import PostItem from './PostItem';
import Filters from './Filters';
import Pagination from './Pagination';

const FeedTab = ({
   posts,
   loading,
   error,
   filters,
   pagination,
   isFilterOpen,
   platforms,
   sentiments,
   categories,
   handleFilterChange,
   resetFilters,
   handlePrevPage,
   handleNextPage,
   setIsFilterOpen,
   setPagination,
   onPostClick,
}) => {
   return (
      <div className="space-y-4">
         <Filters
            isOpen={isFilterOpen}
            filters={filters}
            platforms={platforms}
            sentiments={sentiments}
            categories={categories}
            handleFilterChange={handleFilterChange}
            resetFilters={resetFilters}
            setIsFilterOpen={setIsFilterOpen}
         />

         {loading ? (
            <div className="flex justify-center py-12">
               <div className="animate-spin w-10 h-10 border-3 border-emerald-500 border-t-transparent rounded-full shadow-md"></div>
            </div>
         ) : error ? (
            <div className="bg-gradient-to-br from-red-900/80 to-red-800/80 border border-red-700 text-red-200 px-4 py-3 rounded-sm shadow-md">
               <div className="flex items-center">
                  <svg
                     className="w-5 h-5 text-red-400 mr-2"
                     fill="currentColor"
                     viewBox="0 0 20 20"
                  >
                     <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                     />
                  </svg>
                  {error}
               </div>
            </div>
         ) : posts.length === 0 ? (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-sm p-8 text-center shadow-md">
               <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-b from-gray-700 to-gray-800 rounded-full flex items-center justify-center">
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
                        d="M6 18L18 6M6 6l12 12"
                     />
                  </svg>
               </div>
               <h3 className="text-lg font-medium text-gray-300 mb-2">No posts found</h3>
               <p className="text-gray-400">Try adjusting your filters or search terms</p>
            </div>
         ) : (
            <>
               <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                  {posts.map(post => (
                     <PostItem key={post.post_id} post={post} onPostClick={onPostClick} />
                  ))}
               </div>

               {posts.length > 0 && (
                  <Pagination
                     pagination={pagination}
                     handlePrevPage={handlePrevPage}
                     handleNextPage={handleNextPage}
                     setPagination={setPagination}
                  />
               )}
            </>
         )}
      </div>
   );
};

export default FeedTab;
