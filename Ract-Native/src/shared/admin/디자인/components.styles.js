import { StyleSheet } from 'react-native';
import { COLORS } from '../../디자인/tokens';

export const styles = StyleSheet.create({
  burgerLine: { width: 22, height: 2, borderRadius: 1, backgroundColor: COLORS.ink },
  panel: { width: '78%', maxWidth: 300, paddingTop: 26, paddingHorizontal: 18, paddingBottom: 28, gap: 4 },
  menuHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingTop: 6, marginBottom: 14 },
  menuLogoBadge: { width: 28, height: 28, borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.1)', alignItems: 'center', justifyContent: 'center' },
  menuLogoText: { fontSize: 15, fontWeight: '700', color: '#fff' },
  sectionTitle: { fontSize: 11, fontWeight: '700', letterSpacing: 1, color: COLORS.mint, textTransform: 'uppercase', paddingVertical: 9, paddingHorizontal: 8 },
  menuItem: { paddingVertical: 9, paddingHorizontal: 8, paddingLeft: 20, borderRadius: 11 },
  menuItemText: { fontSize: 14.5, fontWeight: '600', color: '#fff' },
  divider: { height: 1, backgroundColor: 'rgba(255,255,255,0.12)', marginVertical: 10 },
});
