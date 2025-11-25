# Pixelated Background Generator Frontend

A Next.js frontend application that generates pixelated backgrounds from AI-generated images using DALL-E.

## Features

- **AI Image Generation**: Enter a prompt and generate images using OpenAI's DALL-E API
- **Pixelated Background**: Automatically converts generated images into a cool pixelated background made of tiny squares
- **Modern UI**: Beautiful, responsive interface with smooth animations
- **Real-time Updates**: Watch as your background pixelates in real-time

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
3. Enter a prompt describing the image you want (e.g., "a sunset over mountains", "abstract geometric patterns")
4. Click "Generate Pixelated Background" or press Enter
5. Watch as the image is generated and converted into a pixelated background of tiny squares

## Project Structure

```
frontend/
├── app/
│   ├── components/
│   │   └── PixelatedBackground.tsx  # Component that creates pixelated effect
│   ├── globals.css                   # Global styles
│   ├── layout.tsx                     # Root layout
│   └── page.tsx                      # Main page with prompt input
├── package.json
├── tsconfig.json
├── next.config.js
└── tailwind.config.js
```

## Technologies

- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **OpenAI DALL-E**: AI image generation

## Troubleshooting

### Images not loading

- Ensure the backend API is running and accessible
- Check that `OPENAI_API_KEY` is set in the backend environment
- Verify CORS is properly configured in the backend

### Pixelation not working

- Check browser console for errors
- Ensure images are loading successfully
- Try refreshing the page

## Deployment

This frontend is designed to work with Vercel. See the main README for deployment instructions.
