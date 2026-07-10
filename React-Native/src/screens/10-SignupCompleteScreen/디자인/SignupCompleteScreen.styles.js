import { StyleSheet } from 'react-native';

export const COLORS = {
  primary: '#033236',
  canvas: '#FFFFFF',
  ink: '#1D1D1F',
  inkMuted48: '#7A7A7A',
};

export const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  header: {
    paddingHorizontal: 20,
    paddingTop: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  logoBadge: {
    width: 30, height: 30, borderRadius: 9,
    backgroundColor: COLORS.primary,
    alignItems: 'center', justifyContent: 'center',
  },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    gap: 24,
  },
  checkCircle: {
    position: 'absolute',
    width: 96, height: 96, borderRadius: 48,
    backgroundColor: COLORS.primary,
    alignItems: 'center', justifyContent: 'center',
  },
  ripple: {
    position: 'absolute',
    width: 96, height: 96, borderRadius: 48,
    borderWidth: 2, borderColor: COLORS.primary,
  },
  title: { fontSize: 26, fontWeight: '600', color: COLORS.ink },
  subtitle: {
    fontSize: 15, color: COLORS.inkMuted48, marginTop: 10,
    textAlign: 'center', lineHeight: 22,
  },
  footer: { paddingHorizontal: 24, paddingBottom: 24 },
  nextButton: {
    height: 50,
    borderRadius: 9999,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  nextButtonText: { fontSize: 17, fontWeight: '600', color: COLORS.canvas },
});
