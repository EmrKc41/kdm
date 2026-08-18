"use client";

import { LogOut } from "lucide-react";
import { cikisYap } from "@/lib/oturum";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function CikisDugmesi() {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon" onClick={() => void cikisYap()} aria-label="Oturumu kapat">
          <LogOut className="size-4" aria-hidden />
        </Button>
      </TooltipTrigger>
      <TooltipContent>Oturumu kapat</TooltipContent>
    </Tooltip>
  );
}
