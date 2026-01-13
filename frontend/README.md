# STELLAR_AI Frontend

A Next.js-based chat interface with a space-themed aesthetic that connects to the FastAPI backend. Features a beautiful starry night sky background with floating space objects including asteroids, planets, and nebula clouds.

## Features

- 🌌 **Space-themed UI**: Realistic night sky background with twinkling stars and floating space objects
- 🪐 **Floating Space Objects**: Continuously animated asteroids, planets, nebula clouds, and space debris
- 💬 **Real-time Chat**: Send messages to the STELLAR_AI personal assistant backend
- 📊 **Progress Bar**: Animated quantum processing indicator during API calls
- 🎯 **Responsive Design**: Works on different screen sizes
- 🚀 **Space Aesthetics**: Cyan and purple color scheme with space-themed messaging

## Prerequisites

- Node.js 18+ and npm (or yarn/pnpm)
- The backend server running on `http://localhost:8000` (see `/api/README.md` for backend setup)

## Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

1. Make sure the backend server is running:
```bash
# From the project root
uv run uvicorn api.index:app --reload
```

2. Start the Next.js development server:
```bash
# From the frontend directory
npm run dev
```

3. Open your browser and navigate to:
```
http://localhost:3000
```

## Usage

- Type your message in the text input box at the bottom
- Press Enter or click the "LAUNCH" button to send your message
- Watch the quantum processing progress bar animate while waiting for the AI response
- Messages are displayed in a chat-style interface with user messages in purple and assistant responses in cyan
- Enjoy the floating space objects (asteroids, planets, nebula clouds) in the background

## Building for Production

To build the application for production:

```bash
npm run build
npm start
```

## Deployment

This frontend is designed to work with Vercel. See the main README for deployment instructions.