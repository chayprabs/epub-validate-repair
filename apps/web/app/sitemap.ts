import type { MetadataRoute } from "next";
import { seoPages } from "../lib/seo-pages";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://epub-doctor.example.com";
  return [
    {
      url: `${baseUrl}/`,
      changeFrequency: "weekly",
      priority: 1
    },
    ...seoPages.map((page) => ({
      url: `${baseUrl}/${page.slug}`,
      changeFrequency: "weekly" as const,
      priority: 0.8
    }))
  ];
}
