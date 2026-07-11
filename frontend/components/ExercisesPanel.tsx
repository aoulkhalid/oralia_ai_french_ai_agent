"use client";

import { useState } from "react";
import {
  generateExercise,
  submitExercise,
  Exercise,
  ExerciseResult,
} from "../lib/api";

export default function ExercisesPanel() {
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [reponse, setReponse] = useState("");
  const [result, setResult] = useState<ExerciseResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setResult(null);
    setReponse("");
    try {
      const ex = await generateExercise();
      setExercise(ex);
    } catch (err: any) {
      setError(err.message || "Impossible de générer un exercice.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!exercise || !reponse.trim()) return;
    setError(null);
    try {
      const res = await submitExercise(exercise.id, reponse.trim());
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Erreur lors de la correction.");
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", fontFamily: "sans-serif" }}>
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: "1.5rem",
        }}
      >
        {!exercise && (
          <>
            <p style={{ color: "#666" }}>
              Génère un exercice personnalisé, ciblé sur tes erreurs les plus
              fréquentes.
            </p>
            <button onClick={handleGenerate} disabled={loading}>
              {loading ? "Génération en cours..." : "🎯 Générer un exercice"}
            </button>
          </>
        )}

        {exercise && (
          <>
            {exercise.categorie && (
              <p style={{ fontSize: "0.85rem", color: "#888", margin: 0 }}>
                Catégorie ciblée : {exercise.categorie}
              </p>
            )}
            <p style={{ fontSize: "1.1rem", fontWeight: 500 }}>{exercise.question}</p>

            {!result ? (
              <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  type="text"
                  value={reponse}
                  onChange={(e) => setReponse(e.target.value)}
                  placeholder="Votre réponse..."
                  style={{ flex: 1, padding: "0.5rem" }}
                  autoFocus
                />
                <button type="submit" disabled={!reponse.trim()}>
                  Valider
                </button>
              </form>
            ) : (
              <div
                style={{
                  padding: "0.75rem",
                  borderRadius: 6,
                  background: result.is_correct ? "#DCF8C6" : "#FFE0E0",
                  marginTop: "0.5rem",
                }}
              >
                <strong>{result.is_correct ? "✅ Correct !" : "❌ Pas tout à fait"}</strong>
                <p style={{ margin: "0.4rem 0 0" }}>{result.feedback}</p>
              </div>
            )}

            {result && (
              <button onClick={handleGenerate} style={{ marginTop: "1rem" }}>
                Exercice suivant →
              </button>
            )}
          </>
        )}

        {error && <p style={{ color: "crimson" }}>{error}</p>}
      </div>
    </div>
  );
}
