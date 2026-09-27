export interface Patient {
  patient_id: string;
  name: string;
  age?: number;
  gender?: string;
  phone?: string;
  email?: string;
  address?: string;
}

export interface SpeakerSegment {
  speaker_type: "DOCTOR" | "PATIENT" | "UNKNOWN";
  speaker_label: string;
  start_time: number;
  end_time: number;
  text: string;
}

export interface Entity {
  entity_text: string;
  entity_type: string;
}

export interface SOAPNote {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

export interface ConsultationResult {
  consultation_id: string;
  status: string;
  transcript_text?: string;
  segments: SpeakerSegment[];
  entities: Entity[];
  soap_note?: SOAPNote;
}

export interface ContinuitySummary {
  patient_id: string;
  soap_visits_used: number;
  semantic_index_available: boolean;
  summary_text: string;
}
