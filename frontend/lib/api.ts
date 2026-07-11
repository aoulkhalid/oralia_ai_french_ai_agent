// Petite couche d'accès à l'API backend (FastAPI).
// Le token JWT est stocké dans localStorage : ceci est une vraie
// application web Next.js (pas un artifact Claude), localStorage est donc
// approprié ici.

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "francais_ia_token";

export function saveToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

async function authHeaders(): Promise<HeadersInit> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleErrors(res: Response) {
  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // corps non-JSON, on garde le message par défaut
    }
    throw new Error(detail);
  }
  return res;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function register(payload: {
  email: string;
  password: string;
  nom?: string;
  niveau_cecrl?: string;
}) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await handleErrors(res);
  return res.json();
}

export async function login(email: string, password: string) {
  // /auth/login attend un formulaire OAuth2PasswordRequestForm
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  await handleErrors(res);
  const data = await res.json();
  saveToken(data.access_token);
  return data;
}

export async function getMe() {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: await authHeaders(),
  });
  await handleErrors(res);
  return res.json();
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export interface Correction {
  erreur: string;
  correction: string;
  explication?: string | null;
  categorie?: string | null;
}

export interface ChatResponse {
  conversation_id: number;
  reply: string;
  corrections: Correction[];
}

export async function sendMessage(
  message: string,
  conversationId: number | null,
  scenarioId: number | null = null
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeaders()),
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      scenario_id: scenarioId,
    }),
  });
  await handleErrors(res);
  return res.json();
}

// ---------------------------------------------------------------------------
// Speech (Phase 4)
// ---------------------------------------------------------------------------

export async function speechToText(audioBlob: Blob): Promise<string> {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");

  const res = await fetch(`${API_URL}/speech/speech-to-text`, {
    method: "POST",
    headers: await authHeaders(), // ne PAS fixer Content-Type: le navigateur gère le multipart
    body: formData,
  });
  await handleErrors(res);
  const data = await res.json();
  return data.text as string;
}

export async function textToSpeech(text: string): Promise<Blob> {
  const res = await fetch(`${API_URL}/speech/text-to-speech`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeaders()),
    },
    body: JSON.stringify({ text }),
  });
  await handleErrors(res);
  return res.blob();
}

// ---------------------------------------------------------------------------
// Progression (Phase 6)
// ---------------------------------------------------------------------------

export interface NiveauHistoriquePoint {
  niveau: string;
  date: string | null;
}

export interface ErreursParSemainePoint {
  semaine: string;
  count: number;
}

export interface ErreurFrequente {
  categorie: string;
  count: number;
}

export interface Badge {
  id: string;
  label: string;
  description: string;
}

export interface ProgressDashboard {
  user_id: number;
  niveau_estime: string | null;
  conversations_completees: number;
  erreurs_frequentes: ErreurFrequente[];
  niveau_historique: NiveauHistoriquePoint[];
  erreurs_par_semaine: ErreursParSemainePoint[];
  points: number;
  streak_jours: number;
  badges: Badge[];
}

export async function getProgressDashboard(
  userId: number
): Promise<ProgressDashboard> {
  const res = await fetch(`${API_URL}/progress/${userId}/dashboard`, {
    headers: await authHeaders(),
  });
  await handleErrors(res);
  return res.json();
}

// ---------------------------------------------------------------------------
// Scénarios de conversation (Phase 7)
// ---------------------------------------------------------------------------

export interface Scenario {
  id: number;
  titre: string;
  description: string | null;
  niveau_cecrl: string | null;
  categorie: string | null;
}

export async function listScenarios(): Promise<Scenario[]> {
  const res = await fetch(`${API_URL}/scenarios`, {
    headers: await authHeaders(),
  });
  await handleErrors(res);
  return res.json();
}

// ---------------------------------------------------------------------------
// Exercices personnalisés (Phase 7)
// ---------------------------------------------------------------------------

export interface Exercise {
  id: number;
  niveau_cecrl: string;
  categorie: string | null;
  question: string;
  reponse_utilisateur: string | null;
  is_correct: boolean | null;
  created_at: string | null;
}

export interface ExerciseResult {
  id: number;
  is_correct: boolean;
  reponse_attendue: string;
  feedback: string;
}

export async function generateExercise(): Promise<Exercise> {
  const res = await fetch(`${API_URL}/exercises/generate`, {
    method: "POST",
    headers: await authHeaders(),
  });
  await handleErrors(res);
  return res.json();
}

export async function listMyExercises(): Promise<Exercise[]> {
  const res = await fetch(`${API_URL}/exercises`, {
    headers: await authHeaders(),
  });
  await handleErrors(res);
  return res.json();
}

export async function submitExercise(
  exerciseId: number,
  reponse: string
): Promise<ExerciseResult> {
  const res = await fetch(`${API_URL}/exercises/${exerciseId}/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeaders()),
    },
    body: JSON.stringify({ reponse }),
  });
  await handleErrors(res);
  return res.json();
}
