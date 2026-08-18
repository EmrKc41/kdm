import type { Metadata } from "next";
import { Fira_Sans, Fira_Code } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { TemaSaglayici } from "@/components/tema-saglayici";
import "./globals.css";

/* next/font fontları DERLEME sırasında indirip kendi sunucumuzdan servis eder.
   Bu sayede fabrika makinesinde internet olmadan da çalışır — Google Fonts'a
   çalışma anında hiçbir istek gitmez. */
const firaSans = Fira_Sans({
  variable: "--font-fira-sans",
  subsets: ["latin", "latin-ext"], // latin-ext: ç ğ ı İ ö ş ü
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

const firaCode = Fira_Code({
  variable: "--font-fira-code",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Kalite Doküman Üretici",
  description:
    "İş talimatı, tek nokta eğitimi ve vardiya listesi dokümanlarını " +
    "şablona sadık biçimde üretir.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    /* suppressHydrationWarning YALNIZCA bulundugu etiketin kendi
       nitelikleri icin gecerlidir, alt agaca inmez.
       <html> icin: next-themes tema sinifini istemcide ekler.
       <body> icin: bazi tarayici eklentileri (ColorZilla -> cz-shortcut-listen,
       Grammarly -> data-gr-*) React yuklenmeden ONCE body'ye nitelik enjekte
       eder. Bu bizim kodumuzdan kaynaklanmaz ve engellenemez; yalnizca bu iki
       etiketin nitelik uyusmazligi susturulur, bilesenlerdeki gercek
       hydration hatalari gorunur kalir. */
    <html lang="tr" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${firaSans.variable} ${firaCode.variable} antialiased`}
      >
        <TemaSaglayici>
          {children}
          <Toaster
            position="bottom-right"
            closeButton
            richColors
            toastOptions={{ duration: 5000 }}
          />
        </TemaSaglayici>
      </body>
    </html>
  );
}
