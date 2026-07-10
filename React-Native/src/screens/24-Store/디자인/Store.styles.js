import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: 1, borderBottomColor: COLORS.hairline },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  titleRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, paddingHorizontal: 20, paddingTop: 18, paddingBottom: 4 },
  title: { fontSize: 21, fontWeight: '700', color: COLORS.ink },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, marginTop: 4 },
  pointPill: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingVertical: 7, paddingHorizontal: 12, borderRadius: RADIUS.pill, backgroundColor: COLORS.goldTint, borderWidth: 1, borderColor: 'rgba(201,162,39,0.35)' },
  pointPillText: { fontSize: 13, fontWeight: '700', color: COLORS.gold },
  purchaseListButton: { backgroundColor: COLORS.ink, paddingVertical: 9, paddingHorizontal: 16, borderRadius: RADIUS.pill },
  purchaseListButtonText: { color: '#fff', fontSize: 13, fontWeight: '600' },
  list: { paddingHorizontal: 20, paddingBottom: 20, gap: 12 },
  itemRow: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 18, padding: 12 },
  itemIcon: { width: 56, height: 56, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  itemName: { fontSize: 15, fontWeight: '700', color: COLORS.ink },
  itemDesc: { fontSize: 12.5, color: COLORS.inkMuted48 },
  itemPrice: { fontSize: 12.5, fontWeight: '700', color: COLORS.gold },
  buyButton: { backgroundColor: COLORS.primary, paddingVertical: 9, paddingHorizontal: 14, borderRadius: RADIUS.pill },
  buyButtonText: { color: '#fff', fontSize: 12.5, fontWeight: '600' },
  detailButton: { borderWidth: 1, borderColor: COLORS.hairline, backgroundColor: '#fff', paddingVertical: 6, paddingHorizontal: 10, borderRadius: RADIUS.pill, alignItems: 'center' },
  detailButtonText: { color: COLORS.inkMuted48, fontSize: 11, fontWeight: '600' },
  toast: { position: 'absolute', left: '50%', bottom: 96, transform: [{ translateX: -110 }], width: 220, backgroundColor: COLORS.ink, borderRadius: RADIUS.pill, paddingVertical: 12, alignItems: 'center' },
  toastText: { color: '#fff', fontSize: 13.5, fontWeight: '600' },
});
