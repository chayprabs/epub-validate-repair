import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EpubDoctor",
  description:
    "Validate, repair and convert EPUB, MOBI and AZW3 ebooks online with epubcheck and Calibre."
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
