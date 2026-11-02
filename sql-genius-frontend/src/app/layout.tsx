'use client';

import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <title>SQL Genius AI | Natural-Language SQL and Analytics Playground</title>
        <meta name="description" content="Inspect schema-aware SQL and run supported read-only queries locally against deterministic sample data." />
      </head>
      <body className="font-sans">
        {children}
      </body>
    </html>
  );
}
