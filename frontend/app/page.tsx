"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState<string>("Connexion au backend...");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    fetch(`${apiUrl}/health`)
      .then((res) => res.json())
      .then((data) => setStatus(`Backend OK ✅ (status: ${data.status})`))
      .catch(() => setStatus("Backend injoignable ❌"));
  }, []);

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Agent IA - Apprentissage du Français 🇫🇷</h1>
      <p>{status}</p>
    </main>
  );
}
