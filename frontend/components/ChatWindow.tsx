"use client";

import { useRef, useState } from "react";
import { sendMessage, speechToText, textToSpeech, Correction } from "../lib/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  corrections?: Correction[];
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  async function playReply(text: string) {
    try {
      const blob = await textToSpeech(text);
      const url = URL.createObjectURL(blob);
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = url;
        await audioPlayerRef.current.play();
      }
    } catch (err) {
      // La lecture audio est un bonus : une erreur TTS ne doit pas
      // bloquer la conversation textuelle.
      console.error("Erreur text-to-speech:", err);
    }
  }

  async function submitMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;

    setError(null);
    setIsSending(true);
    setInput("");

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await sendMessage(trimmed, conversationId);
      setConversationId(response.conversation_id);

      setMessages((prev) => [
        ...prev,
        {
          ...userMessage,
          corrections: response.corrections,
        },
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.reply,
        },
      ]);

      if (autoSpeak) {
        await playReply(response.reply);
      }
    } catch (err: any) {
      setError(err.message || "Erreur lors de l'envoi du message.");
    } finally {
      setIsSending(false);
    }
  }

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });

        setIsTranscribing(true);
        try {
          const text = await speechToText(audioBlob);
          if (text) {
            await submitMessage(text);
          }
        } catch (err: any) {
          setError(err.message || "Erreur lors de la transcription audio.");
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setError("Impossible d'accéder au microphone.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", fontFamily: "sans-serif" }}>
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: "1rem",
          minHeight: 400,
          maxHeight: 500,
          overflowY: "auto",
          marginBottom: "1rem",
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: "#888" }}>
            Commencez la conversation en tapant un message ou en utilisant le
            micro 🎤
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} style={{ marginBottom: "1rem" }}>
            <div
              style={{
                display: "inline-block",
                padding: "0.5rem 0.75rem",
                borderRadius: 8,
                background: m.role === "user" ? "#DCF8C6" : "#F1F0F0",
                maxWidth: "80%",
              }}
            >
              <strong>{m.role === "user" ? "Vous" : "Agent"} :</strong> {m.content}
            </div>

            {m.corrections && m.corrections.length > 0 && (
              <div
                style={{
                  marginTop: "0.4rem",
                  fontSize: "0.9rem",
                  background: "#FFF3CD",
                  border: "1px solid #FFE69C",
                  borderRadius: 6,
                  padding: "0.5rem 0.75rem",
                }}
              >
                <strong>Corrections :</strong>
                <ul style={{ margin: "0.25rem 0 0", paddingLeft: "1.2rem" }}>
                  {m.corrections.map((c, i) => (
                    <li key={i}>
                      <s>{c.erreur}</s> → <strong>{c.correction}</strong>
                      {c.explication && <> — {c.explication}</>}
                      {c.categorie && (
                        <em style={{ color: "#888" }}> ({c.categorie})</em>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submitMessage(input);
        }}
        style={{ display: "flex", gap: "0.5rem" }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Écrivez votre message en français..."
          disabled={isSending || isRecording || isTranscribing}
          style={{ flex: 1, padding: "0.6rem" }}
        />
        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isSending || isTranscribing}
          title="Micro"
          style={{
            padding: "0.6rem 0.9rem",
            background: isRecording ? "#e63946" : "#eee",
            color: isRecording ? "white" : "black",
            border: "none",
            borderRadius: 6,
          }}
        >
          {isRecording ? "⏹️ Stop" : "🎤"}
        </button>
        <button
          type="submit"
          disabled={isSending || isRecording || isTranscribing || !input.trim()}
          style={{ padding: "0.6rem 1rem" }}
        >
          Envoyer
        </button>
      </form>

      <label style={{ display: "block", marginTop: "0.75rem", fontSize: "0.9rem" }}>
        <input
          type="checkbox"
          checked={autoSpeak}
          onChange={(e) => setAutoSpeak(e.target.checked)}
        />{" "}
        Lire les réponses à voix haute
      </label>

      {isTranscribing && <p>Transcription en cours...</p>}
      {isSending && <p>L'agent réfléchit...</p>}

      <audio ref={audioPlayerRef} style={{ display: "none" }} />
    </div>
  );
}
