# TripCraft AI - Setup and Testing Guide

This guide provides detailed instructions for setting up and testing the TripCraft AI application.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Ensure you have the following installed on your system:

### Required Software
- **Node.js**: Version 20.x or higher
  - Download from [nodejs.org](https://nodejs.org/)
  - Verify: `node --version`
- **pnpm**: Version 9.15.0 or higher
  - Install: `npm install -g pnpm@9.15.0`
  - Verify: `pnpm --version`
- **Python**: Version 3.12 or higher
  - Download from [python.org](https://www.python.org/)
  - Verify: `python --version`
- **PostgreSQL**: Version 14 or higher
  - Download from [postgresql.org](https://www.postgresql.org/)
  - Verify: `psql --version`

### API Keys Required

You'll need the following API keys:

1. **Google Gemini API Key** (or OpenAI/OpenRouter)
   - Sign up at [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Exa API Key**
   - Sign up at [Exa.ai](https://exa.ai/)
3. **Firecrawl API Key**
   - Sign up at [Firecrawl](https://firecrawl.dev/)
4. **Bright Data Credentials** (for browser automation)
   - Sign up at [Bright Data](https://brightdata.com/)
5. **Cloudflare R2** (for storage)
   - Sign up at [Cloudflare](https://www.cloudflare.com/products/r2/)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team
```

### Step 2: Setup PostgreSQL Database

Create a new database for the application:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE tripcraft;

# Create user (optional)
CREATE USER tripcraft_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tripcraft TO tripcraft_user;

# Exit psql
\q
```

### Step 3: Install Frontend Dependencies

```bash
cd client
pnpm install
```

Expected output: All dependencies should install without errors. You should see packages like `next`, `react`, `@prisma/client`, etc.

### Step 4: Install Backend Dependencies

```bash
cd ../backend

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Configuration

### Frontend Configuration

1. Create `.env.local` in the `client` directory:

```bash
cd client
cp .env.example .env.local
```

2. Edit `.env.local` with your configuration:

```env
# Application Base URL
NEXT_PUBLIC_BASE_URL=http://localhost:3000

# Database connection URL (PostgreSQL)
DATABASE_URL=postgresql://tripcraft_user:your_secure_password@localhost:5432/tripcraft

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Configuration

1. Create `.env` in the `backend` directory:

```bash
cd backend
cp .env.example .env
```

2. Edit `.env` with your API keys:

```env
# Database
DATABASE_URL=postgresql://tripcraft_user:your_secure_password@localhost:5432/tripcraft

# AI APIs
EXA_API_KEY=your_exa_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
OPENAI_API_KEY=your_openai_api_key
# OR
OPENROUTER_API_KEY=your_openrouter_api_key

# Browser Automation
BRIGHT_DATA_API_TOKEN=your_bright_data_token
BRIGHT_DATA_BROWSER_AUTH=your_bright_data_auth

# Storage
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_R2_ACCESS_KEY_ID=your_r2_access_key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_r2_secret_key
```

## Database Setup

### Generate Prisma Client and Run Migrations

```bash
cd client

# Generate Prisma client
pnpm prisma generate

# Run database migrations
pnpm prisma migrate dev

# (Optional) Seed the database if seed script exists
pnpm prisma db seed
```

Expected output:
- Prisma client should be generated in `lib/generated/prisma`
- Database tables should be created successfully
- You should see confirmation messages for each migration

### Verify Database Setup

```bash
# Open Prisma Studio to view database
pnpm prisma studio
```

This will open a browser window at `http://localhost:5555` where you can view and manage your database.

## Running the Application

### Start Backend Server

```bash
cd backend
python main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The backend API will be available at `http://localhost:8000`

### Start Frontend Server

Open a new terminal:

```bash
cd client
pnpm dev
```

Expected output:
```
▲ Next.js 15.3.3 (Turbopack)
- Local:        http://localhost:3000
- Network:      http://10.x.x.x:3000
- Environments: .env.local

✓ Starting...
✓ Ready in 1247ms
```

The frontend will be available at `http://localhost:3000`

## Testing

### Manual Testing Checklist

1. **Homepage Access**
   - Navigate to `http://localhost:3000`
   - Verify the homepage loads without errors
   - Check that all UI components render correctly

2. **Authentication Flow**
   - Click on "Sign Up" or navigate to `/auth`
   - Create a new account with email and password
   - Verify you receive proper feedback
   - Sign out and sign back in
   - Verify session persistence

3. **Travel Planning Form**
   - Navigate to `/plan` (should redirect to `/auth` if not logged in)
   - After login, verify the planning form loads
   - Fill out the form with:
     - Destination
     - Travel dates
     - Budget
     - Travel style
     - Number of travelers
     - Preferences
   - Submit the form
   - Verify you receive feedback on submission

4. **View Plans**
   - Navigate to `/plans`
   - Verify you can see your submitted travel plans
   - Check plan status (pending, processing, completed, failed)
   - Click on a plan to view details

5. **Error Handling**
   - Try submitting incomplete forms
   - Verify proper error messages display
   - Test with invalid input (negative budget, past dates, etc.)

### Automated Testing

#### Lint Frontend Code

```bash
cd client
pnpm lint
```

Expected output: `✔ No ESLint warnings or errors`

#### Build Frontend

```bash
cd client
pnpm build
```

Note: Build may fail in environments without internet access due to Google Fonts. This is expected in sandboxed environments and won't affect local development.

#### Type Check

```bash
cd client
pnpm tsc --noEmit
```

### API Testing

Test backend endpoints using curl or a tool like Postman:

```bash
# Health check
curl http://localhost:8000/health

# Get plans (requires authentication)
curl http://localhost:8000/api/plans \
  -H "Cookie: session=your_session_token"
```

## Troubleshooting

### Common Issues

#### 1. TypeError: Failed to parse URL from undefined/api/auth/get-session

**Symptoms**: Error shown when accessing protected routes

**Cause**: Missing `NEXT_PUBLIC_BASE_URL` environment variable

**Solution**:
```bash
# Add to .env.local
NEXT_PUBLIC_BASE_URL=http://localhost:3000
# Restart the dev server
```

#### 2. Database Connection Errors

**Symptoms**: 
- `Error: P1001: Can't reach database server`
- `ECONNREFUSED`

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   # On macOS with Homebrew
   brew services list
   
   # On Linux
   systemctl status postgresql
   ```

2. Check DATABASE_URL format:
   ```
   postgresql://username:password@host:port/database
   ```

3. Test connection:
   ```bash
   psql -U tripcraft_user -d tripcraft -h localhost
   ```

#### 3. Prisma Client Not Found

**Symptoms**: `Error: Cannot find module '@/lib/generated/prisma'`

**Solution**:
```bash
cd client
pnpm prisma generate
```

#### 4. ESLint Errors in Generated Files

**Symptoms**: Many ESLint errors in `lib/generated/prisma/` files

**Solution**: Already fixed! Generated files are now ignored by ESLint.

#### 5. Port Already in Use

**Symptoms**: 
- `Error: listen EADDRINUSE: address already in use :::3000`
- `Error: listen EADDRINUSE: address already in use :::8000`

**Solution**:
```bash
# Find process using port 3000
lsof -i :3000
# Kill the process
kill -9 <PID>

# Or use a different port
PORT=3001 pnpm dev
```

#### 6. Missing API Keys

**Symptoms**: Backend errors when trying to use AI features

**Solution**: Ensure all required API keys are set in `backend/.env`

#### 7. CORS Errors

**Symptoms**: Frontend can't communicate with backend

**Solution**: Verify `NEXT_PUBLIC_API_URL` matches backend URL and CORS is properly configured in FastAPI

### Getting Help

If you encounter issues not covered here:

1. Check the [Issues](https://github.com/Shubhamsaboo/awesome-llm-apps/issues) page
2. Review backend logs for error messages
3. Check browser console for frontend errors
4. Ensure all environment variables are correctly set

## Development Tips

1. **Use Turbopack**: The dev script uses `--turbopack` for faster builds
2. **Prisma Studio**: Use `pnpm prisma studio` to view and edit database data
3. **Hot Reload**: Both frontend and backend support hot reloading during development
4. **Logging**: Check terminal output for both servers to see request logs
5. **Environment Variables**: Changes to `.env.local` require restarting the dev server

## Production Deployment

For production deployment:

1. Set production environment variables
2. Build frontend: `pnpm build`
3. Start frontend: `pnpm start`
4. Deploy backend with proper WSGI server (uvicorn with workers)
5. Setup PostgreSQL with production credentials
6. Configure proper CORS and security headers
7. Use HTTPS for all connections

## Next Steps

After successful setup:

1. Explore the codebase structure
2. Review the AI agent implementations
3. Test different travel planning scenarios
4. Customize the UI to your preferences
5. Add additional features or agents

## Version Information

- Next.js: 15.3.3
- React: 19.0.0
- Node.js: 20.x+
- Python: 3.12+
- PostgreSQL: 14+
- Prisma: 6.8.2
- Better-auth: 1.2.8
