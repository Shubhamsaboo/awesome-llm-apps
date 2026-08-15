import * as React from "react";
import { cn } from "@/lib/utils";

const GAP: Record<string, string> = {
  "0": "gap-0",
  "1": "gap-1",
  "2": "gap-2",
  "3": "gap-3",
  "4": "gap-4",
  "5": "gap-5",
  "6": "gap-6",
  "8": "gap-8",
};

const ITEMS: Record<string, string> = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
};

const JUSTIFY: Record<string, string> = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
  around: "justify-around",
};

function Row({
  className,
  gap = "4",
  align = "stretch",
  justify = "start",
  ...props
}: React.ComponentProps<"div"> & {
  gap?: string;
  align?: string;
  justify?: string;
}) {
  return (
    <div
      data-slot="row"
      className={cn(
        "grid w-full grid-cols-[repeat(auto-fit,minmax(0,1fr))] max-w-full [&>*:nth-child(n+4)]:hidden",
        GAP[gap] ?? "gap-4",
        ITEMS[align] ?? "items-stretch",
        JUSTIFY[justify] ?? "justify-start",
        className,
      )}
      {...props}
    />
  );
}

function Column({
  className,
  gap = "4",
  align = "stretch",
  justify = "start",
  ...props
}: React.ComponentProps<"div"> & {
  gap?: string;
  align?: string;
  justify?: string;
}) {
  return (
    <div
      data-slot="column"
      className={cn(
        "flex flex-col w-full",
        GAP[gap] ?? "gap-4",
        ITEMS[align] ?? "items-stretch",
        JUSTIFY[justify] ?? "justify-start",
        className,
      )}
      {...props}
    />
  );
}

export { Row, Column };
