export type SeoPage = {
  slug: string;
  title: string;
  description: string;
  eyebrow: string;
  summary: string;
  bullets: string[];
};

export const seoPages: SeoPage[] = [
  {
    slug: "epub-validator-online",
    title: "EPUB Validator Online",
    description:
      "Validate EPUB files online with EpubDoctor, inspect file-level issues, and download HTML or JSON validation reports.",
    eyebrow: "Validation",
    summary:
      "Upload a broken EPUB, inspect file and line context, and export the validation report before you apply any repairs.",
    bullets: [
      "Runs EPUB validation with file, line, column, and fix suggestions.",
      "Exports both HTML and JSON reports for author, ops, or QA workflows.",
      "Works alongside the repair checklist so you can re-validate after each fix."
    ]
  },
  {
    slug: "epub-to-mobi",
    title: "EPUB to MOBI Converter",
    description:
      "Convert EPUB to MOBI with EpubDoctor using Calibre-backed server-side processing and downloadable artifacts.",
    eyebrow: "Convert",
    summary:
      "Turn EPUB files into MOBI with the same workbench used for validation, metadata edits, and repair before export.",
    bullets: [
      "Server-side conversion powered by Calibre-compatible tooling.",
      "Adjust TOC depth, font embedding, CSS stripping, and page size options.",
      "Keep conversion logs and download the converted artifact from the same job."
    ]
  },
  {
    slug: "mobi-to-epub",
    title: "MOBI to EPUB Converter",
    description:
      "Convert MOBI to EPUB online with EpubDoctor and continue into validation, repair, diff, or metadata editing.",
    eyebrow: "Convert",
    summary:
      "Start from a MOBI upload, convert to EPUB, and then move directly into validation or metadata cleanup in the same interface.",
    bullets: [
      "Accepts direct MOBI uploads for Calibre-backed conversion.",
      "Feeds the converted EPUB into the rest of the repair workflow.",
      "Useful for Kobo, archive, and self-publishing preparation flows."
    ]
  },
  {
    slug: "epub-metadata-editor",
    title: "EPUB Metadata Editor",
    description:
      "Edit EPUB title, subtitle, contributors, identifiers, rights, subjects, series, and cover metadata with EpubDoctor.",
    eyebrow: "Metadata",
    summary:
      "Update title pages, contributors, ISBN values, series data, and custom metadata without unpacking the EPUB by hand.",
    bullets: [
      "Supports title, subtitle, contributor roles, language, rights, and subjects.",
      "Edits ISBN, UUID, DOI, publisher, description, and series information.",
      "Lets you replace the cover with KDP, Apple Books, or Kobo presets."
    ]
  },
  {
    slug: "epub-cover-replace",
    title: "EPUB Cover Replace Tool",
    description:
      "Replace or add an EPUB cover image with EpubDoctor and auto-resize it for KDP, Apple Books, or Kobo targets.",
    eyebrow: "Cover",
    summary:
      "Upload a fresh cover, apply a device preset, and re-validate the package after the cover metadata is rewritten.",
    bullets: [
      "Handles missing-cover repair and explicit cover replacement flows.",
      "Applies KDP, Apple Books, or Kobo resizing presets before packaging.",
      "Works as part of the metadata editor so you can ship one updated EPUB."
    ]
  },
  {
    slug: "kdp-epub-check",
    title: "KDP EPUB Check Workflow",
    description:
      "Run a KDP-focused EPUB validation and repair workflow with EpubDoctor before publishing to Kindle Direct Publishing.",
    eyebrow: "Publishing",
    summary:
      "Check a KDP-bound EPUB for packaging issues, repair common failures, and export a cleaner file for upload review.",
    bullets: [
      "Targets common packaging issues that trigger KDP upload failures.",
      "Pairs validation findings with one-click repair recipes.",
      "Supports follow-up conversion, metadata cleanup, and structure preview."
    ]
  }
];

export const seoPageMap = new Map(seoPages.map((page) => [page.slug, page]));
