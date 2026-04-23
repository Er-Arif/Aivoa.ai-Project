import { Calendar, Clock, Package, Search, Sparkles } from "lucide-react";
import type { ReactNode } from "react";

import { useAppSelector } from "../app/hooks";
import type { Interaction, Sentiment } from "../types";

const emptyInteraction: Partial<Interaction> = {
  hcp_name: "",
  interaction_type: "Meeting",
  interaction_date: "",
  interaction_time: "",
  attendees: [],
  topics_discussed: [],
  materials_shared: [],
  samples_distributed: [],
  sentiment: "unknown",
  outcomes: "",
  follow_up_actions: [],
  ai_suggested_followups: [],
  status: "draft",
};

function text(value: string | null | undefined, placeholder = "") {
  return value || placeholder;
}

function listText(value: string[] | undefined) {
  return value?.length ? value.join(", ") : "";
}

function FieldShell({ field, children }: { field: string; children: ReactNode }) {
  const changed = useAppSelector((state) => state.interaction.lastChangedFields.includes(field));
  return <div className={changed ? "rounded-md animate-flash" : ""}>{children}</div>;
}

function DisabledInput({ field, label, value, placeholder, icon }: { field: string; label: string; value: string; placeholder: string; icon?: ReactNode }) {
  return (
    <FieldShell field={field}>
      <label className="form-label">{label}</label>
      <div className="relative">
        <input className="form-control pr-10" disabled readOnly value={value} placeholder={placeholder} />
        {icon ? <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">{icon}</span> : null}
      </div>
    </FieldShell>
  );
}

function DisabledTextarea({ field, label, value, placeholder }: { field: string; label: string; value: string; placeholder: string }) {
  return (
    <FieldShell field={field}>
      <label className="form-label">{label}</label>
      <textarea className="form-control min-h-[82px] resize-none" disabled readOnly value={value} placeholder={placeholder} />
    </FieldShell>
  );
}

function SentimentRadio({ sentiment }: { sentiment: Sentiment }) {
  const options: Array<{ value: Sentiment; label: string; icon: string }> = [
    { value: "positive", label: "Positive", icon: "🙂" },
    { value: "neutral", label: "Neutral", icon: "😐" },
    { value: "negative", label: "Negative", icon: "☹" },
  ];
  return (
    <FieldShell field="sentiment">
      <label className="form-label">Observed/Inferred HCP Sentiment</label>
      <div className="flex flex-wrap gap-8">
        {options.map((option) => (
          <label key={option.value} className="flex items-center gap-2 text-[15px] font-semibold text-slate-700">
            <input className="h-5 w-5 accent-crm-blue" disabled readOnly type="radio" checked={sentiment === option.value} />
            <span className="leading-none">{option.icon}</span>
            {option.label}
          </label>
        ))}
      </div>
    </FieldShell>
  );
}

function AssetBox({ field, title, items, buttonLabel, icon }: { field: string; title: string; items: string[]; buttonLabel: string; icon: ReactNode }) {
  return (
    <FieldShell field={field}>
      <div className="rounded-md border border-crm-line bg-white px-4 py-3">
        <div className="mb-2 flex items-center justify-between gap-3">
          <h3 className="text-[15px] font-semibold text-slate-700">{title}</h3>
          <button className="inline-flex h-8 items-center gap-2 rounded-md border border-crm-line bg-white px-4 text-sm font-semibold text-slate-600" disabled>
            {icon}
            {buttonLabel}
          </button>
        </div>
        {items.length ? (
          <div className="flex flex-wrap gap-2">
            {items.map((item) => (
              <span key={item} className="rounded-md bg-blue-50 px-2.5 py-1 text-sm font-medium text-blue-700">
                {item}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm italic text-slate-500">No {title.toLowerCase()} added.</p>
        )}
      </div>
    </FieldShell>
  );
}

export function InteractionForm() {
  const current = useAppSelector((state) => state.interaction.current) ?? emptyInteraction;
  const history = useAppSelector((state) => state.interaction.history);

  return (
    <section className="overflow-hidden rounded-md border border-crm-line bg-white shadow-sm">
      <div className="border-b border-crm-line px-7 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-[16px] font-extrabold tracking-wide text-[#1d2940]">Interaction Details</h2>
          <span className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${current.status === "completed" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
            {current.status ?? "draft"}
          </span>
        </div>
      </div>
      <div className="space-y-4 px-7 py-5">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <DisabledInput field="hcp_name" label="HCP Name" value={text(current.hcp_name, "")} placeholder="Search or select HCP..." />
          <FieldShell field="interaction_type">
            <label className="form-label">Interaction Type</label>
            <select className="form-control" disabled value={current.interaction_type ?? "Meeting"}>
              <option>Meeting</option>
              <option>Call</option>
              <option>Email</option>
              <option>Conference</option>
            </select>
          </FieldShell>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <DisabledInput field="interaction_date" label="Date" value={text(current.interaction_date, "")} placeholder="DD-MM-YYYY" icon={<Calendar size={18} />} />
          <DisabledInput field="interaction_time" label="Time" value={text(current.interaction_time, "")} placeholder="HH:MM" icon={<Clock size={18} />} />
        </div>

        <DisabledInput field="attendees" label="Attendees" value={listText(current.attendees)} placeholder="Enter names or search..." />
        <DisabledTextarea field="topics_discussed" label="Topics Discussed" value={listText(current.topics_discussed)} placeholder="Enter key discussion points..." />

        <button className="inline-flex h-8 items-center gap-2 rounded-md bg-slate-100 px-4 text-[15px] font-bold text-slate-700" disabled>
          <Sparkles size={16} />
          Summarize from Voice Note (Requires Consent)
        </button>

        <div>
          <h3 className="form-label mb-2">Materials Shared / Samples Distributed</h3>
          <div className="space-y-3">
            <AssetBox field="materials_shared" title="Materials Shared" items={current.materials_shared ?? []} buttonLabel="Search/Add" icon={<Search size={17} />} />
            <AssetBox field="samples_distributed" title="Samples Distributed" items={current.samples_distributed ?? []} buttonLabel="Add Sample" icon={<Package size={17} />} />
          </div>
        </div>

        <SentimentRadio sentiment={(current.sentiment ?? "unknown") as Sentiment} />
        <DisabledTextarea field="outcomes" label="Outcomes" value={text(current.outcomes, "")} placeholder="Key outcomes or agreements..." />
        <DisabledTextarea field="follow_up_actions" label="Follow-up Actions" value={listText(current.follow_up_actions)} placeholder="Enter next steps or tasks..." />

        <FieldShell field="ai_suggested_followups">
          <div>
            <h3 className="text-[14px] font-extrabold text-slate-700">AI Suggested Follow-ups:</h3>
            {(current.ai_suggested_followups ?? []).length ? (
              <ul className="mt-1 space-y-1 text-sm font-semibold text-blue-600">
                {current.ai_suggested_followups?.map((item) => <li key={item}>+ {item}</li>)}
              </ul>
            ) : (
              <p className="mt-1 text-sm italic text-slate-500">Suggestions will appear after asking the assistant.</p>
            )}
          </div>
        </FieldShell>

        {history.length ? (
          <div className="rounded-md border border-blue-100 bg-blue-50/60 p-3">
            <h3 className="mb-2 text-sm font-extrabold text-blue-900">Previous Interactions</h3>
            <div className="space-y-2">
              {history.map((item) => (
                <article key={item.id} className="rounded-md border border-blue-100 bg-white p-3 text-sm">
                  <div className="flex items-center justify-between gap-3 font-semibold text-slate-800">
                    <span>{item.hcp_name}</span>
                    <span>{item.interaction_date ?? "No date"}</span>
                  </div>
                  <p className="mt-1 text-slate-600">{item.topics_discussed.join(", ") || item.outcomes || "No details available."}</p>
                </article>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
