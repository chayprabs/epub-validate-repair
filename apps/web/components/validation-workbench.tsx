"use client";

import { useEffect, useState, useTransition } from "react";

import type {
  BatchResult,
  CoverPreset,
  ConversionResult,
  ConversionTarget,
  DiffResult,
  EpubMetadata,
  MetadataUpdateResult,
  RepairFixId,
  RepairRecipe,
  RepairResult,
  UnpackEntry,
  UnpackPreview,
  ValidationResult
} from "@epubdoctor/shared-types";

const workerUrl = process.env.NEXT_PUBLIC_WORKER_URL ?? "http://localhost:8000";
const defaultRecipes: RepairRecipe[] = [
  {
    id: "manifest-mismatch",
    label: "Manifest mismatch",
    description: "Add orphaned XHTML, image, font, CSS, NCX, and nav files back to the OPF manifest."
  },
  {
    id: "spine-reference",
    label: "Broken spine references",
    description: "Remove spine entries that point to missing manifest items."
  },
  {
    id: "toc-document",
    label: "Missing TOC",
    description: "Generate a nav.xhtml document and register it in the package manifest."
  },
  {
    id: "invalid-xhtml",
    label: "Invalid XHTML",
    description: "Recover malformed XHTML files using lxml and rewrite them as well-formed XHTML."
  },
  {
    id: "mimetype-entry",
    label: "Bad mimetype entry",
    description: "Rewrite the mimetype record so it is first in the archive and stored uncompressed."
  },
  {
    id: "missing-cover",
    label: "Missing cover",
    description: "Inject a placeholder cover image and declare it in the OPF manifest."
  },
  {
    id: "container-xml",
    label: "Broken container.xml",
    description: "Restore a valid META-INF/container.xml that points at the package document."
  }
];
const conversionTargets: Array<{ label: string; value: ConversionTarget }> = [
  { label: "EPUB", value: "epub" },
  { label: "MOBI", value: "mobi" },
  { label: "AZW3", value: "azw3" },
  { label: "PDF", value: "pdf" },
  { label: "HTML", value: "html" }
];
const sampleFiles = [
  "broken-manifest.epub",
  "drm-protected.epub",
  "kdp-ready.epub",
  "invalid-xhtml.epub",
  "volume-1.epub",
  "volume-2.epub"
] as const;
const emptyMetadataForm = {
  title: "",
  subtitle: "",
  contributors: "",
  language: "",
  identifiers: "",
  publisher: "",
  publishedAt: "",
  description: "",
  subjects: "",
  rights: "",
  series: "",
  seriesIndex: "",
  custom: ""
};

export function ValidationWorkbench() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [compareFile, setCompareFile] = useState<File | null>(null);
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [recipes] = useState<RepairRecipe[]>(defaultRecipes);
  const [selectedFixes, setSelectedFixes] = useState<RepairFixId[]>([]);
  const [entries, setEntries] = useState<UnpackEntry[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [preview, setPreview] = useState<UnpackPreview | null>(null);
  const [metadataForm, setMetadataForm] = useState(emptyMetadataForm);
  const [coverPreset, setCoverPreset] = useState<CoverPreset>("kdp");
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [conversionSourceFile, setConversionSourceFile] = useState<File | null>(null);
  const [conversionTarget, setConversionTarget] = useState<ConversionTarget>("mobi");
  const [tocDepth, setTocDepth] = useState("2");
  const [pageSize, setPageSize] = useState("a4");
  const [embedFonts, setEmbedFonts] = useState(false);
  const [stripCss, setStripCss] = useState(false);
  const [conversionResult, setConversionResult] = useState<ConversionResult | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
  const [batchResult, setBatchResult] = useState<BatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [isRepairPending, startRepairTransition] = useTransition();
  const [isMetadataPending, startMetadataTransition] = useTransition();
  const [isConvertPending, startConvertTransition] = useTransition();
  const [isDiffPending, startDiffTransition] = useTransition();
  const [isBatchPending, startBatchTransition] = useTransition();

  useEffect(() => {
    if (!result) {
      setSelectedFixes([]);
      setEntries([]);
      setSelectedPath(null);
      setPreview(null);
      setConversionResult(null);
      setDiffResult(null);
      return;
    }

    const suggested = Array.from(
      new Set(
        result.messages
          .map((message) => message.fixableBy)
          .filter((value): value is RepairFixId => Boolean(value))
      )
    );
    setSelectedFixes(suggested);
    setMetadataForm({
      title: result.metadata.title ?? "",
      subtitle: result.metadata.subtitle ?? "",
      contributors: result.metadata.contributors.map((contributor) => `${contributor.name}|${contributor.role}`).join("\n"),
      language: result.metadata.language ?? "",
      identifiers: result.metadata.identifiers.map((identifier) => `${identifier.type}|${identifier.value}`).join("\n"),
      publisher: result.metadata.publisher ?? "",
      publishedAt: result.metadata.publishedAt ?? "",
      description: result.metadata.description ?? "",
      subjects: result.metadata.subjects.join(", "),
      rights: result.metadata.rights ?? "",
      series: result.metadata.series ?? "",
      seriesIndex: result.metadata.seriesIndex ?? "",
      custom: Object.entries(result.metadata.custom)
        .map(([key, value]) => `${key}=${value}`)
        .join("\n")
    });
    setCoverFile(null);
    setConversionResult(null);
  }, [result]);

  useEffect(() => {
    if (!result) {
      return;
    }

    void (async () => {
      const response = await fetch(`${workerUrl}/v1/unpack/${result.jobId}`);
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as { entries: UnpackEntry[] };
      setEntries(payload.entries);
      const nextPath = payload.entries.find((entry) => entry.kind === "xhtml")?.path ?? payload.entries[0]?.path ?? null;
      setSelectedPath(nextPath);
    })();
  }, [result]);

  useEffect(() => {
    if (!result || !selectedPath) {
      setPreview(null);
      return;
    }

    void (async () => {
      const response = await fetch(
        `${workerUrl}/v1/unpack/${result.jobId}/preview?path=${encodeURIComponent(selectedPath)}`
      );
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as UnpackPreview;
      setPreview(payload);
    })();
  }, [result, selectedPath]);

  function onSubmit() {
    if (!selectedFile && !urlInput.trim()) {
      setError("Choose an EPUB fixture, paste a remote URL, or upload a file first.");
      return;
    }

    setError(null);
    startTransition(async () => {
      const formData = new FormData();
      if (selectedFile) {
        formData.append("file", selectedFile);
      }
      if (!selectedFile && urlInput.trim()) {
        formData.append("url", urlInput.trim());
      }

      const response = await fetch(`${workerUrl}/v1/validate`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        setResult(null);
        const detail = await readErrorDetail(response);
        setError(detail ?? "Validation failed. Check that the worker is running and reachable.");
        return;
      }

      const payload = (await response.json()) as ValidationResult;
      setResult(payload);
    });
  }

  async function loadSample(name: (typeof sampleFiles)[number]) {
    setError(null);
    const response = await fetch(`/api/samples/${name}`);
    if (!response.ok) {
      setError("Sample loading failed.");
      return;
    }

    const blob = await response.blob();
    const sample = new File([blob], name, { type: "application/epub+zip" });
    setSelectedFile(sample);
    setUrlInput("");
    setResult(null);
  }

  function toggleFix(fixId: RepairFixId) {
    setSelectedFixes((current) =>
      current.includes(fixId) ? current.filter((value) => value !== fixId) : [...current, fixId]
    );
  }

  function onRepair() {
    if (!result || selectedFixes.length === 0) {
      setError("Select at least one repair recipe before applying fixes.");
      return;
    }

    setError(null);
    startRepairTransition(async () => {
      const response = await fetch(`${workerUrl}/v1/repair`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          jobId: result.jobId,
          fixes: selectedFixes
        })
      });

      if (!response.ok) {
        setError("Repair failed. The worker could not produce a repaired EPUB.");
        return;
      }

      const payload = (await response.json()) as RepairResult;
      setResult(payload.validation);
    });
  }

  function updateMetadataField(field: keyof typeof emptyMetadataForm, value: string) {
    setMetadataForm((current) => ({
      ...current,
      [field]: value
    }));
  }

  function onSaveMetadata() {
    if (!result) {
      return;
    }

    startMetadataTransition(async () => {
      const coverImageDataUrl = coverFile ? await fileToDataUrl(coverFile) : null;
      const response = await fetch(`${workerUrl}/v1/metadata`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          jobId: result.jobId,
          coverPreset,
          coverImageDataUrl,
          metadata: buildMetadataPayload(metadataForm)
        })
      });

      if (!response.ok) {
        setError("Metadata save failed. The worker could not rewrite the EPUB package.");
        return;
      }

      const payload = (await response.json()) as MetadataUpdateResult;
      setResult(payload.validation);
    });
  }

  function onConvert() {
    if (!result && !conversionSourceFile) {
      setError("Validate an EPUB or choose a source file before converting.");
      return;
    }

    setError(null);
    startConvertTransition(async () => {
      const options = {
        tocDepth: tocDepth ? Number(tocDepth) : null,
        embedFonts,
        stripCss,
        pageSize: pageSize || null
      };
      const response = conversionSourceFile
        ? await fetch(`${workerUrl}/v1/convert`, {
            method: "POST",
            body: buildConversionFormData(conversionSourceFile, conversionTarget, options)
          })
        : await fetch(`${workerUrl}/v1/convert`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              jobId: result?.jobId,
              target: conversionTarget,
              options
            })
          });

      if (!response.ok) {
        const detail = await readErrorDetail(response);
        setError(detail ?? "Conversion failed. Check that the worker can access ebook-convert.");
        setConversionResult(null);
        return;
      }

      const payload = (await response.json()) as ConversionResult;
      setConversionResult(payload);
    });
  }

  function onDiff() {
    if (!selectedFile || !compareFile) {
      setError("Choose two EPUB files before running a diff.");
      return;
    }

    setError(null);
    startDiffTransition(async () => {
      const formData = new FormData();
      formData.append("fileA", selectedFile);
      formData.append("fileB", compareFile);

      const response = await fetch(`${workerUrl}/v1/diff`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        setDiffResult(null);
        setError("Diff failed. The worker could not compare the two EPUB files.");
        return;
      }

      const payload = (await response.json()) as DiffResult;
      setDiffResult(payload);
    });
  }

  function onBatch() {
    if (!batchFile) {
      setError("Choose a ZIP archive of EPUB files before running batch mode.");
      return;
    }

    setError(null);
    startBatchTransition(async () => {
      const formData = new FormData();
      formData.append("file", batchFile);

      const response = await fetch(`${workerUrl}/v1/batch`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        setBatchResult(null);
        const detail = await readErrorDetail(response);
        setError(detail ?? "Batch mode failed. The worker could not process the ZIP archive.");
        return;
      }

      const payload = (await response.json()) as BatchResult;
      setBatchResult(payload);
    });
  }

  return (
    <section className="panel workbench">
      <div className="workbench-header">
        <div>
          <p className="eyebrow">Validation</p>
          <h2>Upload an EPUB and inspect the first F1 slice.</h2>
        </div>
        <div className="badge subtle">Worker: {workerUrl}</div>
      </div>

      <div className="upload-row">
        <label className="field-stack">
          <span className="sr-only">Choose an EPUB file to validate</span>
          <input
            accept=".epub,application/epub+zip"
            aria-label="Choose an EPUB file to validate"
            className="file-input"
            onChange={(event) => {
              setSelectedFile(event.target.files?.[0] ?? null);
              setUrlInput("");
              setResult(null);
            }}
            type="file"
          />
        </label>
        <button className="action" disabled={isPending} onClick={onSubmit} type="button">
          {isPending ? "Validating..." : "Validate EPUB"}
        </button>
      </div>

      <div className="upload-row compare-row">
        <input
          className="file-input"
          onChange={(event) => {
            setUrlInput(event.target.value);
            if (event.target.value) {
              setSelectedFile(null);
            }
          }}
          placeholder="https://example.com/book.epub"
          type="url"
          value={urlInput}
        />
        <button className="action secondary" disabled={isPending || !urlInput.trim()} onClick={onSubmit} type="button">
          Validate URL
        </button>
      </div>

      <div className="recipe-strip">
        {sampleFiles.map((sample) => (
          <button className="recipe-pill sample-pill" key={sample} onClick={() => void loadSample(sample)} type="button">
            {sample}
          </button>
        ))}
      </div>

      <div className="upload-row compare-row">
        <label className="field-stack">
          <span className="sr-only">Choose a second EPUB file for comparison</span>
          <input
            accept=".epub,application/epub+zip"
            aria-label="Choose a second EPUB file for comparison"
            className="file-input"
            onChange={(event) => {
              setCompareFile(event.target.files?.[0] ?? null);
              setDiffResult(null);
            }}
            type="file"
          />
        </label>
        <button className="action secondary" disabled={isDiffPending} onClick={onDiff} type="button">
          {isDiffPending ? "Comparing..." : "Compare EPUBs"}
        </button>
      </div>

      <div className="upload-row compare-row">
        <label className="field-stack">
          <span className="sr-only">Choose a ZIP archive for batch processing</span>
          <input
            accept=".zip,application/zip"
            aria-label="Choose a ZIP archive for batch processing"
            className="file-input"
            onChange={(event) => {
              setBatchFile(event.target.files?.[0] ?? null);
              setBatchResult(null);
            }}
            type="file"
          />
        </label>
        <button className="action secondary" disabled={isBatchPending} onClick={onBatch} type="button">
          {isBatchPending ? "Batch processing..." : "Run Pro batch"}
        </button>
      </div>

      {recipes.length > 0 ? (
        <div className="recipe-strip">
          {recipes.map((recipe) => (
            <span className="recipe-pill" key={recipe.id}>
              {recipe.label}
            </span>
          ))}
        </div>
      ) : null}

      {selectedFile ? <p className="status-line">Selected: {selectedFile.name}</p> : null}
      {urlInput ? <p className="status-line">Remote URL: {urlInput}</p> : null}
      {compareFile ? <p className="status-line">Compare against: {compareFile.name}</p> : null}
      {batchFile ? <p className="status-line">Batch archive: {batchFile.name}</p> : null}
      {error ? <p className="error-line">{error}</p> : null}

      {result ? (
        <div className="result-grid">
          <div className="result-summary">
            <div className={`badge ${result.pass ? "pass" : "fail"}`}>
              {result.pass ? "Pass" : "Needs repair"}
            </div>
            <p>EPUB {result.epubVersion}</p>
            <pre>{JSON.stringify(result.counts, null, 2)}</pre>
            <div className="artifact-links">
              <a href={result.artifacts.htmlUrl} rel="noreferrer" target="_blank">
                HTML report
              </a>
              <a href={result.artifacts.jsonUrl} rel="noreferrer" target="_blank">
                JSON report
              </a>
            </div>
          </div>

          <div className="result-main">
            <section className="repair-panel">
              <div className="message-topline">
                <h3>Repair checklist</h3>
                <button
                  className="action secondary"
                  disabled={isRepairPending || selectedFixes.length === 0 || result.pass}
                  onClick={onRepair}
                  type="button"
                >
                  {isRepairPending ? "Repairing..." : "Apply selected"}
                </button>
              </div>
              <div className="repair-list">
                {recipes.map((recipe) => {
                  const suggested = result.messages.some((message) => message.fixableBy === recipe.id);
                  return (
                    <label className={`repair-item ${suggested ? "suggested" : ""}`} key={recipe.id}>
                      <input
                        checked={selectedFixes.includes(recipe.id)}
                        onChange={() => toggleFix(recipe.id)}
                        type="checkbox"
                      />
                      <span>
                        <strong>{recipe.label}</strong>
                        <span className="message-suggestion">{recipe.description}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
            </section>

            <section className="metadata-panel">
              <div className="message-topline">
                <h3>Metadata editor</h3>
                <button
                  className="action secondary"
                  disabled={isMetadataPending}
                  onClick={onSaveMetadata}
                  type="button"
                >
                  {isMetadataPending ? "Saving..." : "Save metadata"}
                </button>
              </div>
              <div className="metadata-grid">
                <label>
                  <span>Title</span>
                  <input
                    onChange={(event) => updateMetadataField("title", event.target.value)}
                    type="text"
                    value={metadataForm.title}
                  />
                </label>
                <label>
                  <span>Subtitle</span>
                  <input
                    onChange={(event) => updateMetadataField("subtitle", event.target.value)}
                    type="text"
                    value={metadataForm.subtitle}
                  />
                </label>
                <label>
                  <span>Language</span>
                  <input
                    onChange={(event) => updateMetadataField("language", event.target.value)}
                    type="text"
                    value={metadataForm.language}
                  />
                </label>
                <label>
                  <span>Publisher</span>
                  <input
                    onChange={(event) => updateMetadataField("publisher", event.target.value)}
                    type="text"
                    value={metadataForm.publisher}
                  />
                </label>
                <label>
                  <span>Published</span>
                  <input
                    onChange={(event) => updateMetadataField("publishedAt", event.target.value)}
                    type="text"
                    value={metadataForm.publishedAt}
                  />
                </label>
                <label>
                  <span>Rights</span>
                  <input
                    onChange={(event) => updateMetadataField("rights", event.target.value)}
                    type="text"
                    value={metadataForm.rights}
                  />
                </label>
                <label>
                  <span>Series</span>
                  <input
                    onChange={(event) => updateMetadataField("series", event.target.value)}
                    type="text"
                    value={metadataForm.series}
                  />
                </label>
                <label>
                  <span>Series number</span>
                  <input
                    onChange={(event) => updateMetadataField("seriesIndex", event.target.value)}
                    type="text"
                    value={metadataForm.seriesIndex}
                  />
                </label>
                <label className="metadata-span-2">
                  <span>Description</span>
                  <textarea
                    onChange={(event) => updateMetadataField("description", event.target.value)}
                    value={metadataForm.description}
                  />
                </label>
                <label>
                  <span>Subjects</span>
                  <input
                    onChange={(event) => updateMetadataField("subjects", event.target.value)}
                    placeholder="Comma separated"
                    type="text"
                    value={metadataForm.subjects}
                  />
                </label>
                <label>
                  <span>Contributors</span>
                  <textarea
                    onChange={(event) => updateMetadataField("contributors", event.target.value)}
                    placeholder="Name|role per line"
                    value={metadataForm.contributors}
                  />
                </label>
                <label>
                  <span>Identifiers</span>
                  <textarea
                    onChange={(event) => updateMetadataField("identifiers", event.target.value)}
                    placeholder="type|value per line"
                    value={metadataForm.identifiers}
                  />
                </label>
                <label>
                  <span>Custom metadata</span>
                  <textarea
                    onChange={(event) => updateMetadataField("custom", event.target.value)}
                    placeholder="key=value per line"
                    value={metadataForm.custom}
                  />
                </label>
                <label>
                  <span>Cover preset</span>
                  <select onChange={(event) => setCoverPreset(event.target.value as CoverPreset)} value={coverPreset}>
                    <option value="kdp">KDP</option>
                    <option value="apple">Apple Books</option>
                    <option value="kobo">Kobo</option>
                  </select>
                </label>
                <label>
                  <span>Replace cover</span>
                  <input
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(event) => setCoverFile(event.target.files?.[0] ?? null)}
                    type="file"
                  />
                  {coverFile ? <span className="message-meta">{coverFile.name}</span> : null}
                </label>
              </div>
            </section>

            <section className="convert-panel">
              <div className="message-topline">
                <h3>Convert</h3>
                <button
                  className="action secondary"
                  disabled={isConvertPending}
                  onClick={onConvert}
                  type="button"
                >
                  {isConvertPending ? "Converting..." : "Run conversion"}
                </button>
              </div>
              <div className="convert-grid">
                <label>
                  <span>Source file</span>
                  <input
                    accept=".epub,.mobi,.azw3,.html,.htm,.pdf"
                    onChange={(event) => setConversionSourceFile(event.target.files?.[0] ?? null)}
                    type="file"
                  />
                  <span className="message-meta">
                    {conversionSourceFile
                      ? `Using ${conversionSourceFile.name}`
                      : result
                        ? `Using validated job ${result.jobId}`
                        : "Upload MOBI, AZW3, HTML, PDF, or EPUB for direct conversion."}
                  </span>
                </label>
                <label>
                  <span>Target format</span>
                  <select onChange={(event) => setConversionTarget(event.target.value as ConversionTarget)} value={conversionTarget}>
                    {conversionTargets.map((target) => (
                      <option key={target.value} value={target.value}>
                        {target.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>TOC depth</span>
                  <input onChange={(event) => setTocDepth(event.target.value)} type="number" value={tocDepth} />
                </label>
                <label>
                  <span>Page size</span>
                  <input onChange={(event) => setPageSize(event.target.value)} type="text" value={pageSize} />
                </label>
                <label className="toggle-row">
                  <input checked={embedFonts} onChange={(event) => setEmbedFonts(event.target.checked)} type="checkbox" />
                  <span>Embed fonts</span>
                </label>
                <label className="toggle-row">
                  <input checked={stripCss} onChange={(event) => setStripCss(event.target.checked)} type="checkbox" />
                  <span>Strip CSS</span>
                </label>
              </div>
              {conversionResult ? (
                <div className="convert-result">
                  <div className="artifact-links">
                    <a href={conversionResult.artifactUrl} rel="noreferrer" target="_blank">
                      Download {conversionResult.target.toUpperCase()}
                    </a>
                  </div>
                  <pre>{conversionResult.log}</pre>
                </div>
              ) : (
                <p className="message-suggestion">
                  Convert the current job to EPUB, MOBI, AZW3, PDF, or HTML with Calibre-compatible options.
                </p>
              )}
            </section>

            {batchResult ? (
              <section className="convert-panel">
                <div className="message-topline">
                  <h3>Batch report</h3>
                  <span className="message-meta">{batchResult.items.length} files</span>
                </div>
                <div className="artifact-links">
                  <a href={batchResult.csvUrl} rel="noreferrer" target="_blank">
                    Download CSV
                  </a>
                  <a href={batchResult.repairedZipUrl} rel="noreferrer" target="_blank">
                    Download repaired ZIP
                  </a>
                </div>
                <div className="batch-grid">
                  {batchResult.items.map((item) => (
                    <article className="diff-card" key={item.filename}>
                      <div className="message-topline">
                        <strong>{item.filename}</strong>
                        <span>{item.status}</span>
                      </div>
                      <p className="message-meta">
                        Errors: {item.originalErrors} {"->"} {item.repairedErrors}
                      </p>
                      {item.appliedFixes.length > 0 ? (
                        <p className="message-suggestion">Fixes: {item.appliedFixes.join(", ")}</p>
                      ) : null}
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            <div className="message-list">
              {result.messages.map((message) => (
                <article className={`message-card severity-${message.severity}`} key={`${message.id}-${message.file}`}>
                  <div className="message-topline">
                    <strong>{message.id}</strong>
                    <span>{message.severity}</span>
                  </div>
                  <p>{message.message}</p>
                  <p className="message-meta">{message.file}</p>
                  {message.suggestion ? <p className="message-suggestion">{message.suggestion}</p> : null}
                </article>
              ))}
            </div>

            {entries.length > 0 ? (
              <section className="structure-panel">
                <div className="message-topline">
                  <h3>Structure preview</h3>
                  <span className="message-meta">{entries.length} files</span>
                </div>
                <div className="structure-grid">
                  <div className="file-list">
                    {entries.map((entry) => (
                      <button
                        className={`file-row ${selectedPath === entry.path ? "active" : ""}`}
                        key={entry.path}
                        onClick={() => setSelectedPath(entry.path)}
                        type="button"
                      >
                        <span>{entry.path}</span>
                        <span className="message-meta">{entry.kind}</span>
                      </button>
                    ))}
                  </div>
                  <div className="preview-pane">
                    {preview?.kind === "image" && preview.dataUrl ? (
                      <img alt={preview.path} className="preview-image" src={preview.dataUrl} />
                    ) : null}
                    {preview?.kind === "xhtml" && preview.text ? (
                      <iframe
                        className="preview-frame"
                        sandbox=""
                        srcDoc={preview.text}
                        title={preview.path}
                      />
                    ) : null}
                    {preview && preview.kind !== "image" && preview.kind !== "xhtml" ? (
                      <pre>{preview.text}</pre>
                    ) : null}
                  </div>
                </div>
              </section>
            ) : null}

            {diffResult ? (
              <section className="diff-panel">
                <div className="message-topline">
                  <h3>Diff</h3>
                  <span className="message-meta">
                    {diffResult.structure.length + diffResult.metadata.length + diffResult.chapters.length} changes
                  </span>
                </div>
                <div className="diff-grid">
                  <div className="diff-column">
                    <h4>Structure</h4>
                    {diffResult.structure.length === 0 ? (
                      <p className="message-suggestion">No structure changes.</p>
                    ) : (
                      diffResult.structure.map((change) => (
                        <article className="diff-card" key={`${change.change}-${change.path}`}>
                          <strong>{change.change}</strong>
                          <p>{change.path}</p>
                        </article>
                      ))
                    )}
                  </div>
                  <div className="diff-column">
                    <h4>Metadata</h4>
                    {diffResult.metadata.length === 0 ? (
                      <p className="message-suggestion">No metadata changes.</p>
                    ) : (
                      diffResult.metadata.map((change) => (
                        <article className="diff-card" key={change.field}>
                          <strong>{change.field}</strong>
                          <p className="message-meta">Before: {change.before ?? "(empty)"}</p>
                          <p className="message-meta">After: {change.after ?? "(empty)"}</p>
                        </article>
                      ))
                    )}
                  </div>
                  <div className="diff-column diff-column-wide">
                    <h4>Chapter text</h4>
                    {diffResult.chapters.length === 0 ? (
                      <p className="message-suggestion">No chapter changes.</p>
                    ) : (
                      diffResult.chapters.map((change) => (
                        <article className="diff-card" key={change.path}>
                          <strong>{change.path}</strong>
                          <p className="message-meta">Before: {change.before ?? "(missing)"}</p>
                          <p className="message-meta">After: {change.after ?? "(missing)"}</p>
                        </article>
                      ))
                    )}
                  </div>
                </div>
              </section>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function buildMetadataPayload(form: typeof emptyMetadataForm): EpubMetadata {
  return {
    title: form.title || undefined,
    subtitle: form.subtitle || undefined,
    contributors: form.contributors
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [name, role] = line.split("|").map((value) => value.trim());
        return {
          name,
          role: role || "aut"
        };
      }),
    language: form.language || undefined,
    identifiers: form.identifiers
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [type, value] = line.split("|").map((part) => part.trim());
        return {
          type: type || "identifier",
          value: value || ""
        };
      })
      .filter((identifier) => identifier.value),
    publisher: form.publisher || undefined,
    publishedAt: form.publishedAt || undefined,
    description: form.description || undefined,
    subjects: form.subjects
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean),
    rights: form.rights || undefined,
    series: form.series || undefined,
    seriesIndex: form.seriesIndex || undefined,
    custom: Object.fromEntries(
      form.custom
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const separatorIndex = line.indexOf("=");
          if (separatorIndex === -1) {
            return [line, ""];
          }
          return [line.slice(0, separatorIndex).trim(), line.slice(separatorIndex + 1).trim()];
        })
    )
  };
}

async function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function readErrorDetail(response: Response): Promise<string | null> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? null;
  } catch {
    return null;
  }
}

function buildConversionFormData(
  file: File,
  target: ConversionTarget,
  options: { tocDepth: number | null; embedFonts: boolean; stripCss: boolean; pageSize: string | null }
): FormData {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("target", target);
  if (options.tocDepth !== null) {
    formData.append("tocDepth", String(options.tocDepth));
  }
  formData.append("embedFonts", String(options.embedFonts));
  formData.append("stripCss", String(options.stripCss));
  if (options.pageSize) {
    formData.append("pageSize", options.pageSize);
  }
  return formData;
}
