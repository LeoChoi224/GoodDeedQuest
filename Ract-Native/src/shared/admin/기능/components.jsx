// components.jsx — 관리자 화면 공통 컴포넌트 (일반 유저 화면과 별도 플로우)
// 하단 3탭(대시보드/유저 관리/신고 검토) + 관리자 전용 햄버거 메뉴(로그아웃 포함)

import React from 'react';
import { View, Text, TouchableOpacity, Modal, Pressable } from 'react-native';
import { X } from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS } from '../../디자인/tokens';
import { CareIcon } from '../../기능/components';
import { styles } from '../디자인/components.styles';

export function AdminHamburgerButton({ onPress }) {
  return (
    <TouchableOpacity onPress={onPress} hitSlop={10} style={{ padding: 10 }}>
      <View style={{ gap: 5 }}>
        <View style={styles.burgerLine} />
        <View style={styles.burgerLine} />
        <View style={styles.burgerLine} />
      </View>
    </TouchableOpacity>
  );
}

export function AdminHamburgerMenu({ visible, onClose, navigation }) {
  return (
    <Modal statusBarTranslucent visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={{ flex: 1, flexDirection: 'row' }}>
        <Pressable style={{ flex: 1 }} onPress={onClose} />
        <LinearGradient colors={['#033236', '#063e42', '#04484d']} locations={[0, 0.55, 1]} style={styles.panel}>
          <View style={styles.menuHeader}>
            <View style={styles.menuLogoBadge}>
              <CareIcon size={16} color={COLORS.mint} />
            </View>
            <Text style={styles.menuLogoText}>선행퀘스트 Admin</Text>
            <View style={{ flex: 1 }} />
            <TouchableOpacity onPress={onClose} hitSlop={10}>
              <X size={20} color="rgba(255,255,255,0.55)" />
            </TouchableOpacity>
          </View>

          <Text style={styles.sectionTitle}>관리자</Text>
          <MenuItem label="대시보드" onPress={() => navigation.navigate('AdminDashboard')} />
          <MenuItem label="유저 목록" onPress={() => navigation.navigate('AdminUserList')} />
          <MenuItem label="신고 검토" onPress={() => navigation.navigate('AdminReports')} />

          <Text style={[styles.sectionTitle, { marginTop: 8 }]}>서비스로 나가기</Text>
          <MenuItem label="메인 화면" onPress={() => navigation.navigate('Main')} />

          <View style={styles.divider} />
          <MenuItem label="로그아웃" muted onPress={() => navigation.navigate('Login')} />
        </LinearGradient>
      </View>
    </Modal>
  );
}

function MenuItem({ label, onPress, muted }) {
  return (
    <TouchableOpacity style={styles.menuItem} onPress={onPress}>
      <Text style={[styles.menuItemText, muted && { color: 'rgba(255,255,255,0.68)', fontWeight: '600' }]}>{label}</Text>
    </TouchableOpacity>
  );
}
