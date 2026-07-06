"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
}

const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, alt, fallback, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative flex h-9 w-9 shrink-0 overflow-hidden rounded-full bg-muted",
          className
        )}
        {...props}
      >
        {src ? (
          <img src={src} alt={alt || ""} className="aspect-square h-full w-full" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xs font-medium text-muted-foreground">
            {fallback || "?"}
          </div>
        )}
      </div>
    );
  }
);
Avatar.displayName = "Avatar";

export { Avatar };
