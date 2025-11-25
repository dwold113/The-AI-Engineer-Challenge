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
- Use `frontend/package.json` for dependencies
- Serve the Next.js app as the main site

### Step 2: Verify vercel.json

The `vercel.json` file should:
- Build the Python backend from `api/backend.py`
- Route `/api/*` requests to the Python backend
- Route all other requests to the Next.js frontend

### Step 3: Environment Variables

Set in Vercel → Settings → Environment Variables:
- `OPENAI_API_KEY` - Your OpenAI API key (for backend)

### Step 4: Deploy

After setting the root directory, push your code:
```bash
git push
```

Vercel will automatically:
1. Build Next.js from `frontend/` directory
2. Build Python backend from `api/backend.py`
3. Deploy both together

## How It Works

- **Frontend routes** (`/`, `/about`, etc.) → Next.js app
- **API routes** (`/api/*`) → FastAPI Python backend
- Both are deployed in the same Vercel project

