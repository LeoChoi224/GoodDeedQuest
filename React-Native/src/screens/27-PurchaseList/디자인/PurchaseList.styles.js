import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: 1, borderBottomColor: COLORS.hairline },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  title: { fontSize: 21, fontWeight: '700', color: COLORS.ink },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, marginTop: 4 },
  list: { paddingHorizontal: 20, paddingBottom: 20, gap: 12 },
  itemRow: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 18, padding: 12 },
  itemIcon: { width: 56, height: 56, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  itemName: { fontSize: 15, fontWeight: '700', color: COLORS.ink },
  itemDesc: { fontSize: 12.5, color: COLORS.inkMuted48 },
  equippedTag: { fontSize: 10, fontWeight: '700', color: COLORS.primary, backgroundColor: COLORS.goldTint, borderWidth: 1, borderColor: 'rgba(201,162,39,0.35)', paddingVertical: 2, paddingHorizontal: 7, borderRadius: RADIUS.pill },
  equippedTagText: { fontSize: 10, fontWeight: '700', color: COLORS.primary },
  detailLink: { fontSize: 11.5, fontWeight: '600', color: COLORS.inkMuted48, textDecorationLine: 'underline', marginTop: 2 },
  toggleButton: { paddingVertical: 10, paddingHorizontal: 16, borderRadius: RADIUS.pill },
  toggleButtonText: { fontSize: 12.5, fontWeight: '600' },
});
