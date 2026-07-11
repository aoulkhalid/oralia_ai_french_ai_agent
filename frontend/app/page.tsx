"use client";

import { useEffect, useState } from "react";
import { API_URL } from "../lib/api";

export default function Home() {
  const [status, setStatus] = useState<string>("Connexion au backend...");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => res.json())
      .then((data) => setStatus(`Backend OK ✅ (status: ${data.status})`))
      .catch(() => setStatus("Backend injoignable ❌"));
  }, []);

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Agent IA - Apprentissage du Français 🇫🇷</h1>
      <p>{status}</p>
      <p>
        <a href="/login">Se connecter</a> · <a href="/register">Créer un compte</a> ·{" "}
        <a href="/chat">Aller à la conversation</a>
      </p>
    </main>
  );
}
