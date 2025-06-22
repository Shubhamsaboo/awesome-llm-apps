import React, { useState, useEffect } from 'react';
import {
   Check,
   X,
   Loader2,
   Maximize2,
   Info,
   ChevronLeft,
   ChevronRight,
   Pause,
   Play,
   Eye,
   Sparkles,
} from 'lucide-react';
import api from '../services/api';

const BannerConfirmation = ({
   bannerUrl,
   topic,
   onApprove,
   onReject,
   isProcessing,
   bannerImages,
}) => {
   const [isPreviewOpen, setIsPreviewOpen] = useState(false);
   const [imageError, setImageError] = useState(false);
   const [currentImageIndex, setCurrentImageIndex] = useState(0);
   const [isAnimating, setIsAnimating] = useState(false);
   const [isPaused, setIsPaused] = useState(false);
   const [autoPlayEnabled, setAutoPlayEnabled] = useState(true);
   const API_BASE_URL = api.API_BASE_URL;
   const constructImageUrl = imageName => {
      return imageName ? `${API_BASE_URL}/podcast_img/${imageName}` : '';
   };
   const imagesToShow =
      bannerImages && bannerImages.length > 0
         ? bannerImages.map(constructImageUrl)
         : bannerUrl
         ? [bannerUrl]
         : [];
   const hasMultipleImages = imagesToShow.length > 1;
   const currentImage = imagesToShow[currentImageIndex] || '';

   useEffect(() => {
      if (!hasMultipleImages || isPaused || isProcessing || !autoPlayEnabled) return;

      const interval = setInterval(() => {
         setIsAnimating(true);
         setTimeout(() => {
            setCurrentImageIndex(prev => (prev + 1) % imagesToShow.length);
            setIsAnimating(false);
         }, 300);
      }, 5000);

      return () => clearInterval(interval);
   }, [hasMultipleImages, isPaused, isProcessing, autoPlayEnabled, imagesToShow.length]);

   const handleImageError = () => {
      setImageError(true);
   };
   const goToImage = index => {
      if (index === currentImageIndex || isAnimating) return;
      setIsAnimating(true);
      setTimeout(() => {
         setCurrentImageIndex(index);
         setIsAnimating(false);
      }, 300);
   };
   const goToPrevious = () => {
      const newIndex = currentImageIndex === 0 ? imagesToShow.length - 1 : currentImageIndex - 1;
      goToImage(newIndex);
   };
   const goToNext = () => {
      const newIndex = (currentImageIndex + 1) % imagesToShow.length;
      goToImage(newIndex);
   };
   const toggleAutoPlay = () => {
      setAutoPlayEnabled(!autoPlayEnabled);
   };

   return (
      <div className="w-full max-w-2xl mx-auto">
         <div className="bg-gradient-to-br from-gray-900 via-gray-850 to-gray-800 rounded-lg overflow-hidden shadow-xl border border-gray-700/50 transition-all duration-300 hover:shadow-2xl">
            <div className="relative px-3 py-2 bg-gradient-to-r from-gray-800/80 to-gray-900/80 backdrop-blur border-b border-gray-700/30">
               <div className="absolute inset-0 bg-gradient-to-r from-emerald-600/5 to-teal-600/5" />
               <div className="relative flex justify-between items-center">
                  <div className="flex items-center gap-2">
                     <div className="p-1 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-md">
                        <Sparkles className="w-3 h-3 text-emerald-400" />
                     </div>
                     <div>
                        <h3 className="text-sm font-semibold text-white">
                           Banner{hasMultipleImages ? ' Collection' : ''} Preview
                        </h3>
                        <p className="text-xs text-gray-400">{topic}</p>
                     </div>
                  </div>
                  {hasMultipleImages && (
                     <div className="flex items-center gap-3">
                        <div className="text-xs text-gray-300 bg-gray-800/50 px-2 py-1 rounded-md border border-gray-700/30">
                           {currentImageIndex + 1} of {imagesToShow.length}
                        </div>
                        <button
                           onClick={toggleAutoPlay}
                           className="p-1.5 text-gray-400 hover:text-white transition-all duration-200 hover:bg-gray-700/30 rounded-md"
                           title={autoPlayEnabled ? 'Pause slideshow' : 'Play slideshow'}
                        >
                           {autoPlayEnabled ? <Pause size={14} /> : <Play size={14} />}
                        </button>
                     </div>
                  )}
               </div>
            </div>
            <div className="relative px-6 py-6">
               {isProcessing && (
                  <div className="absolute inset-6 bg-gray-900/90 backdrop-blur-sm flex items-center justify-center z-10 rounded-xl border border-gray-700/30">
                     <div className="flex flex-col items-center gap-3">
                        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                        <p className="text-white font-medium">Processing banner...</p>
                     </div>
                  </div>
               )}
               <div
                  className="relative group cursor-pointer"
                  onMouseEnter={() => setIsPaused(true)}
                  onMouseLeave={() => setIsPaused(false)}
                  onClick={() => setIsPreviewOpen(true)}
               >
                  {imageError || !currentImage ? (
                     <div className="aspect-video w-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-700 rounded-xl border border-gray-600/30 text-gray-400">
                        <div className="flex flex-col items-center gap-3">
                           <Info className="w-8 h-8" />
                           <p className="text-sm font-medium">Failed to load banner</p>
                        </div>
                     </div>
                  ) : (
                     <div className="relative overflow-hidden rounded-xl shadow-lg">
                        <div className="aspect-video w-full relative overflow-hidden">
                           <img
                              src={currentImage}
                              alt={`Podcast banner ${
                                 hasMultipleImages ? `${currentImageIndex + 1} ` : ''
                              }for ${topic}`}
                              className={`w-full h-full object-cover transition-all duration-500 ease-out ${
                                 isAnimating ? 'opacity-0 scale-105' : 'opacity-100 scale-100'
                              } group-hover:scale-105`}
                              onError={handleImageError}
                           />
                           {isAnimating && (
                              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-[shimmer_1s_ease-in-out] rounded-xl" />
                           )}
                           <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300" />
                           <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
                              <div className="bg-black/50 backdrop-blur-sm p-4 rounded-full border border-white/20">
                                 <Maximize2 className="w-6 h-6 text-white" />
                              </div>
                           </div>
                        </div>
                        {hasMultipleImages && (
                           <>
                              <button
                                 onClick={e => {
                                    e.stopPropagation();
                                    goToPrevious();
                                 }}
                                 className="absolute left-4 top-1/2 -translate-y-1/2 bg-black/60 backdrop-blur-sm hover:bg-black/80 text-white p-3 rounded-full border border-white/10 opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
                                 aria-label="Previous banner"
                              >
                                 <ChevronLeft className="w-5 h-5" />
                              </button>
                              <button
                                 onClick={e => {
                                    e.stopPropagation();
                                    goToNext();
                                 }}
                                 className="absolute right-4 top-1/2 -translate-y-1/2 bg-black/60 backdrop-blur-sm hover:bg-black/80 text-white p-3 rounded-full border border-white/10 opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
                                 aria-label="Next banner"
                              >
                                 <ChevronRight className="w-5 h-5" />
                              </button>
                           </>
                        )}
                     </div>
                  )}
               </div>
               {hasMultipleImages && (
                  <div className="flex justify-center gap-2 mt-4">
                     {imagesToShow.map((_, index) => (
                        <button
                           key={index}
                           onClick={() => goToImage(index)}
                           className={`transition-all duration-300 rounded-full ${
                              index === currentImageIndex
                                 ? 'w-8 h-3 bg-gradient-to-r from-emerald-500 to-teal-500 shadow-lg shadow-emerald-500/25'
                                 : 'w-3 h-3 bg-gray-600 hover:bg-gray-500 hover:scale-125'
                           }`}
                           aria-label={`Go to banner ${index + 1}`}
                        />
                     ))}
                  </div>
               )}
            </div>
            <div className="px-3 py-2 bg-gradient-to-r from-gray-900/50 to-gray-800/50 backdrop-blur border-t border-gray-700/30">
               <div className="flex justify-center">
                  <button
                     onClick={onApprove}
                     disabled={isProcessing}
                     className={`group flex items-center justify-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-sm font-medium rounded-lg transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-emerald-500/25 border border-emerald-500/30 ${
                        isProcessing ? 'opacity-70 cursor-not-allowed' : ''
                     }`}
                     aria-disabled={isProcessing}
                  >
                     {isProcessing ? (
                        <>
                           <Loader2 className="w-4 h-4 animate-spin" />
                           <span>Processing...</span>
                        </>
                     ) : (
                        <>
                           <Check className="w-4 h-4 group-hover:scale-110 transition-transform" />
                           <span>Approve Banner{hasMultipleImages ? 's' : ''}</span>
                        </>
                     )}
                  </button>
               </div>
               <div className="mt-1.5 text-center">
                  <p className="text-xs text-gray-400 flex items-center justify-center gap-1">
                     <Eye className="w-3 h-3" />
                     {hasMultipleImages
                        ? 'Click any banner to view in full size'
                        : 'Click banner to view in full size'}
                  </p>
               </div>
            </div>
         </div>
         {isPreviewOpen && (
            <div className="fixed inset-0 bg-black/95 backdrop-blur-sm flex items-center justify-center z-50 p-4">
               <div className="max-w-7xl max-h-screen overflow-auto relative">
                  <button
                     onClick={() => setIsPreviewOpen(false)}
                     className="absolute top-6 right-6 bg-black/60 backdrop-blur-sm text-white p-3 rounded-full hover:bg-black/80 transition-all duration-200 hover:scale-110 border border-white/10 z-10"
                     aria-label="Close full preview"
                  >
                     <X className="w-6 h-6" />
                  </button>
                  {hasMultipleImages && (
                     <>
                        <button
                           onClick={goToPrevious}
                           className="absolute left-6 top-1/2 -translate-y-1/2 bg-black/60 backdrop-blur-sm hover:bg-black/80 text-white p-4 rounded-full transition-all duration-200 hover:scale-110 border border-white/10 z-10"
                           aria-label="Previous banner"
                        >
                           <ChevronLeft className="w-6 h-6" />
                        </button>
                        <button
                           onClick={goToNext}
                           className="absolute right-6 top-1/2 -translate-y-1/2 bg-black/60 backdrop-blur-sm hover:bg-black/80 text-white p-4 rounded-full transition-all duration-200 hover:scale-110 border border-white/10 z-10"
                           aria-label="Next banner"
                        >
                           <ChevronRight className="w-6 h-6" />
                        </button>
                        <div className="absolute top-6 left-6 bg-black/60 backdrop-blur-sm text-white px-4 py-2 rounded-lg text-sm border border-white/10 z-10">
                           <span className="font-medium">{currentImageIndex + 1}</span>
                           <span className="text-gray-300 mx-1">of</span>
                           <span className="font-medium">{imagesToShow.length}</span>
                        </div>
                     </>
                  )}
                  <img
                     src={currentImage}
                     alt={`Full size podcast banner ${
                        hasMultipleImages ? `${currentImageIndex + 1} ` : ''
                     }for ${topic}`}
                     className="max-w-full h-auto shadow-2xl rounded-lg transition-all duration-300"
                  />
                  {hasMultipleImages && imagesToShow.length > 1 && (
                     <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-3 bg-black/60 backdrop-blur-sm p-3 rounded-xl border border-white/10">
                        {imagesToShow.map((image, index) => (
                           <button
                              key={index}
                              onClick={() => goToImage(index)}
                              className={`transition-all duration-200 rounded-lg overflow-hidden border-2 ${
                                 index === currentImageIndex
                                    ? 'border-emerald-500 scale-110 shadow-lg shadow-emerald-500/25'
                                    : 'border-transparent hover:scale-105 opacity-70 hover:opacity-100'
                              }`}
                           >
                              <img
                                 src={image}
                                 alt={`Thumbnail ${index + 1}`}
                                 className="w-20 h-12 object-cover"
                              />
                           </button>
                        ))}
                     </div>
                  )}
               </div>
            </div>
         )}
      </div>
   );
};

BannerConfirmation.defaultProps = {
   onReject: () => {},
   isProcessing: false,
   bannerImages: [],
};

export default BannerConfirmation;
