import { NativeModules, Platform } from "react-native";

import type { AnalysisResponse, InterviewAnalysis, SelectedAudio } from "../types/analysis";

const envApiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.trim() ?? "";

const mimeTypeMap: Record<string, string> = {
  aac: "audio/aac",
  m4a: "audio/mp4",
  mp3: "audio/mpeg",
  wav: "audio/wav",
  webm: "audio/webm",
};

export function inferMimeType(fileName: string): string {
  const extension = fileName.split(".").pop()?.toLowerCase() ?? "";
  return mimeTypeMap[extension] ?? "audio/wav";
}

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, "");
}

function readBundleHost(): string | null {
  const scriptUrl = NativeModules.SourceCode?.scriptURL;
  if (typeof scriptUrl === "string" && scriptUrl.length > 0) {
    const match = scriptUrl.match(/^[a-z]+:\/\/([^/:?#]+)(?::\d+)?/i);
    if (match?.[1]) {
      return match[1];
    }
  }

  if (
    typeof globalThis.window !== "undefined" &&
    typeof globalThis.window.location?.hostname === "string" &&
    globalThis.window.location.hostname.length > 0
  ) {
    return globalThis.window.location.hostname;
  }

  return null;
}

function resolveApiBaseUrl(): string {
  if (envApiBaseUrl) {
    return normalizeBaseUrl(envApiBaseUrl);
  }

  const bundleHost = readBundleHost();
  if (bundleHost) {
    return `http://${bundleHost}:8000`;
  }

  if (Platform.OS === "android") {
    return "http://10.0.2.2:8000";
  }

  return "http://127.0.0.1:8000";
}

export const defaultApiBaseUrl = resolveApiBaseUrl();
export const defaultAnalyzeUrl = buildAnalyzeUrl(defaultApiBaseUrl);

function buildAnalyzeUrl(apiBaseUrl: string): string {
  const trimmed = normalizeBaseUrl(apiBaseUrl);

  if (!trimmed) {
    throw new Error("The app could not determine the backend address.");
  }

  if (trimmed.endsWith("/api/analyze")) {
    return trimmed;
  }

  if (trimmed.endsWith("/api")) {
    return `${trimmed}/analyze`;
  }

  return `${trimmed}/api/analyze`;
}

type AnalyzeInterviewParams = {
  audio: SelectedAudio;
};

async function createUploadPart(audio: SelectedAudio): Promise<File | Blob | { uri: string; name: string; type: string }> {
  if (Platform.OS === "web") {
    if (audio.webFile) {
      return audio.webFile;
    }

    const fileResponse = await fetch(audio.uri);
    const blob = await fileResponse.blob();
    return blob;
  }

  return {
    uri: audio.uri,
    name: audio.name,
    type: audio.mimeType || inferMimeType(audio.name),
  };
}

function getErrorDetail(payload: AnalysisResponse | { detail?: string | Array<{ loc?: unknown[]; msg?: string }> } | null): string {
  if (!payload || typeof payload !== "object" || !("detail" in payload)) {
    return "The backend could not analyze this file.";
  }

  if (typeof payload.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload.detail) && payload.detail.length > 0) {
    return payload.detail
      .map((item) => item?.msg)
      .filter((msg): msg is string => typeof msg === "string" && msg.length > 0)
      .join(" ");
  }

  return "The backend could not analyze this file.";
}

export async function analyzeInterview({
  audio,
}: AnalyzeInterviewParams): Promise<InterviewAnalysis> {
  const formData = new FormData();
  const uploadPart = await createUploadPart(audio);
  formData.append("file", uploadPart as any, audio.name);

  let response: Response;
  const analyzeUrl = defaultAnalyzeUrl;

  try {
    response = await fetch(analyzeUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
      body: formData,
    });
  } catch (_error) {
    throw new Error(
      `Could not reach the interview analysis service at ${analyzeUrl}. Make sure the FastAPI backend is running and reachable on port 8000.`,
    );
  }

  const payload = (await response.json().catch(() => null)) as AnalysisResponse | {
    detail?: string | Array<{ loc?: unknown[]; msg?: string }>;
  } | null;

  if (!response.ok) {
    throw new Error(getErrorDetail(payload));
  }

  if (!payload || typeof payload !== "object" || !("data" in payload) || !payload.data) {
    throw new Error("The backend returned an unexpected response.");
  }

  return payload.data;
}
