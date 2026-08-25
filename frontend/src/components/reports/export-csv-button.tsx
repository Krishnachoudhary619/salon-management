"use client";

import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";

interface ExportCsvButtonProps {
  label: string;
  disabled?: boolean;
  onExport: () => void;
}

export function ExportCsvButton({ label, disabled, onExport }: ExportCsvButtonProps) {
  return (
    <Button type="button" variant="outline" disabled={disabled} onClick={onExport}>
      <Download className="h-4 w-4" />
      {label}
    </Button>
  );
}
