# Hacker Chat Frontend

A Next.js-based chat interface with a hacker-style aesthetic that connects to the FastAPI backend.

## Features

- 🎨 **Hacker-style UI**: Matrix-style animated background with green terminal aesthetic
- 💬 **Real-time Chat**: Send messages to the AI mental coach backend
- 📊 **Progress Bar**: Animated progress indicator during API calls
- 🎯 **Responsive Design**: Works on different screen sizes

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
- Press Enter or click the "SEND" button to send your message
- Watch the progress bar animate while waiting for the AI response
- Messages are displayed in a chat-style interface with user messages in blue and assistant responses in green

## Building for Production

To build the application for production:

```bash
npm run build
npm start
```

## Deployment

This frontend is designed to work with Vercel. See the main README for deployment instructions.