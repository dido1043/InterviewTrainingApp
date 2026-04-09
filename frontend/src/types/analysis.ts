export type InterviewAnalysis = {
  score: number;
  filler_words: string[];
  critique: string;
  improved_script: string;
};

export type AnalysisResponse = {
  status: string;
  data: InterviewAnalysis;
};

export type SelectedAudio = {
  uri: string;
  name: string;
  mimeType: string;
  size?: number | null;
  webFile?: File | Blob | null;
};
