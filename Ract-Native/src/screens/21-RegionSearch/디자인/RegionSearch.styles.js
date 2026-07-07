import { StyleSheet } from 'react-native';
import { COLORS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  searchBar: { height: 48, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 14, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 14, marginHorizontal: 24, marginTop: 10 },
  searchInput: { flex: 1, fontSize: 15, color: COLORS.ink },
  content: { paddingHorizontal: 24, paddingTop: 14, paddingBottom: 24, gap: 8 },
  resultCount: { fontSize: 13, fontWeight: '600', color: COLORS.inkMuted48, marginBottom: 4 },
  resultRow: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 12, borderRadius: 14, backgroundColor: COLORS.parchment, marginBottom: 8 },
  resultIcon: { width: 38, height: 38, borderRadius: 9999, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  resultName: { fontSize: 14.5, fontWeight: '700', color: COLORS.ink },
  resultAddress: { fontSize: 12, color: COLORS.inkMuted48 },
  selectedCard: { position: 'absolute', left: 20, right: 20, bottom: 82, backgroundColor: '#fff', borderRadius: 20, padding: 16, paddingBottom: 14, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.16, shadowRadius: 20, elevation: 8 },
  aroundButton: { height: 44, borderRadius: 9999, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center', marginTop: 12 },
  aroundButtonText: { fontSize: 15, fontWeight: '600', color: '#fff' },
});
