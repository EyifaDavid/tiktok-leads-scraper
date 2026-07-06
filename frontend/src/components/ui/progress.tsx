"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
}

const Progress = forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)}
      {...props}
    >
      <div
        className="h-full w-full flex-1 rounded-full bg-primary transition-all duration-300"
        style={{ transform: `translateX(-${100 - Math.min(value, 100)}%)` }}
      />
    </div>
  )
);
Progress.displayName = "Progress";

export { Progress };
