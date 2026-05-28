export type ValidationSeverity = "error" | "warning" | "info" | "usage";
export type RepairFixId =
  | "manifest-mismatch"
  | "spine-reference"
  | "toc-document"
  | "invalid-xhtml"
  | "mimetype-entry"
  | "missing-cover"
  | "container-xml";

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

export interface ManifestItem {
  id: string;
  href: string;
  mediaType: string;
}

export interface SpineItem {
  idref: string;
  href?: string | null;
}

export interface TocItem {
  label: string;
  href: string;
  children: TocItem[];
}

export interface EpubMetadata {
  title?: string;
  subtitle?: string;
  contributors: string[];
  language?: string;
  identifiers: string[];
  publisher?: string;
  publishedAt?: string;
  description?: string;
  subjects: string[];
  rights?: string;
  series?: string;
  seriesIndex?: string;
  custom: Record<string, string>;
}

export interface ValidationArtifacts {
  htmlUrl: string;
  jsonUrl: string;
}

export interface RepairRecipe {
  id: RepairFixId;
  label: string;
  description: string;
}

export interface ValidationResult {
  jobId: string;
  epubVersion: "2.0" | "3.0" | "3.1" | "3.2" | "3.3";
  pass: boolean;
  counts: Record<ValidationSeverity, number>;
  messages: EpubcheckMessage[];
  metadata: EpubMetadata;
  spine: SpineItem[];
  manifest: ManifestItem[];
  toc: TocItem[];
  artifacts: ValidationArtifacts;
}

export interface RepairResult {
  jobId: string;
  appliedFixes: RepairFixId[];
  validation: ValidationResult;
}
