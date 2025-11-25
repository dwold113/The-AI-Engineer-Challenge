/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.openai.com',
      },
    ],
  },
  // Proxy API calls to Python backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '/api/:path*', // This will be handled by vercel.json routing
      },
    ]
  },
}

module.exports = nextConfig

