import { cn } from "@/lib/utils";

interface Ozellikler {
  baslik: string;
  aciklama?: string;
  eylem?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}

/** Yoğun veri girişi için sade bölüm kartı (Data-Dense Dashboard). */
export function Bolum({ baslik, aciklama, eylem, className, children }: Ozellikler) {
  return (
    <section
      className={cn(
        "rounded-lg border border-border bg-card shadow-sm",
        className,
      )}
    >
      <header className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-border px-4 py-2.5">
        <h2 className="font-mono text-[11px] font-bold uppercase tracking-[0.08em] text-muted-foreground">
          {baslik}
        </h2>
        {aciklama && (
          <p className="text-xs text-muted-foreground/80">{aciklama}</p>
        )}
        {eylem && <div className="ml-auto">{eylem}</div>}
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}
