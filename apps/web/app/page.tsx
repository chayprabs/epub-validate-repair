import Link from "next/link";
import { WorkbenchShell } from "../components/workbench-shell";
import { seoPages } from "../lib/seo-pages";

const highlights = [
  "Validate EPUBs and export HTML or JSON reports.",
  "Repair common epubcheck failures with one checklist.",
  "Edit metadata, swap covers, convert formats, diff volumes, and run ZIP batch mode."
];

const quickSteps = [
  "Upload an EPUB, paste a URL, or start from a sample fixture.",
  "Review the pass/fail summary, error counts, and file-level issues.",
  "Move through Repairs, Metadata, Structure, Convert, and Diff without leaving the page."
];

export default function HomePage() {
  return (
    <main className="shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">EpubDoctor</p>
          <h1>Fix broken EPUBs without digging through the package by hand.</h1>
          <p className="lede">
            Validate, repair, unpack, convert, and update ebook metadata in one
            focused workbench for EPUB, MOBI, and AZW3 publishing jobs.
          </p>
          <div className="hero-actions">
            <a className="action" href="#workbench">
              Open the workbench
            </a>
            <a className="action secondary" href="#entry-points">
              Browse guided entry points
            </a>
          </div>
        </div>
        <div className="hero-side">
          <div className="hero-card">
            <p className="eyebrow subtle-text">Straight to the point</p>
            <ul className="hero-list">
              {highlights.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
          </div>
        </div>
      </header>
      <section className="panel quickstart-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Start Here</p>
            <h2>Use the same flow whether you are validating, repairing, or converting.</h2>
          </div>
          <div className="badge subtle">Validation, repair, metadata, convert, diff, batch</div>
        </div>
        <ol className="step-list">
          {quickSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>
      <section className="panel seo-panel" id="entry-points">
        <h2>Guided entry points</h2>
        <p className="lede">
          These focused landing pages all route back into the same workbench,
          so readers can enter from the exact job they need.
        </p>
        <div className="link-grid">
          {seoPages.map((page) => (
            <Link className="link-card" href={`/${page.slug}`} key={page.slug}>
              <strong>{page.title}</strong>
              <span>{page.description}</span>
            </Link>
          ))}
        </div>
      </section>
      <div id="workbench">
        <WorkbenchShell />
      </div>
    </main>
  );
}
