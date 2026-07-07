// components.styles.js — shared/기능/components.jsx가 사용하는 StyleSheet
import { StyleSheet } from 'react-native';
import { COLORS, TYPE } from './tokens';

export const styles = StyleSheet.create({
  burgerLine: { width: 22, height: 2, borderRadius: 1, backgroundColor: COLORS.ink },
  bottomNav: { flexDirection: 'row', justifyContent: 'space-around', paddingTop: 10, paddingBottom: 20, borderTopWidth: 1, borderTopColor: COLORS.hairline, backgroundColor: COLORS.canvas },
  navItem: { alignItems: 'center', gap: 4, width: 56 },
  navLabel: { ...TYPE.micro, color: COLORS.inkMuted48 },
  menuOverlayRow: { flex: 1, flexDirection: 'row' },
  menuPanel: { width: '78%', maxWidth: 300, paddingTop: 26, paddingHorizontal: 18, paddingBottom: 28 },
  menuHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingTop: 6, marginBottom: 18 },
  menuLogoBadge: { width: 28, height: 28, borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.1)', alignItems: 'center', justifyContent: 'center' },
  menuLogoText: { fontSize: 17, fontWeight: '700', color: '#fff', letterSpacing: -0.3 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 9, paddingHorizontal: 8, borderRadius: 11 },
  sectionTitle: { fontSize: 11, fontWeight: '700', letterSpacing: 1, color: COLORS.mint, textTransform: 'uppercase' },
  menuItemRow: { paddingVertical: 9, paddingHorizontal: 8, paddingLeft: 20, borderRadius: 11 },
  menuItemRowText: { fontSize: 14.5, fontWeight: '600', color: '#fff' },
  menuDivider: { height: 1, backgroundColor: 'rgba(255,255,255,0.12)', marginVertical: 10 },
  menuFooterItem: { paddingVertical: 9, paddingHorizontal: 8, borderRadius: 11 },
  menuFooterItemText: { fontSize: 14, fontWeight: '600', color: 'rgba(255,255,255,0.68)' },
});
