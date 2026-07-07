"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe, clearToken } from "../../lib/api";
import ChatWindow from "../../components/ChatWindow";

export default function ChatPage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then((user) => setUserEmail(user.email))
      .catch(() => router.push("/login"))
      .finally(() => setChecking(false));
  }, [router]);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  if (checking) {
    return <main style={{ padding: "2rem" }}>Chargement...</main>;
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          maxWidth: 700,
          margin: "0 auto 1.5rem",
        }}
      >
        <h1 style={{ margin: 0 }}>Conversation en français 🇫🇷</h1>
        <div>
          <span style={{ marginRight: "1rem", color: "#666" }}>{userEmail}</span>
          <button onClick={handleLogout}>Déconnexion</button>
        </div>
      </div>
      <ChatWindow />
    </main>
  );
}
