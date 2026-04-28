import { Animate } from "@openai/apps-sdk-ui/components/Transition";
import React, { useRef } from "react";
import { CarouselItem } from "./CarouselItem";
import { useCarouselAnimation } from "../hooks/useCarouselAnimation";

interface CarouselProps {
  results: Array<{ fruit: string; color: string }>;
  favorites?: string[];
  onSelectFruit: (fruit: string) => void;
  onToggleFavorite?: (fruit: string) => void;
}

export const Carousel: React.FC<CarouselProps> = ({
  results,
  favorites = [],
  onSelectFruit,
  onToggleFavorite,
}) => {
  const carouselContainerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useCarouselAnimation(carouselContainerRef, scrollContainerRef);

  return (
    <div
      ref={scrollContainerRef}
      className="carousel-scroll-container w-full overflow-x-auto overflow-y-visible pl-8"
    >
      <div ref={carouselContainerRef} className="overflow-visible">
        <Animate className="flex gap-4">
          {results.map((item, index) => {
            const fruit =
              item.fruit ?? (item as { name?: string }).name ?? "Item";
            return (
              <CarouselItem
                key={`${fruit}-${index}`}
                fruit={fruit}
                color={item.color ?? "bg-default/10"}
                isFavorite={favorites.includes(fruit)}
                onClick={() => onSelectFruit(fruit)}
                onToggleFavorite={
                  onToggleFavorite ? () => onToggleFavorite(fruit) : undefined
                }
              />
            );
          })}
        </Animate>
      </div>
    </div>
  );
};
