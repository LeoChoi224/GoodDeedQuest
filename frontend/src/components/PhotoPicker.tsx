/**
 * 인증용 다중 사진 선택기 — photos[0]이 대표(AI 판정 대상).
 * 대표는 크게, 추가 사진은 아래 가로 썸네일 줄. 썸네일 탭 → 대표로 승격.
 */
import React from 'react';
import { View, Text, Image, StyleSheet, Pressable, ScrollView } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { colors, fonts, radii } from '../theme';
import { useToast } from './Toast';
import { CameraIcon } from '../screens/quest/_parts';

type Props = {
  photos: string[];
  onChange: (photos: string[]) => void;
  max?: number;
  disabled?: boolean;
  /** primary: 첫 장이 AI 판정 대상(크게 표시) | extras: 전부 보조 사진(썸네일 줄만) */
  variant?: 'primary' | 'extras';
};

export default function PhotoPicker({ photos, onChange, max = 5, disabled = false, variant = 'primary' }: Props) {
  const toast = useToast();
  const remaining = max - photos.length;

  const pick = async () => {
    if (disabled) return;
    if (remaining <= 0) {
      toast.show(`사진은 최대 ${max}장까지 올릴 수 있어요.`);
      return;
    }
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      toast.show('사진 접근 권한을 허용해 주세요.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.7,
      allowsMultipleSelection: true,
      selectionLimit: remaining,
    });
    if (result.canceled) return;

    // 이미 담긴 사진은 제외(중복 업로드 방지) 후 남은 자리만큼만 수용
    const picked = result.assets.map((a) => a.uri).filter((uri) => !photos.includes(uri));
    const accepted = picked.slice(0, remaining);
    if (picked.length > accepted.length) {
      toast.show(`사진은 최대 ${max}장까지 올릴 수 있어요.`);
    }
    if (accepted.length === 0) return;
    onChange([...photos, ...accepted]);
  };

  const promote = (index: number) => {
    const next = [...photos];
    [next[0], next[index]] = [next[index], next[0]];
    onChange(next);
  };

  const remove = (index: number) => {
    onChange(photos.filter((_, i) => i !== index));
  };

  // 보조 사진 모드 — 판정 대상이 따로 있으므로 대표 개념 없이 썸네일 줄만 보여준다.
  if (variant === 'extras') {
    return (
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.thumbRow}>
        {photos.map((uri, index) => (
          <View key={uri} style={styles.thumb}>
            <Image source={{ uri }} style={StyleSheet.absoluteFill} resizeMode="cover" />
            <Pressable onPress={() => remove(index)} hitSlop={6} style={styles.thumbClear}>
              <Text style={styles.clearX}>×</Text>
            </Pressable>
          </View>
        ))}
        {remaining > 0 && (
          <Pressable onPress={pick} style={styles.addThumb}>
            <Text style={styles.addPlus}>+</Text>
          </Pressable>
        )}
      </ScrollView>
    );
  }

  return (
    <View>
      {/* 대표 사진 */}
      <Pressable onPress={photos.length ? undefined : pick} style={styles.mainWrap}>
        {photos.length ? (
          <View style={styles.mainFill}>
            <Image source={{ uri: photos[0] }} style={StyleSheet.absoluteFill} resizeMode="cover" />
            <View style={styles.badge}>
              <Text style={styles.badgeText}>AI가 이 사진으로 판정해요</Text>
            </View>
            <Pressable onPress={() => remove(0)} hitSlop={8} style={styles.mainClear}>
              <Text style={styles.clearX}>×</Text>
            </Pressable>
          </View>
        ) : (
          <View style={styles.mainEmpty}>
            <CameraIcon size={40} color="#8AA598" />
            <Text style={styles.emptyText}>사진 추가하기</Text>
          </View>
        )}
      </Pressable>

      {/* 추가 사진 썸네일 줄 */}
      {photos.length > 0 && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.thumbRow}>
          {photos.slice(1).map((uri, i) => {
            const index = i + 1;
            return (
              <Pressable key={uri} onPress={() => promote(index)} style={styles.thumb}>
                <Image source={{ uri }} style={StyleSheet.absoluteFill} resizeMode="cover" />
                <Pressable onPress={() => remove(index)} hitSlop={6} style={styles.thumbClear}>
                  <Text style={styles.clearX}>×</Text>
                </Pressable>
              </Pressable>
            );
          })}
          {remaining > 0 && (
            <Pressable onPress={pick} style={styles.addThumb}>
              <Text style={styles.addPlus}>+</Text>
            </Pressable>
          )}
        </ScrollView>
      )}

      {photos.length > 1 && <Text style={styles.hint}>추가 사진을 탭하면 대표 사진으로 바꿀 수 있어요</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  mainWrap: { height: 180, borderRadius: radii.input, overflow: 'hidden', marginBottom: 10 },
  mainEmpty: {
    flex: 1, borderRadius: radii.input, borderWidth: 2, borderColor: colors.primaryDark,
    borderStyle: 'dashed', backgroundColor: colors.screenBg,
    alignItems: 'center', justifyContent: 'center', gap: 8,
  },
  emptyText: { fontSize: 15, color: colors.textSecondary, fontWeight: '600', fontFamily: fonts.bodyM },
  mainFill: { flex: 1, borderRadius: radii.input, borderWidth: 2, borderColor: colors.primaryDark, overflow: 'hidden' },
  badge: {
    position: 'absolute', left: 8, bottom: 8, backgroundColor: 'rgba(3,50,54,0.82)',
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999,
  },
  badgeText: { color: colors.white, fontSize: 11, fontWeight: '700', fontFamily: fonts.bodyM },
  mainClear: {
    position: 'absolute', top: 8, right: 8, width: 26, height: 26, borderRadius: 13,
    backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center',
  },
  clearX: { fontSize: 15, lineHeight: 17, color: colors.textPrimary },

  thumbRow: { gap: 8, paddingRight: 4, paddingBottom: 2 },
  thumb: { width: 64, height: 64, borderRadius: 10, overflow: 'hidden', borderWidth: 1, borderColor: colors.inputBorder },
  thumbClear: {
    position: 'absolute', top: 2, right: 2, width: 20, height: 20, borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.92)', alignItems: 'center', justifyContent: 'center',
  },
  addThumb: {
    width: 64, height: 64, borderRadius: 10, borderWidth: 2, borderStyle: 'dashed',
    borderColor: colors.primaryDark, backgroundColor: colors.screenBg,
    alignItems: 'center', justifyContent: 'center',
  },
  addPlus: { fontSize: 26, lineHeight: 30, color: colors.primaryDark },
  hint: { marginTop: 8, fontSize: 11, color: colors.textMuted, fontFamily: fonts.bodyR },
});