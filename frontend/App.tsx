import React, { useState } from "react";
import { StatusBar } from "expo-status-bar";
import * as DocumentPicker from "expo-document-picker";
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { analyzeInterview, inferMimeType } from "./src/api/interviewApi";
import { ResultCard } from "./src/components/ResultCard";
import { ScoreMeter } from "./src/components/ScoreMeter";
import { colors, fonts } from "./src/theme";
import type { InterviewAnalysis, SelectedAudio } from "./src/types/analysis";

function formatFileSize(size: number | null | undefined): string {
  if (!size) {
    return "Unknown size";
  }

  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let index = 0;

  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }

  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function getFileBadge(name: string): string {
  const extension = name.split(".").pop()?.trim().toUpperCase() ?? "AUDIO";
  return extension.slice(0, 4);
}

const flowSteps = [
  "Drop in a short interview answer from your phone.",
  "The app sends the recording straight to the backend analyzer.",
  "Practice the tightened version until it sounds natural.",
];

export default function App() {
  const [selectedAudio, setSelectedAudio] = useState<SelectedAudio | null>(null);
  const [analysis, setAnalysis] = useState<InterviewAnalysis | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const pickAudio = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      copyToCacheDirectory: true,
      multiple: false,
      type: ["audio/*"],
    });

    if (result.canceled) {
      return;
    }

    const asset = result.assets[0];
    if (!asset) {
      return;
    }

    setSelectedAudio({
      uri: asset.uri,
      name: asset.name ?? "interview-answer.wav",
      mimeType: asset.mimeType ?? inferMimeType(asset.name ?? ""),
      size: asset.size ?? null,
      webFile: asset.file ?? null,
    });
    setAnalysis(null);
    setErrorMessage(null);
  };

  const submitForAnalysis = async () => {
    if (!selectedAudio) {
      setErrorMessage("Choose an audio file before requesting analysis.");
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMessage(null);
      const nextAnalysis = await analyzeInterview({
        audio: selectedAudio,
      });
      setAnalysis(nextAnalysis);
    } catch (error) {
      setAnalysis(null);
      setErrorMessage(
        error instanceof Error ? error.message : "The analysis request failed unexpectedly.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <View pointerEvents="none" style={styles.haloTop} />
      <View pointerEvents="none" style={styles.haloBottom} />
      <View pointerEvents="none" style={styles.meshCard} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.heroCard}>
          <View style={styles.heroGlow} />
          <View style={styles.heroHeader}>
            <Text style={styles.kicker}>Interview Studio</Text>
            <View style={styles.statusPill}>
              <View style={styles.statusDot} />
              <Text style={styles.statusText}>Instant coaching</Text>
            </View>
          </View>

          <Text style={styles.title}>Practice answers that sound calmer, sharper, and more hireable.</Text>
          <Text style={styles.subtitle}>
            Choose a recording and the app will send it straight to the backend for scoring, filler
            detection, critique, and a cleaner script to rehearse.
          </Text>

          <View style={styles.heroMetrics}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>1 tap</Text>
              <Text style={styles.metricLabel}>Upload flow</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>4 signals</Text>
              <Text style={styles.metricLabel}>Score, fillers, critique, rewrite</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>Mobile</Text>
              <Text style={styles.metricLabel}>Built for quick practice loops</Text>
            </View>
          </View>
        </View>

        <View style={styles.studioCard}>
          <View style={styles.studioHeader}>
            <View>
              <Text style={styles.sectionEyebrow}>Recording</Text>
              <Text style={styles.sectionTitle}>Drop in your latest answer</Text>
            </View>
            <View style={styles.sectionBadge}>
              <Text style={styles.sectionBadgeText}>Audio upload</Text>
            </View>
          </View>

          {selectedAudio ? (
            <View style={styles.fileCard}>
              <View style={styles.fileIcon}>
                <Text style={styles.fileIconText}>{getFileBadge(selectedAudio.name)}</Text>
              </View>
              <View style={styles.fileCopy}>
                <Text numberOfLines={1} style={styles.fileName}>
                  {selectedAudio.name}
                </Text>
                <Text style={styles.fileMeta}>
                  {formatFileSize(selectedAudio.size)} · {selectedAudio.mimeType}
                </Text>
              </View>
            </View>
          ) : (
            <View style={styles.placeholderCard}>
              {flowSteps.map((step, index) => (
                <View key={step} style={styles.stepRow}>
                  <View style={styles.stepNumber}>
                    <Text style={styles.stepNumberText}>{index + 1}</Text>
                  </View>
                  <Text style={styles.stepText}>{step}</Text>
                </View>
              ))}
            </View>
          )}

          <View style={styles.actions}>
            <Pressable onPress={pickAudio} style={({ pressed }) => [styles.secondaryButton, pressed && styles.buttonPressed]}>
              <Text style={styles.secondaryButtonText}>
                {selectedAudio ? "Replace recording" : "Choose recording"}
              </Text>
            </Pressable>

            <Pressable
              disabled={isSubmitting || !selectedAudio}
              onPress={submitForAnalysis}
              style={({ pressed }) => [
                styles.primaryButton,
                (pressed || isSubmitting) && styles.buttonPressed,
                (!selectedAudio || isSubmitting) && styles.buttonDisabled,
              ]}
            >
              {isSubmitting ? (
                <ActivityIndicator color={colors.textOnDark} />
              ) : (
                <Text style={styles.primaryButtonText}>Analyze recording</Text>
              )}
            </Pressable>
          </View>

          {errorMessage ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          ) : null}
        </View>

        {analysis ? (
          <View style={styles.results}>
            <ScoreMeter score={analysis.score} />

            <ResultCard accentColor={colors.accent} eyebrow="Filler Words" title="Words worth smoothing out">
              {analysis.filler_words.length > 0 ? (
                <View style={styles.tagWrap}>
                  {analysis.filler_words.map((word) => (
                    <View key={word} style={styles.tag}>
                      <Text style={styles.tagText}>{word}</Text>
                    </View>
                  ))}
                </View>
              ) : (
                <Text style={styles.cardBody}>
                  No obvious filler words were flagged in this answer. That already makes the
                  delivery sound steadier.
                </Text>
              )}
            </ResultCard>

            <ResultCard accentColor={colors.mint} eyebrow="Coach Critique" title="What to improve next">
              <Text style={styles.cardBody}>{analysis.critique}</Text>
            </ResultCard>

            <ResultCard accentColor={colors.sun} eyebrow="Improved Script" title="Tighter version to practice">
              <Text style={styles.cardBody}>{analysis.improved_script}</Text>
            </ResultCard>
          </View>
        ) : (
          <View style={styles.previewCard}>
            <Text style={styles.previewEyebrow}>What this session gives you</Text>
            <Text style={styles.previewTitle}>A faster practice loop, without setup friction in the screen.</Text>
            <View style={styles.previewGrid}>
              <View style={styles.previewItem}>
                <Text style={styles.previewItemTitle}>Sharper feedback</Text>
                <Text style={styles.previewItemText}>
                  See where hesitation or filler language weakens the answer.
                </Text>
              </View>
              <View style={styles.previewItem}>
                <Text style={styles.previewItemTitle}>Clean rewrite</Text>
                <Text style={styles.previewItemText}>
                  Rehearse a tighter version immediately after every upload.
                </Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    paddingHorizontal: 18,
    paddingTop: 14,
    paddingBottom: 42,
    gap: 18,
  },
  haloTop: {
    position: "absolute",
    top: -50,
    right: -30,
    width: 240,
    height: 240,
    borderRadius: 999,
    backgroundColor: "rgba(244, 107, 78, 0.18)",
  },
  haloBottom: {
    position: "absolute",
    bottom: 80,
    left: -70,
    width: 220,
    height: 220,
    borderRadius: 999,
    backgroundColor: "rgba(183, 216, 243, 0.20)",
  },
  meshCard: {
    position: "absolute",
    top: 220,
    right: -80,
    width: 220,
    height: 220,
    borderRadius: 48,
    backgroundColor: "rgba(166, 217, 200, 0.12)",
    transform: [{ rotate: "-16deg" }],
  },
  heroCard: {
    overflow: "hidden",
    padding: 24,
    borderRadius: 34,
    backgroundColor: colors.panel,
    borderWidth: 1,
    borderColor: colors.panelMuted,
    gap: 18,
    shadowColor: "#1A120B",
    shadowOpacity: 0.18,
    shadowRadius: 24,
    shadowOffset: {
      width: 0,
      height: 16,
    },
    elevation: 7,
  },
  heroGlow: {
    position: "absolute",
    top: -60,
    right: -30,
    width: 180,
    height: 180,
    borderRadius: 999,
    backgroundColor: "rgba(255, 212, 199, 0.16)",
  },
  heroHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
  },
  kicker: {
    color: colors.accentSoft,
    fontSize: 12,
    letterSpacing: 1.8,
    textTransform: "uppercase",
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: "rgba(166, 217, 200, 0.14)",
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 999,
    backgroundColor: colors.mint,
  },
  statusText: {
    color: colors.textOnDark,
    fontSize: 13,
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  title: {
    color: colors.textOnDark,
    fontSize: 38,
    lineHeight: 42,
    fontFamily: fonts.display,
    fontWeight: "700",
  },
  subtitle: {
    color: colors.subtleText,
    fontSize: 16,
    lineHeight: 24,
    fontFamily: fonts.body,
  },
  heroMetrics: {
    gap: 10,
  },
  metricCard: {
    padding: 14,
    borderRadius: 22,
    backgroundColor: "rgba(255, 247, 239, 0.08)",
    borderWidth: 1,
    borderColor: "rgba(255, 247, 239, 0.08)",
    gap: 4,
  },
  metricValue: {
    color: colors.textOnDark,
    fontSize: 20,
    lineHeight: 22,
    fontFamily: fonts.display,
    fontWeight: "700",
  },
  metricLabel: {
    color: colors.subtleText,
    fontSize: 14,
    lineHeight: 20,
    fontFamily: fonts.body,
  },
  studioCard: {
    padding: 22,
    borderRadius: 32,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.outline,
    gap: 16,
    shadowColor: "#2D2012",
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: {
      width: 0,
      height: 10,
    },
    elevation: 4,
  },
  studioHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 12,
  },
  sectionEyebrow: {
    color: colors.mutedDark,
    fontSize: 12,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  sectionTitle: {
    marginTop: 6,
    color: colors.ink,
    fontSize: 30,
    lineHeight: 32,
    fontFamily: fonts.display,
    fontWeight: "700",
  },
  sectionBadge: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: colors.paperAlt,
  },
  sectionBadgeText: {
    color: colors.deepAccent,
    fontSize: 13,
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  fileCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    padding: 16,
    borderRadius: 24,
    backgroundColor: colors.paperAlt,
    borderWidth: 1,
    borderColor: colors.outline,
  },
  fileIcon: {
    width: 54,
    height: 54,
    borderRadius: 18,
    backgroundColor: colors.panel,
    alignItems: "center",
    justifyContent: "center",
  },
  fileIconText: {
    color: colors.textOnDark,
    fontSize: 13,
    fontFamily: fonts.body,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  fileCopy: {
    flex: 1,
    gap: 4,
  },
  fileName: {
    color: colors.ink,
    fontSize: 18,
    lineHeight: 22,
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  fileMeta: {
    color: colors.mutedDark,
    fontSize: 14,
    fontFamily: fonts.mono,
  },
  placeholderCard: {
    padding: 18,
    borderRadius: 24,
    backgroundColor: colors.backgroundAlt,
    borderWidth: 1,
    borderColor: colors.outline,
    gap: 14,
  },
  stepRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 999,
    backgroundColor: colors.panel,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
  },
  stepNumberText: {
    color: colors.textOnDark,
    fontSize: 13,
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  stepText: {
    flex: 1,
    color: colors.ink,
    fontSize: 15,
    lineHeight: 22,
    fontFamily: fonts.body,
  },
  actions: {
    gap: 10,
  },
  primaryButton: {
    minHeight: 58,
    borderRadius: 20,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 18,
    shadowColor: "#B64D36",
    shadowOpacity: 0.2,
    shadowRadius: 14,
    shadowOffset: {
      width: 0,
      height: 8,
    },
    elevation: 4,
  },
  primaryButtonText: {
    color: colors.textOnDark,
    fontSize: 16,
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  secondaryButton: {
    minHeight: 56,
    borderRadius: 20,
    backgroundColor: colors.panel,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 18,
  },
  secondaryButtonText: {
    color: colors.textOnDark,
    fontSize: 16,
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  buttonPressed: {
    opacity: 0.9,
    transform: [{ scale: 0.99 }],
  },
  buttonDisabled: {
    opacity: 0.55,
  },
  errorBox: {
    padding: 14,
    borderRadius: 18,
    backgroundColor: colors.errorBg,
  },
  errorText: {
    color: colors.errorText,
    fontSize: 14,
    lineHeight: 20,
    fontFamily: fonts.body,
    fontWeight: "600",
  },
  results: {
    gap: 16,
  },
  tagWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  tag: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: colors.paperAlt,
    borderWidth: 1,
    borderColor: colors.outline,
  },
  tagText: {
    color: colors.ink,
    fontSize: 15,
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  cardBody: {
    color: colors.ink,
    fontSize: 16,
    lineHeight: 24,
    fontFamily: fonts.body,
  },
  previewCard: {
    padding: 22,
    borderRadius: 30,
    backgroundColor: colors.paperAlt,
    borderWidth: 1,
    borderColor: colors.outline,
    gap: 14,
  },
  previewEyebrow: {
    color: colors.mutedDark,
    fontSize: 12,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    fontFamily: fonts.body,
    fontWeight: "700",
  },
  previewTitle: {
    color: colors.ink,
    fontSize: 26,
    lineHeight: 30,
    fontFamily: fonts.display,
    fontWeight: "700",
  },
  previewGrid: {
    gap: 12,
  },
  previewItem: {
    padding: 16,
    borderRadius: 22,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.outline,
    gap: 6,
  },
  previewItemTitle: {
    color: colors.ink,
    fontSize: 18,
    lineHeight: 22,
    fontFamily: fonts.display,
    fontWeight: "700",
  },
  previewItemText: {
    color: colors.mutedDark,
    fontSize: 15,
    lineHeight: 22,
    fontFamily: fonts.body,
  },
});
