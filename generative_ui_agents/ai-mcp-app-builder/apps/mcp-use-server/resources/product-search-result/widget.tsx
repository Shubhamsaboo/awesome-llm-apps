import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import {
  Image,
  McpUseProvider,
  useCallTool,
  useWidget,
  type WidgetMetadata,
} from "mcp-use/react";
import React, { useCallback } from "react";
import { Link } from "react-router";
import "../styles.css";
import { Carousel } from "./components/Carousel";
import { CarouselSkeleton } from "./components/CarouselSkeleton";
import { Accordion } from "./components/Accordion";
import type { ProductSearchResultProps } from "./types";
import { propSchema } from "./types";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import {
  Expand,
  HeartFilled,
  HeartXs,
  PictureInPicture,
} from "@openai/apps-sdk-ui/components/Icon";
export const widgetMetadata: WidgetMetadata = {
  description:
    "Display product search results with filtering, state management, and tool interactions",
  props: propSchema,
  exposeAsTool: false,
  metadata: {
    prefersBorder: false,
    invoking: "Loading product search results...",
    invoked: "Product search results loaded",
    csp: {
      // Widget-specific
      resourceDomains: ["https://cdn.openai.com"],
    },
  },
};
type FavoritesState = { favorites: string[] };

const ProductSearchResult: React.FC = () => {
  const {
    props,
    isPending,
    displayMode,
    requestDisplayMode,
    sendFollowUpMessage,
    locale,
    state,
    setState,
  } = useWidget<ProductSearchResultProps, FavoritesState>();

  const {
    callTool: getFruitDetails,
    data: fruitDetails,
    isPending: isLoadingDetails,
  } = useCallTool("get-fruit-details");

  const selectedFruit = fruitDetails?.structuredContent as
    | { fruit: string; facts?: string[] }
    | undefined;
  const favorites = state?.favorites ?? [];

  const toggleFavorite = useCallback(
    (fruit: string) => {
      const current = state?.favorites ?? [];
      const next = current.includes(fruit)
        ? current.filter((f: string) => f !== fruit)
        : [...current, fruit];
      setState({ favorites: next });
    },
    [state, setState],
  );

  const accordionItems = [
    {
      question: "Demo of the autosize feature",
      answer:
        "This is a demo of the autosize feature. The widget will automatically resize to fit the content, as supported by the mcp-apps specification",
    },
  ];

  if (isPending) {
    return (
      <McpUseProvider>
        <div className="relative bg-surface-elevated border border-default rounded-3xl">
          <div className="p-8 pb-4">
            <h5 className="text-secondary mb-1">MCP-Apps Template</h5>
            <h2 className="heading-xl mb-3">Lovely Little Fruit Shop</h2>
            <div className="h-5 w-48 rounded-md bg-default/10 animate-pulse" />
          </div>
          <CarouselSkeleton />
        </div>
      </McpUseProvider>
    );
  }

  const { query, results } = props;
  const isFullscreen = displayMode === "fullscreen";
  const isPip = displayMode === "pip";
  const lang = locale?.split("-")[0] ?? "en";

  return (
    <McpUseProvider>
      <AppsSDKUIProvider linkComponent={Link}>
        <div className="relative bg-surface-elevated border border-default rounded-3xl">
          {/* Toolbar — top-right badges and controls */}
          <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
            {/* Locale badge */}
            <span className="px-2.5 py-1 text-xs font-medium rounded-full text-secondary uppercase tracking-wide">
              {lang}
            </span>

            {/* Favorites count */}
            {favorites.length > 0 && (
              <Button
                color="secondary"
                pill
                size="lg"
                uniform
                variant="ghost"
                className="text-danger/80"
              >
                <HeartFilled />
                {favorites.length}
              </Button>
            )}

            {/* Display mode buttons */}
            {!isFullscreen && !isPip && (
              <>
                <Button
                  color="secondary"
                  pill
                  size="lg"
                  uniform
                  variant="outline"
                  onClick={() => requestDisplayMode("pip")}
                  title="Picture-in-picture"
                >
                  <PictureInPicture />
                </Button>
                <Button
                  color="secondary"
                  pill
                  size="lg"
                  uniform
                  variant="outline"
                  onClick={() => requestDisplayMode("fullscreen")}
                  title="Fullscreen"
                >
                  <Expand />
                </Button>
              </>
            )}

            {(isFullscreen || isPip) && (
              <Button
                color="secondary"
                pill
                size="lg"
                uniform
                variant="outline"
                onClick={() => requestDisplayMode("inline")}
                title="Exit"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </Button>
            )}
          </div>

          {/* Header */}
          <div className="p-8 pb-4">
            <h5 className="text-secondary mb-1">MCP-Apps Template</h5>
            <h2 className="heading-xl mb-1">Lovely Little Fruit Shop</h2>
            <p className="text-md text-secondary">
              {query
                ? `Showing results for "${query}"`
                : "Tap a fruit to see details"}
            </p>
          </div>

          {/* Carousel */}
          <Carousel
            results={results}
            favorites={favorites}
            onSelectFruit={(fruit: string) =>
              getFruitDetails({ fruit } as never)
            }
            onToggleFavorite={toggleFavorite}
          />

          {/* Detail view */}
          {selectedFruit && (
            <div className="mx-8 my-6 rounded-2xl border border-default bg-surface p-5 flex items-center gap-6">
              <div
                className={`rounded-xl p-4 shrink-0 ${
                  results.find(
                    (r: { fruit: string }) => r.fruit === selectedFruit.fruit,
                  )?.color ?? ""
                }`}
              >
                <Image
                  src={`/fruits/${selectedFruit.fruit}.png`}
                  alt={selectedFruit.fruit}
                  className="w-24 h-24 object-contain"
                />
              </div>
              <div className="flex-1">
                {isLoadingDetails ? (
                  <div className="animate-pulse h-4 w-32 bg-surface-elevated rounded" />
                ) : (
                  <>
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-lg capitalize">
                        {selectedFruit.fruit}
                      </h3>
                      <Button
                        color="secondary"
                        pill
                        size="md"
                        uniform
                        variant="ghost"
                        onClick={() => toggleFavorite(selectedFruit.fruit)}
                        title={
                          favorites.includes(selectedFruit.fruit)
                            ? "Remove from favorites"
                            : "Add to favorites"
                        }
                        className={
                          favorites.includes(selectedFruit.fruit)
                            ? "text-danger/80"
                            : "text-secondary"
                        }
                      >
                        {favorites.includes(selectedFruit.fruit) ? (
                          <HeartFilled />
                        ) : (
                          <HeartXs />
                        )}
                      </Button>
                    </div>
                    <ul className="space-y-1">
                      {(selectedFruit.facts ?? []).map((fact: string) => (
                        <li
                          key={fact}
                          className="text-sm text-secondary flex items-start gap-2"
                        >
                          <span className="text-info mt-0.5">•</span>
                          {fact}
                        </li>
                      ))}
                    </ul>
                    {/* Follow-up message demo — sends a message to the LLM from the widget */}
                    <button
                      onClick={() =>
                        sendFollowUpMessage(
                          `Tell me more interesting facts about ${selectedFruit.fruit}`,
                        )
                      }
                      className="mt-3 px-3 py-1.5 text-xs font-medium rounded-lg bg-info/10 text-info hover:bg-info/20 transition-colors cursor-pointer"
                    >
                      Ask the AI for more about {selectedFruit.fruit}
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          <Accordion items={accordionItems} />
        </div>
      </AppsSDKUIProvider>
    </McpUseProvider>
  );
};

export default ProductSearchResult;
