export type ValidationSeverity = "error" | "warning" | "info" | "usage";
export type CoverPreset = "kdp" | "apple" | "kobo";
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

export interface Contributor {
  name: string;
  role: string;
}

export interface Identifier {
  type: string;
  value: string;
}

export interface EpubMetadata {
  title?: string;
  subtitle?: string;
  contributors: Contributor[];
  language?: string;
  identifiers: Identifier[];
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

export interface MetadataUpdateResult {
  jobId: string;
  validation: ValidationResult;
}

export type UnpackKind =
  | "xhtml"
  | "css"
  | "image"
  | "xml"
  | "opf"
  | "ncx"
  | "font"
  | "text"
  | "binary";

export interface UnpackEntry {
  path: string;
  kind: UnpackKind;
  size: number;
}

export interface UnpackPreview {
  path: string;
  kind: UnpackKind;
  text?: string | null;
  dataUrl?: string | null;
}
