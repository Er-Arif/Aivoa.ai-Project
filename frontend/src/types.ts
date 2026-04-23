export type Sentiment = "positive" | "neutral" | "negative" | "unknown";
export type InteractionStatus = "draft" | "completed";

export interface Interaction {
  id: number;
  hcp_name: string | null;
  interaction_type: string | null;
  interaction_date: string | null;
  interaction_time: string | null;
  attendees: string[];
  topics_discussed: string[];
  materials_shared: string[];
  samples_distributed: string[];
  sentiment: Sentiment;
  outcomes: string | null;
  follow_up_actions: string[];
  ai_suggested_followups: string[];
  status: InteractionStatus;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number | string;
  interaction_id?: number;
  role: "user" | "assistant";
  content: string;
  tool_name?: string | null;
  tool_explanation?: string;
  confidence?: number | null;
  status?: InteractionStatus;
  created_at: string;
}

export interface InteractionHistoryItem {
  id: number;
  hcp_name: string | null;
  interaction_type: string | null;
  interaction_date: string | null;
  sentiment: Sentiment;
  topics_discussed: string[];
  outcomes: string | null;
  follow_up_actions: string[];
}

export interface ChatResponse {
  interaction: Interaction;
  assistant_message: ChatMessage;
  tool_name: string;
  tool_explanation: string;
  confidence: number;
  changed_fields: string[];
  tool_output: Record<string, unknown>;
  history: InteractionHistoryItem[] | null;
}
