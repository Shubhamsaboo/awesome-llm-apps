# TripCraft AI - Frontend Client

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Prerequisites

Before you begin, ensure you have the following installed:
- Node.js 20.x or higher
- pnpm 9.15.0 or higher (recommended) or npm/yarn
- PostgreSQL database

## Setup Instructions

### 1. Install Dependencies

Using pnpm (recommended):
```bash
pnpm install
```

Or using npm:
```bash
npm install
```

### 2. Environment Configuration

Create a `.env.local` file in the root of the client directory by copying the example:

```bash
cp .env.example .env.local
```

Then edit `.env.local` and configure the following environment variables:

```bash
# Application Base URL
# For local development:
NEXT_PUBLIC_BASE_URL=http://localhost:3000

# Database connection URL (PostgreSQL)
# Format: postgresql://username:password@host:port/database
DATABASE_URL=postgresql://user:password@localhost:5432/tripcraft

# Backend API URL (if backend is separate)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Database Setup

Initialize the database with Prisma:

```bash
# Generate Prisma Client
pnpm prisma generate

# Run database migrations
pnpm prisma migrate dev
```

### 4. Run the Development Server

Start the development server:

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Common Issues and Solutions

### Issue: "TypeError: Failed to parse URL from undefined/api/auth/get-session"

**Cause**: The `NEXT_PUBLIC_BASE_URL` environment variable is not set.

**Solution**: 
1. Create a `.env.local` file if it doesn't exist
2. Add `NEXT_PUBLIC_BASE_URL=http://localhost:3000`
3. Restart the development server

### Issue: Database connection errors

**Cause**: PostgreSQL is not running or DATABASE_URL is incorrect.

**Solution**:
1. Ensure PostgreSQL is running
2. Verify DATABASE_URL in `.env.local` is correct
3. Run `pnpm prisma migrate dev` to set up the database

### Issue: Prisma Client errors

**Cause**: Prisma Client is not generated or out of sync.

**Solution**:
```bash
pnpm prisma generate
```

## Project Structure

```
client/
├── app/              # Next.js app directory
│   ├── api/          # API routes
│   ├── auth/         # Authentication pages
│   ├── plan/         # Travel planning pages
│   └── plans/        # Travel plans listing
├── components/       # Reusable React components
├── lib/              # Utility functions and configurations
│   ├── auth.ts       # Better-auth configuration
│   └── auth-client.ts # Auth client setup
├── prisma/           # Database schema and migrations
└── middleware.ts     # Next.js middleware for authentication
```

## Technologies Used

- **Next.js 15.3.3** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Prisma** - Database ORM
- **Better-auth** - Authentication
- **Radix UI** - Accessible component primitives

## Scripts

- `pnpm dev` - Start development server with Turbopack
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

