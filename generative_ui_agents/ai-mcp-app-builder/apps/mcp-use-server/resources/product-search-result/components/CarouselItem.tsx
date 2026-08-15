import { Button } from "@openai/apps-sdk-ui/components/Button";
import { HeartFilled, HeartXs } from "@openai/apps-sdk-ui/components/Icon";
import { Image } from "mcp-use/react";
import React from "react";

export interface CarouselItemProps {
  fruit: string;
  color: string;
  isFavorite?: boolean;
  onClick: () => void;
  onToggleFavorite?: () => void;
}

export const CarouselItem: React.FC<CarouselItemProps> = ({
  fruit,
  color,
  isFavorite,
  onClick,
  onToggleFavorite,
}) => {
  return (
    <div
      className={`carousel-item size-52 rounded-xl border border-subtle ${color} cursor-pointer`}
      onClick={onClick}
    >
      {onToggleFavorite && (
        <Button
          color="secondary"
          pill
          size="md"
          uniform
          variant="ghost"
          onClick={(e) => {
            e.stopPropagation();
            onToggleFavorite();
          }}
          className={`absolute top-2 right-2 z-10 ${isFavorite ? "text-danger/80" : "text-secondary"}`}
        >
          {isFavorite ? <HeartFilled /> : <HeartXs />}
        </Button>
      )}
      <div className="carousel-item-bg">
        <Image src={"/fruits/" + fruit + ".png"} alt={fruit} />
      </div>
      <div className="carousel-item-content">
        <Image
          src={"/fruits/" + fruit + ".png"}
          alt={fruit}
          className="w-24 h-24 object-contain"
        />
      </div>
    </div>
  );
};
