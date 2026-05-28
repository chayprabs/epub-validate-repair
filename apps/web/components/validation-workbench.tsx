"use client";

import { useEffect, useState, useTransition } from "react";

import type {
  CoverPreset,
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
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [recipes, setRecipes] = useState<RepairRecipe[]>([]);
  const [selectedFixes, setSelectedFixes] = useState<RepairFixId[]>([]);
  const [entries, setEntries] = useState<UnpackEntry[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [preview, setPreview] = useState<UnpackPreview | null>(null);
  const [metadataForm, setMetadataForm] = useState(emptyMetadataForm);
  const [coverPreset, setCoverPreset] = useState<CoverPreset>("kdp");
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [isRepairPending, startRepairTransition] = useTransition();
  const [isMetadataPending, startMetadataTransition] = useTransition();

  useEffect(() => {
    void (async () => {
      const response = await fetch(`${workerUrl}/v1/repair/recipes`);
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as { recipes: RepairRecipe[] };
      setRecipes(payload.recipes);
    })();
  }, []);

  useEffect(() => {
    if (!result) {
      setSelectedFixes([]);
      setEntries([]);
      setSelectedPath(null);
      setPreview(null);
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
    if (!selectedFile) {
      setError("Choose an EPUB fixture or upload a file first.");
      return;
    }

    setError(null);
    startTransition(async () => {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${workerUrl}/v1/validate`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        setResult(null);
        setError("Validation failed. Check that the worker is running and reachable.");
        return;
      }

      const payload = (await response.json()) as ValidationResult;
      setResult(payload);
    });
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
        <input
          accept=".epub,application/epub+zip"
          className="file-input"
          onChange={(event) => {
            setSelectedFile(event.target.files?.[0] ?? null);
            setResult(null);
          }}
          type="file"
        />
        <button className="action" disabled={isPending} onClick={onSubmit} type="button">
          {isPending ? "Validating..." : "Validate EPUB"}
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
