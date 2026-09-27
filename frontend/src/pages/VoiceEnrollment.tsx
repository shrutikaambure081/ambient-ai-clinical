import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";

const ALL_LANGUAGES = [
  "English", "Hindi", "Kannada", "Tamil", "Telugu",
  "Malayalam", "Marathi", "Bengali", "Gujarati", "Punjabi",
];

const SAMPLE_SENTENCE =
  "Clinical documentation is essential for quality patient care and professional accountability.";

export default function VoiceEnrollment() {
  const [step, setStep] = useState<"languages" | "record">("languages");
  const [selected, setSelected] = useState<string[]>(["English"]);
  const [recording, setRecording] = useState(false);
  const [verified, setVerified] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const navigate = useNavigate();

  function toggleLanguage(lang: string) {
    setSelected((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  }

  async function handleContinue() {
    await apiClient.post("/auth/fluent-languages", { languages: selected });
    setStep("record");
  }

  async function startRecording() {
    setRecording(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      recorder.start();
    } catch {
      // Microphone unavailable (e.g. no permissions) -- allow manual verify.
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  async function verifySample() {
    await apiClient.post(`/auth/voice-enrollment?language=${selected[0]}`);
    setVerified(true);
    setTimeout(() => navigate("/dashboard"), 600);
  }

  if (step === "languages") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="card w-full max-w-lg space-y-5">
          <h1 className="text-xl font-semibold">Fluent languages</h1>
          <p className="text-sm text-gray-400">
            You'll record a short phrase in each language for voice matching.
          </p>
          <div className="flex flex-wrap gap-2">
            {ALL_LANGUAGES.map((lang) => (
              <span
                key={lang}
                onClick={() => toggleLanguage(lang)}
                className={`chip ${selected.includes(lang) ? "chip-selected" : ""}`}
              >
                {lang}
              </span>
            ))}
          </div>
          <button className="btn-primary" onClick={handleContinue}>
            Continue
          </button>
          <p className="text-xs text-gray-500">
            Not a cache issue: this screen comes from your account's enrollment
            state on the server. Clearing site data only removes the login
            session stored in this browser.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="card w-full max-w-lg space-y-5 text-center">
        <h1 className="text-xl font-semibold text-left">Voice enrollment</h1>
        <p className="text-sm text-gray-400 text-left">Language: {selected[0]}</p>
        <div className="border border-border rounded-xl p-4 text-left">
          <p className="text-xs text-gray-500 mb-1">READ THIS SENTENCE</p>
          <p className="text-sm">{SAMPLE_SENTENCE}</p>
        </div>
        <div className="py-10">
          <button
            onClick={recording ? stopRecording : startRecording}
            className={`w-20 h-20 rounded-full border-2 ${
              recording ? "border-red-500 text-red-500" : "border-accent text-accent"
            } flex items-center justify-center mx-auto text-2xl`}
          >
            🎙
          </button>
          <p className="text-xs text-gray-500 mt-3">
            {recording ? "Recording..." : "Tap to record"}
          </p>
        </div>
        <div className="flex gap-3 justify-center">
          <button className="btn-primary" onClick={verifySample} disabled={verified}>
            {verified ? "Verified ✓" : "Verify sample"}
          </button>
          <button className="btn-secondary" onClick={() => setStep("languages")}>
            Retry recording
          </button>
        </div>
      </div>
    </div>
  );
}
