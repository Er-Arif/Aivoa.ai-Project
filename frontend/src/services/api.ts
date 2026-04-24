import type { ChatResponse, Interaction } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8011/api/v1";

async function buildApiError(response: Response, fallbackMessage: string): Promise<Error> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return new Error(payload.detail || fallbackMessage);
  } catch {
    return new Error(fallbackMessage);
  }
}

export async function sendChat(message: string, interactionId: number | null): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, interaction_id: interactionId }),
  });
  if (!response.ok) {
    throw await buildApiError(response, "I couldn't fully understand that. Can you rephrase or provide more details?");
  }
  return response.json();
}

export async function createInteraction(): Promise<Interaction> {
  const response = await fetch(`${API_BASE}/interaction`, { method: "POST" });
  if (!response.ok) {
    throw await buildApiError(response, "Unable to create interaction");
  }
  return response.json();
}
