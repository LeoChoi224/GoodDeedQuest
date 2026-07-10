import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: 1, borderBottomColor: COLORS.hairline },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  content: { padding: 20, gap: 18 },
  imageBox: { height: 220, borderRadius: 24, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center' },
  infoCard: { backgroundColor: COLORS.parchment, borderRadius: 20, padding: 18, borderWidth: 1, borderColor: COLORS.hairline, gap: 10 },
  itemName: { fontSize: 21, fontWeight: '700', color: COLORS.ink },
  itemDesc: { fontSize: 14, color: COLORS.inkMuted48, lineHeight: 20, marginTop: 2 },
  divider: { height: 1, backgroundColor: COLORS.hairline, marginVertical: 2 },
  priceLabel: { fontSize: 12, fontWeight: '600', color: COLORS.inkMuted48 },
  priceValue: { fontSize: 16, fontWeight: '700', color: COLORS.gold },
  myPointRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 4 },
  myPointLabel: { fontSize: 12.5, color: COLORS.inkMuted48 },
  myPointValue: { fontSize: 13, fontWeight: '700', color: COLORS.ink },
  footer: { padding: 20, paddingTop: 12, borderTopWidth: 1, borderTopColor: COLORS.hairline },
  buyButton: { height: 50, borderRadius: RADIUS.pill, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  buyButtonText: { fontSize: 17, fontWeight: '600', color: '#fff' },
  toast: { position: 'absolute', left: '50%', bottom: 96, transform: [{ translateX: -110 }], width: 220, backgroundColor: COLORS.ink, borderRadius: RADIUS.pill, paddingVertical: 12, alignItems: 'center' },
  toastText: { color: '#fff', fontSize: 13.5, fontWeight: '600' },
  confirmOverlay: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32, backgroundColor: 'rgba(3,50,54,0.4)' },
  confirmCard: { width: '100%', maxWidth: 280, backgroundColor: '#fff', borderRadius: 22, padding: 22, paddingTop: 26, alignItems: 'center', gap: 18 },
  confirmTitle: { fontSize: 16.5, fontWeight: '700', color: COLORS.ink, textAlign: 'center' },
  confirmPrice: { fontSize: 13, fontWeight: '600', color: COLORS.gold },
  confirmCancel: { flex: 1, height: 44, borderRadius: RADIUS.pill, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: 'rgba(0,0,0,0.1)', alignItems: 'center', justifyContent: 'center' },
  confirmCancelText: { fontSize: 14.5, fontWeight: '600', color: COLORS.ink },
  confirmOk: { flex: 1, height: 44, borderRadius: RADIUS.pill, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  confirmOkText: { fontSize: 14.5, fontWeight: '600', color: '#fff' },
});
