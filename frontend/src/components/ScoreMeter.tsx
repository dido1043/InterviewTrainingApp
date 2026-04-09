import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, fonts } from "../theme";

type ScoreMeterProps = {
  score: number;
};

function describeScore(score: number) {
  if (score >= 85) {
    return {
      label: "Strong foundation",
      detail: "The answer already sounds focused. You mainly need polish and repetition.",
      color: colors.mint,
    };
  }

  if (score >= 70) {
    return {
      label: "Good direction",
      detail: "The message is there, but it will land better with sharper structure and cleaner pacing.",
      color: colors.sun,
    };
  }

  return {
    label: "Needs tightening",
    detail: "Focus on clarity, fewer filler phrases, and a more direct result-oriented structure.",
    color: colors.accent,
  };
}

export function ScoreMeter({ score }: ScoreMeterProps) {
  const summary = describeScore(score);

  return (
    <View style={styles.card}>
      <Text style={styles.eyebrow}>Overall Score</Text>
      <View style={styles.row}>
        <Text style={styles.score}>{score}</Text>
        <View style={styles.copy}>
          <Text style={styles.label}>{summary.label}</Text>
          <Text style={styles.detail}>{summary.detail}</Text>
        </View>
      </View>

      <View style={styles.track}>
        <View style={[styles.fill, { width: `${Math.max(0, Math.min(score, 100))}%`, backgroundColor: summary.color }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 24,
    borderRadius: 30,
    backgroundColor: colors.panel,
    borderWidth: 1,
    borderColor: colors.panelMuted,
    gap: 16,
    shadowColor: "#120D09",
    shadowOpacity: 0.14,
    shadowRadius: 18,
    shadowOffset: {
      width: 0,
      height: 12,
    },
    elevation: 6,
  },
  eyebrow: {
    color: colors.accentSoft,
    fontSize: 12,
    fontFamily: fonts.body,
    fontWeight: "700",
    letterSpacing: 1.4,
    textTransform: "uppercase",
  },
  row: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 14,
  },
  score: {
    color: colors.textOnDark,
    fontSize: 56,
    lineHeight: 56,
    fontFamily: fonts.display,
    fontWeight: "700",
  },
  copy: {
    flex: 1,
    gap: 6,
  },
  label: {
    color: colors.textOnDark,
    fontSize: 22,
    lineHeight: 24,
    fontFamily: fonts.display,
    fontWeight: "700",
  },
  detail: {
    color: colors.subtleText,
    fontSize: 15,
    lineHeight: 22,
    fontFamily: fonts.body,
  },
  track: {
    width: "100%",
    height: 14,
    borderRadius: 999,
    backgroundColor: "rgba(255, 247, 239, 0.14)",
    overflow: "hidden",
  },
  fill: {
    height: "100%",
    borderRadius: 999,
  },
});
