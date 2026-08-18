import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";

interface Ozellikler {
  etiket: string;
  htmlFor?: string;
  ipucu?: React.ReactNode;
  zorunlu?: boolean;
  className?: string;
  children: React.ReactNode;
}

/** Görünür etiket + isteğe bağlı yardım metni (ui-ux-pro-max: input-labels). */
export function Alan({
  etiket,
  htmlFor,
  ipucu,
  zorunlu,
  className,
  children,
}: Ozellikler) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <Label
        htmlFor={htmlFor}
        className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"
      >
        {etiket}
        {zorunlu && (
          <span className="text-destructive" aria-label="zorunlu alan">
            *
          </span>
        )}
      </Label>
      {children}
      {ipucu && (
        <p className="text-[11px] leading-snug text-muted-foreground">{ipucu}</p>
      )}
    </div>
  );
}
