"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register, login } from "../../lib/api";

const NIVEAUX = ["A1", "A2", "B1", "B2", "C1", "C2"];

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nom, setNom] = useState("");
  const [niveau, setNiveau] = useState("A1");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register({ email, password, nom, niveau_cecrl: niveau });
      // Connexion automatique après inscription
      await login(email, password);
      router.push("/chat");
    } catch (err: any) {
      setError(err.message || "Échec de l'inscription.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: 400 }}>
      <h1>Créer un compte</h1>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <label>
          Nom
          <input
            type="text"
            value={nom}
            onChange={(e) => setNom(e.target.value)}
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </label>
        <label>
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </label>
        <label>
          Mot de passe (min. 8 caractères)
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </label>
        <label>
          Niveau CECRL de départ
          <select
            value={niveau}
            onChange={(e) => setNiveau(e.target.value)}
            style={{ width: "100%", padding: "0.5rem" }}
          >
            {NIVEAUX.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ padding: "0.6rem" }}>
          {loading ? "Création..." : "Créer mon compte"}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        Déjà un compte ? <a href="/login">Se connecter</a>
      </p>
    </main>
  );
}
