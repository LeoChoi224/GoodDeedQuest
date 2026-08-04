/**
 * 공통 배경 — "뿌연 그린 그라데이션" (CLAUDE.md).
 * Web uses radial-gradients + blur(70-85px) blobs. RN has no cheap blur, so we
 * approximate: LinearGradient base + large translucent circles (soft, low-opacity)
 * to read as hazy green glow. Tone/opacity kept per spec.
 */
import React from 'react';
import { View, StyleSheet, DimensionValue } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { hazeBase, hazeBlobs } from '../theme';

export default function HazeBackground({ children }: { children?: React.ReactNode }) {
  return (
    <View style={StyleSheet.absoluteFill}>
      <LinearGradient
        colors={hazeBase.colors}
        start={hazeBase.start}
        end={hazeBase.end}
        style={StyleSheet.absoluteFill}
      />
      <View style={[StyleSheet.absoluteFill, styles.clip]} pointerEvents="none">
        {hazeBlobs.map((b, i) => (
          <View
            key={i}
            style={{
              position: 'absolute',
              width: b.size,
              height: b.size,
              borderRadius: b.size / 2,
              backgroundColor: b.color,
              opacity: b.opacity * 0.75, // dial down since we can't blur as much
              top: (b as any).top as DimensionValue,
              left: (b as any).left as DimensionValue,
              right: (b as any).right as DimensionValue,
              bottom: (b as any).bottom as DimensionValue,
            }}
          />
        ))}
      </View>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  clip: { overflow: 'hidden' },
});
