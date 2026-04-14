/** @type {import('next').NextConfig} */
const backendBaseUrl = process.env.INTERNAL_BACKEND_URL ?? "http://backend:8000";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendBaseUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
