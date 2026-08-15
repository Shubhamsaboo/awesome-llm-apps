import { getSvgPath } from "figma-squircle";
import {
  type CSSProperties,
  type HTMLAttributes,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

type CornerRadius = {
  topLeft: number;
  topRight: number;
  bottomLeft: number;
  bottomRight: number;
};

export type SquircleProps = HTMLAttributes<HTMLDivElement> & {
  squircle: string;
  smoothing?: number;
  preserveSmoothing?: boolean;
  borderWidth?: number;
  borderColor?: string;
  measurementScale?: number;
};

function parseCornerRadius(input: string): CornerRadius {
  const parts = input.trim().split(/\s+/).filter(Boolean).map(Number);

  if (parts.length === 1) {
    return {
      topLeft: parts[0],
      topRight: parts[0],
      bottomLeft: parts[0],
      bottomRight: parts[0],
    };
  }

  if (parts.length === 2) {
    return {
      topLeft: parts[0],
      topRight: parts[0],
      bottomLeft: parts[1],
      bottomRight: parts[1],
    };
  }

  if (parts.length === 4) {
    return {
      topLeft: parts[0],
      topRight: parts[1],
      bottomLeft: parts[2],
      bottomRight: parts[3],
    };
  }

  throw new Error("Invalid squircle input");
}

export function Squircle({
  squircle,
  smoothing = 1,
  preserveSmoothing = true,
  borderWidth = 0,
  borderColor,
  measurementScale = 1,
  className,
  style,
  children,
  ...rest
}: SquircleProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [box, setBox] = useState({ width: 0, height: 0 });
  const [resolvedBorderColor, setResolvedBorderColor] = useState(borderColor ?? "transparent");

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const readBox = () => {
      const rect = host.getBoundingClientRect();
      const scale = measurementScale > 0 ? measurementScale : 1;
      const cssBorderColor = getComputedStyle(host)
        .getPropertyValue("--app-squircle-border-color")
        .trim();

      setBox({
        width: rect.width / scale,
        height: rect.height / scale,
      });
      setResolvedBorderColor((borderColor ?? cssBorderColor) || "transparent");
    };

    readBox();

    if (typeof ResizeObserver === "undefined") {
      return;
    }

    const resizeObserver = new ResizeObserver(readBox);
    resizeObserver.observe(host);

    return () => resizeObserver.disconnect();
  }, [borderColor, measurementScale]);

  const cornerRadius = useMemo(() => parseCornerRadius(squircle), [squircle]);

  const path = useMemo(() => {
    if (!box.width || !box.height) {
      return "";
    }

    return getSvgPath({
      width: box.width,
      height: box.height,
      topLeftCornerRadius: cornerRadius.topLeft,
      topRightCornerRadius: cornerRadius.topRight,
      bottomLeftCornerRadius: cornerRadius.bottomLeft,
      bottomRightCornerRadius: cornerRadius.bottomRight,
      cornerSmoothing: smoothing,
      preserveSmoothing,
    });
  }, [box, cornerRadius, preserveSmoothing, smoothing]);

  const clipPathValue = path ? `path('${path}')` : undefined;

  const borderImage = useMemo(() => {
    if (!path || borderWidth <= 0) {
      return undefined;
    }

    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 ${box.width} ${box.height}">
        <path d="${path}" fill="none" style="stroke:${resolvedBorderColor};stroke-width:${borderWidth};" />
      </svg>
    `;

    return `url("data:image/svg+xml;base64,${btoa(svg)}")`;
  }, [borderWidth, box.height, box.width, path, resolvedBorderColor]);

  const mergedStyle = {
    ...style,
    clipPath: clipPathValue,
    WebkitClipPath: clipPathValue,
    "--app-squircle-border-color": borderColor ?? resolvedBorderColor,
    "--app-squircle-border-width": `${borderWidth}px`,
    "--app-squircle-width": `${box.width}px`,
    "--app-squircle-height": `${box.height}px`,
  } as CSSProperties;

  return (
    <div
      ref={hostRef}
      className={["squircle", className].filter(Boolean).join(" ")}
      style={mergedStyle}
      {...rest}
    >
      {children}
      {borderImage ? (
        <div
          aria-hidden
          className="squircle-border-overlay"
          style={{ backgroundImage: borderImage }}
        />
      ) : null}
    </div>
  );
}
