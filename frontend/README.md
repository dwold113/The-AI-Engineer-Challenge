# Learning Experience Frontend

A Next.js frontend application that helps users learn about any topic by generating personalized learning plans with real examples scraped from the web.

## Features

- **AI Learning Plans**: Enter a topic and get a structured, step-by-step learning plan
- **Real Examples**: Automatically finds and displays real-world resources, tutorials, and examples
- **Expandable Steps**: Dive deeper into any learning step for additional context and details
- **Modern UI**: Beautiful, responsive interface with smooth animations
- **Smart Validation**: AI-powered validation to ensure topics are meaningful and learnable

## Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000` (see main README for backend setup)
- OpenAI API key configured in the backend

## Setup

1. Install dependencies:

```bash
npm install
```

2. Set the API URL (optional, defaults to `http://localhost:8000`):

Create a `.env.local` file in the `frontend` directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Development Mode

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Production Build

Build the application:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

## Usage

1. Make sure the backend API is running (see `api/README.md`)
2. Start the frontend development server
3. Enter a topic you want to learn about (e.g., "Python programming", "Machine Learning", "Cooking Italian food")
4. Optionally specify number of steps and resources (e.g., "give me 3 steps and 10 examples")
5. Click "Start Learning" or press Enter
6. Review your personalized learning plan
7. Click "Dive Deeper" on any step for additional context
8. Explore the real examples and resources provided

## Project Structure

```
frontend/
├── app/
│   ├── globals.css                   # Global styles
│   ├── layout.tsx                     # Root layout
│   └── page.tsx                      # Main page with learning interface
├── package.json
├── tsconfig.json
├── next.config.js
└── README.md
```

## Technologies

- **Next.js 15**: React framework with App Router
- **React 18**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **OpenAI GPT-4o-mini**: Learning plan generation and validation
