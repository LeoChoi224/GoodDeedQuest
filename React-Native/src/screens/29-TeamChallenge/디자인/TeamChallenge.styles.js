import { StyleSheet } from 'react-native';
import { COLORS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  content: { flex: 1, paddingHorizontal: 24, paddingTop: 28, gap: 26 },
  title: { fontSize: 24, fontWeight: '600', color: COLORS.ink, lineHeight: 32 },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, marginTop: 8 },
  optionCard: { flexDirection: 'row', alignItems: 'center', gap: 14, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 20, padding: 20 },
  optionIcon: { width: 48, height: 48, borderRadius: 14, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  optionTitle: { fontSize: 16, fontWeight: '700', color: COLORS.ink },
  optionDesc: { fontSize: 13, color: COLORS.inkMuted48, lineHeight: 18 },
});
