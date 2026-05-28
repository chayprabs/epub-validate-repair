import { WorkbenchShell } from "../components/workbench-shell";

const features = [
  "Fixture-backed validation API with downloadable HTML and JSON reports",
  "Worker-side artifact storage and shared validation types",
  "Next.js upload workbench ready for repair, metadata, convert, and diff tabs"
];

export default function HomePage() {
  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">EpubDoctor</p>
          <h1>Validate, repair, and convert broken ebooks.</h1>
          <p className="lede">
            Server-side EPUB, MOBI, and AZW3 tooling with epubcheck,
            Calibre, and an XHTML-safe preview surface.
          </p>
        </div>
        <div className="badge">Pattern 1 bootstrap in progress</div>
      </header>
      <section className="panel">
        <h2>Current implementation slice</h2>
        <ul>
          {features.map((feature) => (
            <li key={feature}>{feature}</li>
          ))}
        </ul>
      </section>
      <WorkbenchShell />
    </main>
  );
}
