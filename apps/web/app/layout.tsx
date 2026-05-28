import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EpubDoctor",
  description:
    "Validate, repair and convert EPUB, MOBI and AZW3 ebooks online with epubcheck and Calibre.",
  icons: {
    icon: [
      {
        url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%23101822'/%3E%3Cpath d='M18 16h20a10 10 0 0 1 10 10v22H28a10 10 0 0 0-10-10V16Z' fill='%23f1b24a'/%3E%3Cpath d='M28 16h18v22H28a10 10 0 0 0-10 10V26a10 10 0 0 1 10-10Z' fill='%23f7f7f7' fill-opacity='.86'/%3E%3C/svg%3E"
      }
    ]
  }
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
