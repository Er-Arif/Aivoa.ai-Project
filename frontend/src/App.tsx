import { useEffect } from "react";

import { ChatPanel } from "./components/ChatPanel";
import { InteractionForm } from "./components/InteractionForm";
import { useAppDispatch, useAppSelector } from "./app/hooks";
import { clearLastChangedFields } from "./features/interaction/interactionSlice";

export default function App() {
  const dispatch = useAppDispatch();
  const changed = useAppSelector((state) => state.interaction.lastChangedFields);

  useEffect(() => {
    if (!changed.length) return;
    const timer = window.setTimeout(() => dispatch(clearLastChangedFields()), 1400);
    return () => window.clearTimeout(timer);
  }, [changed, dispatch]);

  return (
    <main className="min-h-screen bg-crm-bg px-2 py-2 text-crm-ink sm:px-4">
      <div className="mx-auto max-w-[1500px]">
        <h1 className="mb-5 text-[22px] font-extrabold tracking-[0.12em] text-[#17213a]">Log HCP Interaction</h1>
        <div className="grid min-h-[calc(100vh-76px)] grid-cols-1 gap-8 lg:grid-cols-[1fr_0.48fr]">
          <InteractionForm />
          <ChatPanel />
        </div>
      </div>
    </main>
  );
}
