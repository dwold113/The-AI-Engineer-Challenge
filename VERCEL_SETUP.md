# Vercel Deployment Setup

This project is a monorepo with:
- **Frontend**: Next.js app in `frontend/` directory
- **Backend**: FastAPI Python API in `api/` directory

## Required Vercel Configuration

### Step 1: Set Root Directory in Vercel Dashboard

1. Go to your Vercel project → **Settings** → **General**
2. Find **"Root Directory"** setting
3. Set it to: `frontend`
4. Click **Save**

This tells Vercel to:
- Build Next.js from the `frontend/` directory
- Automatically run `npm install` and `npm run build` (as per frontend README)
- Use `frontend/package.json` for dependencies
- Serve the Next.js app as the main site

### Step 2: Verify vercel.json

The `vercel.json` file at the repo root:
- Builds the Python backend from `api/backend.py`
- Routes `/api/*` requests to the Python backend
- Routes all other requests to the Next.js frontend

**Note**: When Root Directory is set to `frontend`, Vercel automatically:
- Runs `npm install` in the `frontend/` directory
- Runs `npm run build` (as specified in `frontend/package.json`)
- Uses `.next` as the output directory

### Step 3: Environment Variables

Set in Vercel → Settings → Environment Variables:
- `OPENAI_API_KEY` - Your OpenAI API key (for backend)
- `NEXT_PUBLIC_API_URL` (optional) - If your frontend needs to know the API URL

### Step 4: Deploy

After setting the root directory, push your code:
```bash
git push
```

Vercel will automatically:
1. Install dependencies: `npm install` in `frontend/`
2. Build Next.js: `npm run build` in `frontend/` (creates `frontend/.next/`)
3. Build Python backend: Creates serverless function from `api/backend.py`
4. Deploy both together

## How It Works

- **Frontend routes** (`/`, `/about`, etc.) → Next.js app (from `frontend/.next/`)
- **API routes** (`/api/*`) → FastAPI Python backend (from `api/backend.py`)
- Both are deployed in the same Vercel project

## Build Process (from frontend README)

The build process matches what's documented in `frontend/README.md`:
1. `npm install` - Install dependencies
2. `npm run build` - Build Next.js production bundle
3. Output goes to `frontend/.next/` directory

