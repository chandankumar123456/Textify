import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Textify - AI Document Intelligence",
  description: "Transform handwritten study material into structured learning resources",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-50 text-gray-900">
        {children}
      </body>
    </html>
  );
}
