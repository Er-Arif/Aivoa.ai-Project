import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { sendChat } from "../../services/api";
import type { RootState } from "../../app/store";
import type { ChatMessage, ChatResponse } from "../../types";
import { setHistory, setInteraction, setLastChangedFields } from "../interaction/interactionSlice";

type ThinkingPhase = "idle" | "analyzing" | "extracting" | "updating";

interface ChatState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  thinkingPhase: ThinkingPhase;
  activeInteractionId: number | null;
  lastSubmitAt: number;
}

const initialState: ChatState = {
  messages: [],
  loading: false,
  error: null,
  thinkingPhase: "idle",
  activeInteractionId: null,
  lastSubmitAt: 0,
};

export const submitChat = createAsyncThunk<
  ChatResponse,
  string,
  { state: RootState; rejectValue: string }
>("chat/submit", async (message, { getState, dispatch, rejectWithValue }) => {
  const state = getState();
  try {
    const result = await sendChat(message, state.chat.activeInteractionId);
    dispatch(setInteraction(result.interaction));
    dispatch(setLastChangedFields(result.changed_fields));
    dispatch(setHistory(result.history ?? []));
    return result;
  } catch (error) {
    return rejectWithValue(error instanceof Error ? error.message : "I couldn't fully understand that. Can you rephrase or provide more details?");
  }
});

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addUserMessage(state, action: PayloadAction<string>) {
      state.messages.push({
        id: `local-${Date.now()}`,
        role: "user",
        content: action.payload,
        created_at: new Date().toISOString(),
      });
      state.lastSubmitAt = Date.now();
    },
    setThinkingPhase(state, action: PayloadAction<ThinkingPhase>) {
      state.thinkingPhase = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitChat.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.thinkingPhase = "analyzing";
      })
      .addCase(submitChat.fulfilled, (state, action) => {
        state.loading = false;
        state.thinkingPhase = "idle";
        state.activeInteractionId = action.payload.interaction.id;
        state.messages.push({
          ...action.payload.assistant_message,
          tool_name: action.payload.tool_name,
          tool_explanation: action.payload.tool_explanation,
          confidence: action.payload.confidence,
        });
      })
      .addCase(submitChat.rejected, (state, action) => {
        state.loading = false;
        state.thinkingPhase = "idle";
        state.error = action.payload ?? "I couldn't fully understand that. Can you rephrase or provide more details?";
        state.messages.push({
          id: `error-${Date.now()}`,
          role: "assistant",
          content: state.error,
          tool_name: "Fallback",
          confidence: 0,
          created_at: new Date().toISOString(),
        });
      });
  },
});

export const { addUserMessage, setThinkingPhase } = chatSlice.actions;
export default chatSlice.reducer;
