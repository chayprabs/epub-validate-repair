"use client";

import { useEffect, useState, useTransition } from "react";

import type {
  RepairFixId,
  RepairRecipe,
  RepairResult,
  UnpackEntry,
  UnpackPreview,
  ValidationResult
} from "@epubdoctor/shared-types";

const workerUrl = process.env.NEXT_PUBLIC_WORKER_URL ?? "http://localhost:8000";

export function ValidationWorkbench() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [recipes, setRecipes] = useState<RepairRecipe[]>([]);
  const [selectedFixes, setSelectedFixes] = useState<RepairFixId[]>([]);
  const [entries, setEntries] = useState<UnpackEntry[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [preview, setPreview] = useState<UnpackPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [isRepairPending, startRepairTransition] = useTransition();

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
