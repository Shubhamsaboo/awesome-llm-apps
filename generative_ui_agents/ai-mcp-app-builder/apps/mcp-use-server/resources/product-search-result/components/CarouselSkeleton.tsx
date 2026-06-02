import React from "react";

const SKELETON_COUNT = 6;

export const CarouselSkeleton: React.FC = () => {
  return (
    <div className="carousel-scroll-container w-full overflow-x-auto overflow-y-visible pl-8">
      <div className="overflow-hidden">
        <div className="flex gap-4">
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <div
              key={i}
              className="carousel-item shrink-0 size-52 rounded-xl border border-subtle animate-pulse bg-gray-100"
            ></div>
          ))}
        </div>
      </div>
    </div>
  );
};
