/**
 * SVG icons ported 1:1 from 01_login_flow.dc.html renderVals() (React.createElement → react-native-svg).
 * shapeRendering:crispEdges is emulated where relevant; line icons keep round joins.
 */
import React from 'react';
import Svg, { Path, Rect, Circle, Line } from 'react-native-svg';

type IconProps = { size?: number; color?: string };

export const MailIcon = ({ size = 20, color = '#033236' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 10 10">
    <Rect x={0} y={1} width={10} height={8} fill="none" stroke={color} strokeWidth={1} />
    <Path d="M1 2 L5 6 L9 2" fill="none" stroke={color} strokeWidth={1} />
  </Svg>
);

export const LockIcon = ({ size = 20, color = '#033236' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 10 10">
    <Rect x={2} y={4} width={6} height={5} fill={color} />
    <Path d="M3 4 V2.5 h1 V2 h2 v0.5 h1 V4" fill="none" stroke={color} strokeWidth={1} />
    <Rect x={4.5} y={5.5} width={1} height={2} fill="#FFF8E7" />
  </Svg>
);

export const SwordIcon = ({ size = 18 }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 12 12">
    <Path d="M9 1h2v2L6 8v1H5v1H4v1H2v-1h1v-1h1V7h1V6z" fill="#fff" />
    <Rect x={2} y={7} width={3} height={1} fill="#D4A017" />
    <Rect x={3} y={8} width={1} height={2} fill="#D4A017" />
  </Svg>
);

export const EyeOpen = ({ size = 20, color = '#9CA3AF' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
    <Circle cx={12} cy={12} r={3} />
  </Svg>
);

export const EyeOff = ({ size = 20, color = '#9CA3AF' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c6.5 0 10 8 10 8a18.5 18.5 0 0 1-2.16 3.19M6.61 6.61A18.5 18.5 0 0 0 2 12s3.5 8 10 8a9.12 9.12 0 0 0 5.39-1.61" />
    <Path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
    <Line x1={2} y1={2} x2={22} y2={22} />
  </Svg>
);

export const KakaoIcon = ({ size = 18 }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="#191919">
    <Path d="M12 3C6.5 3 2 6.6 2 11c0 2.8 1.9 5.3 4.7 6.7-.2.7-.7 2.6-.8 3-.1.5.2.5.4.4.2-.1 2.6-1.8 3.6-2.5.7.1 1.4.2 2.1.2 5.5 0 10-3.6 10-8S17.5 3 12 3z" />
  </Svg>
);

export const GoogleIcon = ({ size = 18 }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24">
    <Path fill="#4285F4" d="M23 12.3c0-.8-.1-1.5-.2-2.3H12v4.5h6.2a5.3 5.3 0 0 1-2.3 3.5v2.9h3.7c2.2-2 3.4-5 3.4-8.6z" />
    <Path fill="#34A853" d="M12 24c3.1 0 5.7-1 7.6-2.8l-3.7-2.9c-1 .7-2.4 1.1-3.9 1.1-3 0-5.5-2-6.4-4.7H1.7v3C3.6 21.4 7.5 24 12 24z" />
    <Path fill="#FBBC05" d="M5.6 14.7a7.2 7.2 0 0 1 0-4.6v-3H1.7a12 12 0 0 0 0 10.6l3.9-3z" />
    <Path fill="#EA4335" d="M12 4.8c1.7 0 3.2.6 4.4 1.7l3.3-3.3C17.7 1.2 15.1 0 12 0 7.5 0 3.6 2.6 1.7 6.4l3.9 3C6.5 6.8 9 4.8 12 4.8z" />
  </Svg>
);

export const CalIcon = ({ size = 20, color = '#6B7280' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <Rect x={3} y={4} width={18} height={18} rx={3} />
    <Line x1={3} y1={9} x2={21} y2={9} />
    <Line x1={8} y1={2} x2={8} y2={6} />
    <Line x1={16} y1={2} x2={16} y2={6} />
  </Svg>
);

export const HamburgerIcon = ({ size = 24, color = '#FFF8E7' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round">
    <Line x1={4} y1={7} x2={20} y2={7} />
    <Line x1={4} y1={12} x2={20} y2={12} />
    <Line x1={4} y1={17} x2={20} y2={17} />
  </Svg>
);

export const ChevronLeft = ({ size = 24, color = '#1A1A1A' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M15 18l-6-6 6-6" />
  </Svg>
);

export const PencilIcon = ({ size = 14, color = '#1A1A1A' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19 3 20l1-4Z" />
  </Svg>
);

export const CheckMark = ({ size = 13, color = '#fff' }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M5 12l5 5L20 6" />
  </Svg>
);

/**
 * Status bar signal + battery glyphs (dark = #1A1A1A for light screens, light = #fff for hero).
 */
export const StatusGlyphs = ({ color = '#1A1A1A' }: { color?: string }) => (
  <Svg width={18} height={12} viewBox="0 0 18 12">
    <Rect x={0} y={7} width={3} height={5} rx={1} fill={color} />
    <Rect x={5} y={4} width={3} height={8} rx={1} fill={color} />
    <Rect x={10} y={1.5} width={3} height={10.5} rx={1} fill={color} />
    <Rect x={15} y={0} width={3} height={12} rx={1} fill={color} opacity={0.35} />
  </Svg>
);

export const BatteryGlyph = ({ color = '#1A1A1A' }: { color?: string }) => (
  <Svg width={26} height={12} viewBox="0 0 26 12">
    <Rect x={0.5} y={0.5} width={21} height={11} rx={3} fill="none" stroke={color} opacity={0.5} />
    <Rect x={2.5} y={2.5} width={16} height={7} rx={1.5} fill={color} />
    <Rect x={23} y={4} width={2} height={4} rx={1} fill={color} opacity={0.6} />
  </Svg>
);
