/** @type {import('next').NextConfig} */
const nextConfig = {
  // self contained server for the docker image (see Dockerfile)
  output: "standalone",
  poweredByHeader: false,
}

export default nextConfig
