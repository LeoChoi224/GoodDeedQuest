/**
 * Pixel city skyline silhouette at the base of the hero — ported from
 * 01_login_flow.dc.html renderVals() skyline SVG (crispEdges, preserveAspectRatio none).
 */
import React from 'react';
import Svg, { Path, Rect } from 'react-native-svg';

const c1 = '#02282B';
const c2 = '#01353A';
const c3 = '#022F33';

export default function Skyline({ width, height }: { width: number; height: number }) {
  return (
    <Svg width={width} height={height} viewBox="0 0 100 40" preserveAspectRatio="none">
      <Path
        d="M0 40 V22 h6 v-3 h6 v-4 h6 v4 h8 v4 h10 v-6 h6 v-3 h6 v3 h6 v6 h10 v-4 h8 v4 h6 v-2 h6 v2 h8 V40 Z"
        fill={c3}
        opacity={0.55}
      />
      <Rect x={40} y={24} width={20} height={16} fill={c2} />
      <Rect x={44} y={20} width={3} height={20} fill={c2} />
      <Rect x={53} y={18} width={3} height={22} fill={c2} />
      <Rect x={44} y={18} width={1} height={2} fill={c2} />
      <Rect x={46} y={18} width={1} height={2} fill={c2} />
      <Rect x={53} y={16} width={1} height={2} fill={c2} />
      <Rect x={55} y={16} width={1} height={2} fill={c2} />
      <Rect x={10} y={28} width={6} height={12} fill={c1} />
      <Rect x={8} y={30} width={10} height={2} fill={c1} />
      <Rect x={22} y={30} width={5} height={10} fill={c1} />
      <Rect x={20} y={32} width={9} height={2} fill={c1} />
      <Rect x={70} y={27} width={6} height={13} fill={c1} />
      <Rect x={68} y={29} width={10} height={2} fill={c1} />
      <Rect x={84} y={30} width={5} height={10} fill={c1} />
      <Rect x={82} y={32} width={9} height={2} fill={c1} />
      <Rect x={0} y={37} width={100} height={3} fill={c1} />
    </Svg>
  );
}
