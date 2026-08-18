import Image from "next/image";
import { ClipboardList, FileText, GraduationCap, Settings2, Users } from "lucide-react";
import { TemaDugmesi } from "@/components/tema-dugmesi";
import { OturumKapisi } from "@/components/giris/oturum-kapisi";
import { CikisDugmesi } from "@/components/giris/cikis-dugmesi";
import { MotorDurumu } from "@/components/ortak/motor-durumu";
import { SekmeGecisi } from "@/components/ortak/sekme-gecisi";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TalimatFormu } from "@/components/talimat/talimat-formu";
import { TneFormu } from "@/components/tne/tne-formu";
import { VardiyaFormu } from "@/components/vardiya/vardiya-formu";
import { RaporFormu } from "@/components/rapor/rapor-formu";
import { AyarlarPaneli } from "@/components/ayarlar/ayarlar-paneli";

const SEKMELER = [
  { deger: "talimat", etiket: "İş Talimatı", Ikon: ClipboardList },
  { deger: "tne", etiket: "Tek Nokta Eğitimi", Ikon: GraduationCap },
  { deger: "vardiya", etiket: "Vardiya Listesi", Ikon: Users },
  { deger: "rapor", etiket: "Kalite Raporu", Ikon: FileText },
  { deger: "ayarlar", etiket: "Ayarlar", Ikon: Settings2 },
] as const;

export default function AnaSayfa() {
  return (
    <OturumKapisi>
      <Tabs defaultValue="talimat" className="min-h-dvh gap-0">
        <header className="sticky top-0 z-40 border-b border-border bg-card/90 backdrop-blur supports-[backdrop-filter]:bg-card/75">
          <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2.5 sm:px-6">
            <div className="flex items-center gap-2.5">
              {/* Marka isareti beyaz zeminiyle bir butundur (ic detaylar beyaz
                  cizilmistir), bu yuzden koyu temada da beyaz bir karo olarak
                  durur. Ince bir cerceve kenarini zeminden ayirir. */}
              <Image
                src="/marka/logo-192.png"
                alt="Kalite Doküman Üretici"
                width={32}
                height={32}
                priority
                className="size-8 shrink-0 rounded-md bg-white ring-1 ring-border"
              />
              <div className="leading-tight">
                <h1 className="text-sm font-bold tracking-tight">
                  Kalite Doküman Üretici
                </h1>
                <p className="text-[11px] text-muted-foreground">
                  Şablona sadık Excel çıktısı
                </p>
              </div>
            </div>

            {/* shadcn varsayilani "inline-flex w-fit"; dar ekranda 4 sekme
                sigmayip yatay tasma yapiyordu. Sarmalayacak sekilde eziliyor
                (ui-ux-pro-max: horizontal-scroll). */}
            <TabsList className="flex h-auto w-full flex-wrap justify-start gap-1 bg-transparent p-0 md:w-auto">
              {SEKMELER.map(({ deger, etiket, Ikon }) => (
                <TabsTrigger
                  key={deger}
                  value={deger}
                  className="flex-none gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm"
                >
                  <Ikon className="size-3.5" aria-hidden />
                  {etiket}
                </TabsTrigger>
              ))}
            </TabsList>

            <div className="ml-auto flex items-center gap-1.5">
              <MotorDurumu />
              <TemaDugmesi />
              <CikisDugmesi />
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1600px] flex-1 px-4 py-4 sm:px-6">
          <TabsContent value="talimat" className="mt-0">
            <SekmeGecisi>
              <TalimatFormu />
            </SekmeGecisi>
          </TabsContent>
          <TabsContent value="tne" className="mt-0">
            <SekmeGecisi>
              <TneFormu />
            </SekmeGecisi>
          </TabsContent>
          <TabsContent value="vardiya" className="mt-0">
            <SekmeGecisi>
              <VardiyaFormu />
            </SekmeGecisi>
          </TabsContent>
          <TabsContent value="rapor" className="mt-0">
            <SekmeGecisi>
              <RaporFormu />
            </SekmeGecisi>
          </TabsContent>
          <TabsContent value="ayarlar" className="mt-0">
            <SekmeGecisi>
              <AyarlarPaneli />
            </SekmeGecisi>
          </TabsContent>
          </main>
      </Tabs>
    </OturumKapisi>
  );
}
