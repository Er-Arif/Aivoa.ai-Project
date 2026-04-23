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
    <main className="h-screen overflow-hidden bg-crm-bg px-2 py-2 text-crm-ink sm:px-4 sm:py-4">
      <div className="mx-auto flex h-full max-w-[1500px] min-h-0 flex-col">
        <h1 className="mb-4 shrink-0 text-[22px] font-extrabold tracking-[0.12em] text-[#17213a]">Log HCP Interaction</h1>
        <div className="grid min-h-0 flex-1 grid-cols-1 overflow-hidden rounded-xl border border-crm-line bg-white shadow-sm lg:grid-cols-[1fr_0.48fr] lg:divide-x lg:divide-crm-line">
          <InteractionForm />
          <ChatPanel />
        </div>
      </div>
    </main>
  );
}
