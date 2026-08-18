import { cn } from "@/lib/utils";

const STILLER: Record<string, string> = {
  Açık: "bg-amber-100 text-amber-950 border-amber-300 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800",
  "Devam Ediyor":
    "bg-sky-100 text-sky-950 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800",
  Kapalı:
    "bg-emerald-100 text-emerald-950 border-emerald-400 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800",
};

interface Ozellikler {
  durum: string;
  className?: string;
}

/** Excel çıktısındaki durum sütununu arayüzde hızlı ayırt etmek için. */
export function DurumPili({ durum, className }: Ozellikler) {
  const etiket = durum.trim() || "Açık";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold",
        STILLER[etiket] ?? STILLER["Açık"],
        className,
      )}
    >
      {etiket}
    </span>
  );
}
