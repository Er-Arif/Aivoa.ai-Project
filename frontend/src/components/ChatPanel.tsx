import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bot, Send, TriangleAlert } from "lucide-react";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { addUserMessage, setThinkingPhase, submitChat } from "../features/chat/chatSlice";

const thinkingLabels = {
  idle: "",
  analyzing: "Analyzing...",
  extracting: "Extracting data...",
  updating: "Updating interaction...",
};

export function ChatPanel() {
  const dispatch = useAppDispatch();
  const { messages, loading, error, thinkingPhase, lastSubmitAt } = useAppSelector((state) => state.chat);
  const [text, setText] = useState("");

  useEffect(() => {
    if (!loading) return;
    const extractTimer = window.setTimeout(() => dispatch(setThinkingPhase("extracting")), 450);
    const updateTimer = window.setTimeout(() => dispatch(setThinkingPhase("updating")), 1050);
    return () => {
      window.clearTimeout(extractTimer);
      window.clearTimeout(updateTimer);
    };
  }, [dispatch, loading]);

  const canSubmit = useMemo(() => {
    return text.trim().length > 0 && !loading && Date.now() - lastSubmitAt > 600;
  }, [text, loading, lastSubmitAt]);

  const shouldShowExplanation = (toolExplanation?: string, content?: string) => {
    if (!toolExplanation || !content) return false;
    return toolExplanation.trim() !== content.trim();
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const message = text.trim();
    if (!canSubmit || !message) return;
    dispatch(addUserMessage(message));
    dispatch(submitChat(message));
    setText("");
  };

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden border-t border-crm-line bg-white lg:border-t-0">
      <div className="shrink-0 border-b border-crm-line px-5 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <Bot className="text-crm-blue" size={24} />
          <div>
            <h2 className="text-[16px] font-extrabold tracking-wide text-[#1d2940]">AI Assistant</h2>
            <p className="text-sm font-semibold text-slate-500">Log interaction via chat</p>
          </div>
        </div>
      </div>

      <div className="crm-scroll min-h-0 flex-1 space-y-4 overflow-y-auto bg-[#fbfcfe] px-5 py-4 sm:px-6">
        <div className="w-[88%] rounded-md border border-crm-line bg-white p-4 text-[15px] font-semibold leading-6 text-slate-700 shadow-sm">
          Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.
        </div>

        {messages.map((message) => (
          <article key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[88%] rounded-md border px-4 py-3 text-sm shadow-sm ${message.role === "user" ? "border-blue-100 bg-blue-600 text-white" : "border-crm-line bg-white text-slate-700"}`}>
              {message.tool_name ? (
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-700">{message.tool_name}</span>
                  {typeof message.confidence === "number" ? <span className="text-xs font-semibold text-slate-500">Confidence {(message.confidence * 100).toFixed(0)}%</span> : null}
                  {message.status === "completed" ? <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-bold text-emerald-700">Completed</span> : null}
                </div>
              ) : null}
              {shouldShowExplanation(message.tool_explanation, message.content) ? <p className="mb-1 text-xs font-semibold text-blue-700">{message.tool_explanation}</p> : null}
              <p className="whitespace-pre-wrap leading-5">{message.content}</p>
            </div>
          </article>
        ))}

        {loading ? (
          <div className="rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800">
            {thinkingLabels[thinkingPhase]}
          </div>
        ) : null}

        {error && !loading ? (
          <div className="flex items-center gap-2 rounded-md border border-red-100 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
            <TriangleAlert size={16} />
            {error}
          </div>
        ) : null}
      </div>

      <form className="shrink-0 flex gap-3 border-t border-crm-line bg-white px-5 py-4 sm:px-6" onSubmit={handleSubmit}>
        <input
          className="h-10 flex-1 rounded-md border border-crm-line px-4 text-sm font-semibold outline-none transition focus:border-crm-blue focus:ring-2 focus:ring-blue-100 disabled:bg-slate-50"
          disabled={loading}
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Describe interaction..."
        />
        <button
          className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-700 px-5 text-sm font-extrabold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={!canSubmit}
          type="submit"
        >
          <Send size={16} />
          Log
        </button>
      </form>
    </section>
  );
}
