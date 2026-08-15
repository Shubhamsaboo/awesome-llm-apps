import { useEffect, type RefObject } from "react";

export function useCarouselAnimation(
  carouselContainerRef: RefObject<HTMLDivElement | null>,
  scrollContainerRef: RefObject<HTMLDivElement | null>,
): void {
  useEffect(() => {
    let lastPointerX = 0;
    let lastPointerY = 0;

    const updateItems = () => {
      const container = carouselContainerRef.current;
      if (!container) return;

      const articles =
        container.querySelectorAll<HTMLElement>(".carousel-item");

      articles.forEach((article) => {
        const rect = article.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const relativeX = lastPointerX - centerX;
        const relativeY = lastPointerY - centerY;
        const x = relativeX / (rect.width / 2);
        const y = relativeY / (rect.height / 2);

        // Calculate distance from cursor to center of item
        const distance = Math.sqrt(
          relativeX * relativeX + relativeY * relativeY,
        );
        // Use a larger max distance to make the effect work across gaps
        const maxDistance = Math.max(rect.width, rect.height) * 2;
        const normalizedDistance = Math.min(distance / maxDistance, 1);

        // Closer items get higher opacity and scale
        // Use exponential falloff for smoother transition
        const proximity = Math.pow(1 - normalizedDistance, 2);
        const opacity = 0.1 + proximity * 0.3; // Range from 0.1 to 0.4
        const scale = 2.0 + proximity * 2.0; // Range from 2.0 to 4.0

        article.style.setProperty("--pointer-x", x.toFixed(3));
        article.style.setProperty("--pointer-y", y.toFixed(3));
        article.style.setProperty("--icon-opacity", opacity.toFixed(3));
        article.style.setProperty("--icon-scale", scale.toFixed(2));
      });
    };

    const handlePointerMove = (event: { clientX: number; clientY: number }) => {
      lastPointerX = event.clientX;
      lastPointerY = event.clientY;
      updateItems();
    };

    const handleScroll = () => {
      updateItems();
    };

    document.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("scroll", handleScroll, true);

    const scrollContainer = scrollContainerRef.current;
    if (scrollContainer) {
      scrollContainer.addEventListener("scroll", handleScroll);
    }

    // Initial update
    updateItems();

    return () => {
      document.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("scroll", handleScroll, true);
      const container = scrollContainerRef.current;
      if (container) {
        container.removeEventListener("scroll", handleScroll);
      }
    };
  }, [carouselContainerRef, scrollContainerRef]);
}
