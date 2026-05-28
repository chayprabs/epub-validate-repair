export type ValidationSeverity = "error" | "warning" | "info" | "usage";

export interface EpubcheckMessage {
  id: string;
  severity: ValidationSeverity;
  message: string;
  file: string;
  line?: number;
  column?: number;
  suggestion?: string;
  fixableBy?: string;
}

export interface ValidationResult {
  jobId: string;
  epubVersion: "2.0" | "3.0" | "3.1" | "3.2" | "3.3";
  pass: boolean;
  counts: Record<ValidationSeverity, number>;
  messages: EpubcheckMessage[];
}
