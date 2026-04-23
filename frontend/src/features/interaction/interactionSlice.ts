import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { Interaction, InteractionHistoryItem } from "../../types";

interface InteractionState {
  current: Interaction | null;
  history: InteractionHistoryItem[];
  lastChangedFields: string[];
}

const initialState: InteractionState = {
  current: null,
  history: [],
  lastChangedFields: [],
};

const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {
    setInteraction(state, action: PayloadAction<Interaction>) {
      state.current = action.payload;
    },
    setHistory(state, action: PayloadAction<InteractionHistoryItem[]>) {
      state.history = action.payload;
    },
    setLastChangedFields(state, action: PayloadAction<string[]>) {
      state.lastChangedFields = action.payload;
    },
    clearLastChangedFields(state) {
      state.lastChangedFields = [];
    },
  },
});

export const { setInteraction, setHistory, setLastChangedFields, clearLastChangedFields } = interactionSlice.actions;
export default interactionSlice.reducer;
