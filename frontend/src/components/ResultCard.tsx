import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, fonts } from "../theme";

type ResultCardProps = {
  accentColor: string;
  eyebrow: string;
  title: string;
  children: React.ReactNode;
};

export function ResultCard({ accentColor, eyebrow, title, children }: ResultCardProps) {
  return (
    <View style={styles.card}>
      <View style={[styles.accent, { backgroundColor: accentColor }]} />
      <Text style={styles.eyebrow}>{eyebrow}</Text>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.body}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 22,
    borderRadius: 30,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.outline,
    gap: 10,
    shadowColor: "#241B12",
    shadowOpacity: 0.08,
    shadowRadius: 16,
    shadowOffset: {
      width: 0,
      height: 10,
    },
    elevation: 4,
  },
  accent: {
    width: 72,
    height: 6,
    borderRadius: 999,
  },
  eyebrow: {
    color: colors.mutedDark,
    fontSize: 12,
    fontFamily: fonts.body,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  title: {
    color: colors.ink,
    fontSize: 26,
    lineHeight: 30,
    fontFamily: fonts.display,
    fontWeight: "700",
  },
  body: {
    marginTop: 4,
  },
});
