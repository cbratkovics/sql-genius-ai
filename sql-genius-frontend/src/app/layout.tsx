'use client';

import "./globals.css";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useState } from 'react';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        refetchOnWindowFocus: false,
      },
    },
  }));

  return (
    <html lang="en">
      <head>
        <title>SQL Genius AI | Natural-Language SQL and Analytics Playground</title>
        <meta name="description" content="Inspect schema-aware SQL and run supported read-only queries locally against deterministic sample data." />
      </head>
      <body className="font-sans">
        <QueryClientProvider client={queryClient}>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#1F2937',
                color: '#fff',
              },
            }}
          />
        </QueryClientProvider>
      </body>
    </html>
  );
}
