"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { getProgressDashboard, ProgressDashboard as ProgressDashboardData } from "../lib/api";

const CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];

const CATEGORY_LABELS: Record<string, string> = {
  grammaire: "Grammaire",
  conjugaison: "Conjugaison",
  orthographe: "Orthographe",
  accord: "Accords",
  vocabulaire: "Vocabulaire",
};

export default function ProgressDashboard({ userId }: { userId: number }) {
  const [data, setData] = useState<ProgressDashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProgressDashboard(userId)
      .then(setData)
      .catch((err) => setError(err.message || "Impossible de charger la progression."))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return <p>Chargement de votre progression...</p>;
  }

  if (error) {
    return <p style={{ color: "crimson" }}>{error}</p>;
  }

  if (!data) return null;

  const niveauIndex = CEFR_LEVELS.indexOf(data.niveau_estime || "A1");
  const progressionPct =
    niveauIndex >= 0 ? Math.round(((niveauIndex + 1) / CEFR_LEVELS.length) * 100) : 0;

  const erreursChartData = data.erreurs_frequentes.map((e) => ({
    categorie: CATEGORY_LABELS[e.categorie] || e.categorie,
    count: e.count,
  }));

  const semaineChartData = data.erreurs_par_semaine.map((e) => ({
    semaine: e.semaine.replace(/^\d{4}-/, ""), // "2026-W27" -> "W27"
    erreurs: e.count,
  }));

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", fontFamily: "sans-serif" }}>
      {/* --- Carte niveau CECRL --- */}
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: "1.25rem",
          marginBottom: "1.5rem",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Niveau CECRL actuel</h2>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div
            style={{
              fontSize: "2rem",
              fontWeight: "bold",
              background: "#DCF8C6",
              borderRadius: 8,
              padding: "0.5rem 1rem",
            }}
          >
            {data.niveau_estime || "A1"}
          </div>
          <div style={{ flex: 1 }}>
            <div
              style={{
                height: 10,
                borderRadius: 5,
                background: "#eee",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${progressionPct}%`,
                  background: "#4CAF50",
                  transition: "width 0.4s ease",
                }}
              />
            </div>
            <small style={{ color: "#888" }}>
              A1 → C2 · {data.conversations_completees} conversation
              {data.conversations_completees > 1 ? "s" : ""} complétée
              {data.conversations_completees > 1 ? "s" : ""}
            </small>
          </div>
        </div>

        {data.niveau_historique.length > 1 && (
          <p style={{ marginTop: "0.75rem", color: "#555" }}>
            Progression :{" "}
            {data.niveau_historique.map((h, i) => (
              <span key={i}>
                {h.niveau}
                {i < data.niveau_historique.length - 1 && " → "}
              </span>
            ))}
          </p>
        )}
      </section>

      {/* --- Gamification : points, streak, badges (Phase 7) --- */}
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: "1.25rem",
          marginBottom: "1.5rem",
          display: "flex",
          gap: "2rem",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <div>
          <div style={{ fontSize: "1.5rem", fontWeight: "bold" }}>⭐ {data.points}</div>
          <small style={{ color: "#888" }}>points</small>
        </div>
        <div>
          <div style={{ fontSize: "1.5rem", fontWeight: "bold" }}>
            🔥 {data.streak_jours}
          </div>
          <small style={{ color: "#888" }}>
            jour{data.streak_jours > 1 ? "s" : ""} de suite
          </small>
        </div>
        {data.badges.length > 0 && (
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {data.badges.map((b) => (
              <span
                key={b.id}
                title={b.description}
                style={{
                  background: "#f0f0ff",
                  border: "1px solid #d0d0ff",
                  borderRadius: 20,
                  padding: "0.3rem 0.75rem",
                  fontSize: "0.85rem",
                }}
              >
                {b.label}
              </span>
            ))}
          </div>
        )}
      </section>

      {/* --- Graphique : erreurs fréquentes par catégorie --- */}
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: "1.25rem",
          marginBottom: "1.5rem",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Erreurs les plus fréquentes</h2>
        {erreursChartData.length === 0 ? (
          <p style={{ color: "#888" }}>
            Pas encore assez de données. Continuez à discuter pour voir vos
            tendances d'erreurs apparaître ici.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={erreursChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="categorie" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="Occurrences" fill="#e63946" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>

      {/* --- Graphique : tendance des erreurs dans le temps --- */}
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: "1.25rem",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Tendance des erreurs par semaine</h2>
        {semaineChartData.length < 2 ? (
          <p style={{ color: "#888" }}>
            Pas encore assez de semaines de données pour tracer une tendance.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={semaineChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semaine" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="erreurs"
                name="Erreurs détectées"
                stroke="#4C6EF5"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
        <p style={{ color: "#888", fontSize: "0.85rem", marginBottom: 0 }}>
          Une courbe qui descend dans le temps est bon signe : ça veut dire
          moins d'erreurs par semaine 📉
        </p>
      </section>
    </div>
  );
}
