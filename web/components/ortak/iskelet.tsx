import { cn } from "@/lib/utils";

/** Yükleme sırasında boşluğu rezerve eder (ui-ux-pro-max: content-jumping). */
export function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  );
}
