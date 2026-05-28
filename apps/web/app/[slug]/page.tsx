import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { seoPageMap, seoPages } from "../../lib/seo-pages";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return seoPages.map((page) => ({ slug: page.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = seoPageMap.get(slug);
  if (!page) {
    return {};
  }

  return {
    title: `${page.title} | EpubDoctor`,
    description: page.description
  };
}

export default async function SeoLandingPage({ params }: PageProps) {
  const { slug } = await params;
  const page = seoPageMap.get(slug);
  if (!page) {
    notFound();
  }

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">{page.eyebrow}</p>
          <h1>{page.title}</h1>
          <p className="lede">{page.summary}</p>
        </div>
        <div className="badge">Server-side ebook workflow</div>
      </header>

      <section className="panel seo-panel">
        <h2>Why this route exists</h2>
        <p className="lede">
          {page.description}
        </p>
        <ul>
          {page.bullets.map((bullet) => (
            <li key={bullet}>{bullet}</li>
          ))}
        </ul>
      </section>

      <section className="panel seo-panel">
        <h2>Use the full workbench</h2>
        <p className="lede">
          The main EpubDoctor surface combines validation, repair, unpack,
          metadata editing, conversion, diff, and batch flows in one page.
        </p>
        <div className="cta-row">
          <Link className="action" href="/">
            Open the workbench
          </Link>
          <a className="action secondary" href="https://github.com/chayprabs/epub-validate-repair">
            View the repository
          </a>
        </div>
      </section>
    </main>
  );
}
