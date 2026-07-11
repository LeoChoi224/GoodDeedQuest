/**
 * KoreaMapDrilldown — 대한민국 행정구역 드릴다운 지도.
 * korea_map_drilldown.html 에서 추출한 실제 SGIS 경계 데이터(assets/maps/korea_drilldown.json)를
 * react-native-svg 로 렌더한다. 전국(시/도) → 시/도 탭 → 시군구 지도로 드릴다운, 뒤로가기.
 * 선행퀘스트 컨셉(양피지·틸·골드)으로 채색하고, 우리 팀 지역은 골드로 강조.
 */
import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, Pressable, useWindowDimensions } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import Animated, { FadeIn } from 'react-native-reanimated';
import { colors, fonts } from '../theme';

type PathDef = { name: string; d: string };
type MapDef = { viewBox: string; paths: PathDef[] };
type DrillData = { national: MapDef; provinces: Record<string, MapDef> };

// require avoids JSON-module TS config concerns; Metro bundles it.
// eslint-disable-next-line @typescript-eslint/no-var-requires
const DRILL: DrillData = require('../../assets/maps/korea_drilldown.json');

const MAP_COLORS = {
  landFill: '#E3EFE4',
  landStroke: '#A9C2B2',
  team: '#D4A017',
  teamStroke: '#8A6A1E',
  selected: '#0A4F55',
  sigunguFill: '#F5EDD6',
  sigunguStroke: '#CBB27A',
  sigunguTeam: '#D4A017',
};

function vbSize(vb: string) {
  const p = vb.split(/\s+/).map(Number);
  return { w: p[2] || 800, h: p[3] || 760 };
}

// map a national 시/도 name to a provinces[] key (exact, else 2-char prefix)
function provinceKey(name: string): string | null {
  if (DRILL.provinces[name]) return name;
  const pre = name.slice(0, 2);
  const hit = Object.keys(DRILL.provinces).find((k) => k.startsWith(pre));
  return hit ?? null;
}

export default function KoreaMapDrilldown({
  teamRegion = '경기도',
  teamSigungu = '안양시',
  onRegion,
  onSigungu,
  height = 300,
  initialProvince,
  allowNational = true,
  drillOnRegionTap = true,
}: {
  teamRegion?: string;
  teamSigungu?: string;
  onRegion?: (name: string) => void;
  onSigungu?: (name: string, province: string) => void;
  height?: number;
  /** start locked on this province's 시군구 map (e.g. Ranking screen). */
  initialProvince?: string;
  /** show the "← 전국" back button (false = locked to the province). */
  allowNational?: boolean;
  /** national 시/도 tap drills in place; false = only fire onRegion (navigate elsewhere). */
  drillOnRegionTap?: boolean;
}) {
  const { width } = useWindowDimensions();
  const [province, setProvince] = useState<string | null>(
    initialProvince ? provinceKey(initialProvince) : null
  );
  const [pressed, setPressed] = useState<string | null>(null);

  const boxW = Math.min(width - 40, 360);

  const map = province && DRILL.provinces[province] ? DRILL.provinces[province] : DRILL.national;
  const { w, h } = vbSize(map.viewBox);
  const svgH = (boxW * h) / w;

  const onLandPress = (name: string) => {
    if (province) {
      onSigungu?.(name, province);
    } else {
      const key = provinceKey(name);
      onRegion?.(name);
      if (key && drillOnRegionTap) setProvince(key);
    }
  };

  // Reliable tap targets: transparent Pressable per region (bounding box of its path),
  // scaled to screen. RN Pressables always fire — unlike <Path onPress> which is flaky
  // inside a ScrollView on the New Architecture. Smaller regions render last (on top)
  // so a small 시/도 inside a big one (예: 서울 안의 경기) stays tappable.
  const regions = useMemo(() => {
    const scale = boxW / w;
    return map.paths
      .map((p) => {
        const nums = (p.d.match(/-?\d+(?:\.\d+)?/g) || []).map(Number);
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (let i = 0; i + 1 < nums.length; i += 2) {
          const x = nums[i], y = nums[i + 1];
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
        if (!isFinite(minX)) return null;
        return {
          name: p.name,
          left: minX * scale,
          top: minY * scale,
          width: Math.max((maxX - minX) * scale, 10),
          height: Math.max((maxY - minY) * scale, 10),
          area: (maxX - minX) * (maxY - minY),
        };
      })
      .filter(Boolean)
      .sort((a, b) => (b as any).area - (a as any).area) as {
      name: string; left: number; top: number; width: number; height: number; area: number;
    }[];
  }, [map, boxW, w]);

  return (
    <View>
      {/* toolbar: back / title */}
      <View style={styles.bar}>
        {province && allowNational ? (
          <Pressable style={styles.backBtn} onPress={() => setProvince(null)} hitSlop={8}>
            <Text style={styles.backText}>← 전국</Text>
          </Pressable>
        ) : (
          <View style={styles.tag}>
            <View style={styles.dot} />
            <Text style={styles.tagText}>우리 팀 · {teamRegion}</Text>
          </View>
        )}
        <Text style={styles.title}>{province ?? '대한민국 행정구역'}</Text>
      </View>

      {/* map — SVG는 시각용, 탭은 위의 투명 Pressable 오버레이가 처리(터치 신뢰성) */}
      <Animated.View key={province ?? 'nat'} entering={FadeIn.duration(220)} style={[styles.mapWrap, { height: svgH }]}>
        <View style={{ width: boxW, height: svgH }}>
          <Svg width={boxW} height={svgH} viewBox={map.viewBox} style={StyleSheet.absoluteFill}>
            {map.paths.map((p) => {
              const isTeam = province
                ? p.name.startsWith(teamSigungu.slice(0, 2))
                : p.name === teamRegion || p.name.startsWith(teamRegion.slice(0, 2));
              const isPressed = pressed === p.name;
              const fill = isPressed
                ? MAP_COLORS.selected
                : isTeam
                ? province
                  ? MAP_COLORS.sigunguTeam
                  : MAP_COLORS.team
                : province
                ? MAP_COLORS.sigunguFill
                : MAP_COLORS.landFill;
              const stroke = province ? MAP_COLORS.sigunguStroke : MAP_COLORS.landStroke;
              return (
                <Path
                  key={p.name || p.d.slice(0, 12)}
                  d={p.d}
                  fill={fill}
                  stroke={isTeam ? MAP_COLORS.teamStroke : stroke}
                  strokeWidth={isTeam ? 1.4 : 0.8}
                />
              );
            })}
          </Svg>

          {regions.map((r) => (
            <Pressable
              key={r.name || `${r.left},${r.top}`}
              style={{ position: 'absolute', left: r.left, top: r.top, width: r.width, height: r.height }}
              hitSlop={2}
              onPressIn={() => setPressed(r.name)}
              onPressOut={() => setPressed(null)}
              onPress={() => onLandPress(r.name)}
            />
          ))}
        </View>
      </Animated.View>

      <Text style={styles.hint}>
        {province ? '시군구를 눌러 상세 랭킹을 확인하세요' : '시 · 도를 눌러 지역을 확대하세요'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, minHeight: 28 },
  backBtn: { backgroundColor: colors.primaryDark, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 5 },
  backText: { color: colors.parchment, fontSize: 12, fontWeight: '700', fontFamily: fonts.bodyB },
  tag: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(212,160,23,0.14)', borderWidth: 1, borderColor: 'rgba(212,160,23,0.5)', borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.gold },
  tagText: { fontSize: 11, fontWeight: '700', color: '#8A6A1E', fontFamily: fonts.bodyB },
  title: { fontFamily: fonts.pixel, fontSize: 14, color: colors.primaryDark },
  mapWrap: { alignItems: 'center', justifyContent: 'center' },
  hint: { textAlign: 'center', fontSize: 11.5, color: colors.textSecondary, marginTop: 8, fontFamily: fonts.bodyM },
});
