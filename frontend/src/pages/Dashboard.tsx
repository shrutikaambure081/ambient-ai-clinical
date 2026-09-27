import { useEffect, useRef, useState } from "react";
import apiClient from "../api/client";
import Navbar from "../components/Navbar";
import SpeakerTranscript from "../components/SpeakerTranscript";
import SOAPNotes from "../components/SOAPNotes";
import PatientContinuity from "../components/PatientContinuity";
import { ConsultationResult, Patient } from "../types";

export default function Dashboard() {
  const [clinicianName, setClinicianName] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [activePatientId, setActivePatientId] = useState<string>("");
  const [recording, setRecording] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<ConsultationResult | null>(null);
  const [showContinuity, setShowContinuity] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    apiClient.get("/auth/me").then((res) => setClinicianName(res.data.name));
    apiClient.get("/patients").then((res) => {
      setPatients(res.data);
      if (res.data.length) setActivePatientId(res.data[0].patient_id);
    });
  }, []);

  async function toggleRecording() {
    if (recording) {
      mediaRecorderRef.current?.stop();
      setRecording(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioFile(new File([blob], "consultation.webm", { type: "audio/webm" }));
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch {
      alert("Microphone access is required to record a consultation.");
    }
  }

  function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files?.[0]) setAudioFile(e.target.files[0]);
  }

  async function runPipeline() {
    if (!audioFile || !activePatientId) return;
    setProcessing(true);
    setResult(null);
    try {
      const form = new FormData();
      form.append("audio", audioFile);
      form.append("visit_type", "NEW");
      const res = await apiClient.post(
        `/consultations/${activePatientId}/process`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setResult(res.data);
    } finally {
      setProcessing(false);
    }
  }

  return (
    <div className="min-h-screen bg-black">
      <Navbar clinicianName={`Dr. ${clinicianName}`} />

      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-400">
            Use the microphone first. Session is stored automatically.
          </p>
          <button className="btn-secondary" onClick={() => setShowContinuity(true)}>
            🕒 View Patient history
          </button>
        </div>

        <div className="card">
          <h3 className="font-medium mb-1">1. Consultation audio</h3>
          <p className="text-xs text-gray-500 mb-4">
            Primary: live microphone. Optional: upload a file only if
            recording isn't possible.
          </p>

          <select
            className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm mb-4"
            value={activePatientId}
            onChange={(e) => setActivePatientId(e.target.value)}
          >
            {patients.map((p) => (
              <option key={p.patient_id} value={p.patient_id}>
                {p.name}
              </option>
            ))}
          </select>

          <div className="border border-dashed border-border rounded-xl py-10 text-center">
            <button
              onClick={toggleRecording}
              className={`w-16 h-16 rounded-full border-2 mx-auto flex items-center justify-center text-2xl ${
                recording ? "border-red-500 text-red-500" : "border-accent text-accent"
              }`}
            >
              🎙
            </button>
            <p className="text-xs text-gray-500 mt-3">
              {recording ? "Recording..." : audioFile ? audioFile.name : "Tap to record"}
            </p>
          </div>

          <details className="mt-4 text-sm text-gray-400">
            <summary className="cursor-pointer">
              Fallback: upload audio file (.wav, .mp3, .webm)
            </summary>
            <input type="file" accept="audio/*" onChange={handleFileUpload} className="mt-2 text-xs" />
          </details>

          <button
            className="btn-primary mt-5"
            onClick={runPipeline}
            disabled={!audioFile || processing}
          >
            {processing ? "Running clinical pipeline..." : "Run clinical pipeline"}
          </button>
        </div>

        {result && (
          <div className="grid md:grid-cols-2 gap-6">
            <SpeakerTranscript segments={result.segments} />
            {result.soap_note && (
              <SOAPNotes consultationId={result.consultation_id} soapNote={result.soap_note} />
            )}
          </div>
        )}

        {result && result.entities.length > 0 && (
          <div className="card">
            <h3 className="font-medium mb-3">Extracted clinical entities</h3>
            <div className="flex flex-wrap gap-2">
              {result.entities.map((e, i) => (
                <span key={i} className="chip">
                  {e.entity_text} <span className="text-gray-500">· {e.entity_type}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {showContinuity && (
        <PatientContinuity patients={patients} onClose={() => setShowContinuity(false)} />
      )}
    </div>
  );
}
