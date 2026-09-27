import { useState } from "react";
import apiClient from "../api/client";
import { ContinuitySummary, Patient } from "../types";

export default function PatientContinuity({
  patients,
  onClose,
}: {
  patients: Patient[];
  onClose: () => void;
}) {
  const [patientId, setPatientId] = useState(patients[0]?.patient_id || "");
  const [focus, setFocus] = useState("");
  const [result, setResult] = useState<ContinuitySummary | null>(null);
  const [loading, setLoading] = useState(false);

  async function generate() {
    setLoading(true);
    try {
      const res = await apiClient.post("/continuity/summary", {
        patient_id: patientId,
        focus_text: focus,
        top_k: 5,
      });
      setResult(res.data);
    } finally {
      setLoading(false);
    }
  }

  const selectedPatient = patients.find((p) => p.patient_id === patientId);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="card w-full max-w-md relative">
        <button className="absolute top-4 right-4 text-gray-400" onClick={onClose}>
          ✕
        </button>
        <h3 className="font-medium mb-1">Patient continuity</h3>
        <p className="text-xs text-gray-500 mb-4">
          Uses your last five saved SOAP visits (newest first) for C1, C2, ...,
          plus semantic retrieval over a wider window of saved notes when
          indexed. Optional focus text sharpens vector search.
        </p>

        <label className="text-xs text-gray-400">Focus (optional)</label>
        <input
          className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm mb-3"
          value={focus}
          onChange={(e) => setFocus(e.target.value)}
          placeholder="e.g. stomach pain"
        />

        <label className="text-xs text-gray-400">Patient</label>
        <select
          className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm mb-4"
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
        >
          {patients.map((p) => (
            <option key={p.patient_id} value={p.patient_id}>
              {p.name} ({p.gender ?? "-"}, Age {p.age ?? "-"}, {p.phone ?? "-"})
            </option>
          ))}
        </select>

        <button className="btn-primary w-full mb-4" onClick={generate} disabled={loading}>
          {loading ? "Generating..." : "Generate continuity summary"}
        </button>

        {result && (
          <div className="bg-panel2 border border-border rounded-lg p-3 text-sm max-h-72 overflow-y-auto">
            <p className="font-medium">{selectedPatient?.name}</p>
            <p className="text-xs text-gray-500 mb-2">SOAP visits used: {result.soap_visits_used}</p>
            {!result.semantic_index_available && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 text-yellow-300 text-xs rounded-md p-2 mb-2">
                Semantic index empty for this patient. Save a consultation (or
                re-save) to build embeddings.
              </div>
            )}
            <pre className="whitespace-pre-wrap font-sans">{result.summary_text}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
