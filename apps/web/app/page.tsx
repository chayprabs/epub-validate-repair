const features = [
  "Validation with epubcheck severity mapping",
  "Opt-in repair recipes for common EPUB faults",
  "Metadata editing, conversion, diff, and batch workflows"
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
    </main>
  );
}
