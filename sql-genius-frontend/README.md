# SQL Genius AI - Frontend

Next.js-based frontend application for SQL Genius AI with TypeScript, React Query, and Tailwind CSS.

## Prerequisites

- Node.js 18+
- npm or yarn

## Environment Variables

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

The `.env.local` file should contain:
```
NEXT_PUBLIC_API_BASE_URL=https://sql-genius-api.onrender.com
NEXT_PUBLIC_APP_NAME=SQL Genius AI
```

For local development, you can override the API URL:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Installation

```bash
# Install dependencies
npm install
```

## Development

```bash
# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Build

```bash
# Build for production
npm run build

# Start production server locally
npm start
```

## Code Quality

```bash
# Run linter
npm run lint

# Type checking
npm run type-check
```

## API Integration

The frontend uses a typed API client located at `src/lib/api.ts` that automatically handles:
- Relative API paths via `/api/*` proxy
- Type-safe requests and responses
- Authentication token management
- Error handling

### Vercel Rewrites

The application uses Vercel rewrites configured in `vercel.json` to proxy API requests:
- All requests to `/api/*` are forwarded to the backend at `https://sql-genius-api.onrender.com`
- This avoids CORS issues and keeps the API URL internal
- Security headers are automatically added to all responses

### Example API Usage

```typescript
import { post, get } from '@/lib/api';

// Generate SQL
const result = await post<{ sql: string; explanation: string }>(
  '/v1/demo/sql-generate',
  { query: 'Show all users', schema_context: '...' }
);

// Get metrics
const metrics = await get('/v1/demo/metrics');
```

## Project Structure

```
sql-genius-frontend/
├── src/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # Reusable React components
│   ├── hooks/        # Custom React hooks
│   └── lib/          # Utilities and API client
├── public/           # Static assets
├── vercel.json       # Vercel configuration
└── .env.local.example # Environment variables template
```

## Features

- **SQL Generation**: Natural language to SQL conversion
- **Interactive Playground**: Test and execute queries
- **Real-time Metrics**: Performance monitoring dashboard
- **Schema Templates**: Pre-built database schemas
- **Error Handling**: Global error boundary with recovery

## Deployment

### Deploy to Vercel

```bash
npx vercel --prod
```

Or connect your GitHub repository to Vercel for automatic deployments.

### Production Checklist

1. Set environment variables in Vercel dashboard
2. Configure domain and SSL
3. Verify API rewrites are working
4. Test error boundaries
5. Monitor performance metrics

## Troubleshooting

### API Connection Issues
- Verify `NEXT_PUBLIC_API_BASE_URL` is set correctly
- Check that backend is running and accessible
- Ensure CORS is configured properly on backend

### Build Errors
- Clear `.next` directory: `rm -rf .next`
- Clear node_modules: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run type-check`

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Documentation](https://tanstack.com/query)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)