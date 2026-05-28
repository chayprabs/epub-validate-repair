"use client";

import { useState, useTransition } from "react";

import type { ValidationResult } from "@epubdoctor/shared-types";

const workerUrl = process.env.NEXT_PUBLIC_WORKER_URL ?? "http://localhost:8000";

export function ValidationWorkbench() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

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
        </div>
      ) : null}
    </section>
  );
}
