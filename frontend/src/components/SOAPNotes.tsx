import { useState } from "react";
import { SOAPNote } from "../types";
import apiClient from "../api/client";

export default function SOAPNotes({
  consultationId,
  soapNote,
}: {
  consultationId: string;
  soapNote: SOAPNote;
}) {
  const [note, setNote] = useState<SOAPNote>(soapNote);
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await apiClient.put(`/consultations/${consultationId}/soap`, note);
    } finally {
      setSaving(false);
    }
  }

  const fields: (keyof SOAPNote)[] = ["subjective", "objective", "assessment", "plan"];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-medium">SOAP notes</h3>
        <button className="btn-secondary text-xs" onClick={save} disabled={saving}>
          {saving ? "Saving..." : "Save"}
        </button>
      </div>
      <p className="text-xs text-gray-500 mb-3">Edit before saving — LLM output may need corrections.</p>
      <div className="space-y-4">
        {fields.map((f) => (
          <div key={f}>
            <p className="text-xs uppercase tracking-wide text-gray-400 mb-1">{f}</p>
            <textarea
              className="w-full bg-panel2 border border-border rounded-lg p-2 text-sm min-h-[70px]"
              value={note[f]}
              onChange={(e) => setNote({ ...note, [f]: e.target.value })}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
