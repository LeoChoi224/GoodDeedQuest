import { StyleSheet } from 'react-native';
import { COLORS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: 1, borderBottomColor: COLORS.hairline },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  content: { padding: 20, gap: 20 },
  centerName: { fontSize: 21, fontWeight: '700', color: COLORS.ink },
  centerAddress: { fontSize: 13, color: COLORS.inkMuted48 },
  miniMap: { height: 168, borderRadius: 20, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center' },
  pinWrap: { alignItems: 'center' },
  pin: { width: 38, height: 38, borderRadius: 19, borderBottomRightRadius: 0, transform: [{ rotate: '45deg' }], backgroundColor: COLORS.gold, alignItems: 'center', justifyContent: 'center' },
  infoCard: { backgroundColor: COLORS.parchment, borderRadius: 20, padding: 18, borderWidth: 1, borderColor: COLORS.hairline, gap: 12 },
  infoIconBadge: { width: 34, height: 34, borderRadius: 10, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  infoLabel: { fontSize: 12, fontWeight: '600', color: COLORS.inkMuted48 },
  infoValue: { fontSize: 14.5, fontWeight: '600', color: COLORS.ink },
  infoDesc: { fontSize: 14.5, color: COLORS.ink, lineHeight: 21 },
  divider: { height: 1, backgroundColor: COLORS.hairline, marginVertical: 2 },
  footer: { padding: 20, paddingTop: 12, borderTopWidth: 1, borderTopColor: COLORS.hairline },
  applyButton: { height: 50, borderRadius: 9999, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  applyButtonText: { fontSize: 17, fontWeight: '600', color: '#fff' },
  toast: { position: 'absolute', left: '50%', bottom: 96, transform: [{ translateX: -120 }], width: 240, backgroundColor: COLORS.ink, borderRadius: 9999, paddingVertical: 12, paddingHorizontal: 18, alignItems: 'center' },
  toastText: { color: '#fff', fontSize: 13.5, fontWeight: '600' },
});
