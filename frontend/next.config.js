/** @type {import('next').NextConfig} */
const nextConfig = {
  // Build "standalone" : ne copie que les fichiers strictement nécessaires
  // à l'exécution (server.js + node_modules minimal) dans l'image Docker
  // finale, au lieu de tout le node_modules de dev.
  output: "standalone",
  reactStrictMode: true,
};

module.exports = nextConfig;
