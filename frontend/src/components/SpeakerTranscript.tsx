import { SpeakerSegment } from "../types";

export default function SpeakerTranscript({ segments }: { segments: SpeakerSegment[] }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium">Doctor–patient conversation</h3>
        <span className="text-xs text-gray-500">{segments.length} turns</span>
      </div>
      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
        {segments.map((s, i) => (
          <div
            key={i}
            className={`rounded-lg px-3 py-2 text-sm ${
              s.speaker_type === "DOCTOR"
                ? "bg-blue-500/10 border border-blue-500/30"
                : "bg-green-500/10 border border-green-500/30"
            }`}
          >
            <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
              <span className="font-medium text-gray-200">
                {s.speaker_type === "DOCTOR" ? `Doctor (${s.speaker_label})` : "Patient"}
              </span>
              <span>{s.start_time.toFixed(1)}s</span>
            </div>
            <p>{s.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
