// 28-Community.js — React Native (Expo) 커뮤니티 메인페이지
// 선행퀘스트 / 스토리보드 28번 기준 — 인스타 피드 스타일 (게시물 1개씩, 좋아요/댓글/메뉴 바텀시트)

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Heart, MessageCircle, MoreHorizontal, Flag, ThumbsUp, ThumbsDown } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/Community.styles';

const POSTS = [
  { id: 'p1', userId: '@min_kindness', avatarInitial: '민', avatarColor: COLORS.mint, timeAgo: '12분 전', questTitle: '노약자 자리 양보하기', caption: '지하철에서 어르신께 자리를 양보해드렸어요. 감사하다는 말씀에 하루가 밝아졌어요 :)', likeCount: 24, commentCount: 3 },
  { id: 'p2', userId: '@haneul_92', avatarInitial: '하', avatarColor: COLORS.gold, timeAgo: '38분 전', questTitle: '헌혈하기', caption: '오랜만에 헌혈하고 왔습니다. 다들 한 번씩 도전해보세요!', likeCount: 41, commentCount: 7 },
  { id: 'p3', userId: '@doyoon_j', avatarInitial: '도', avatarColor: COLORS.primary, timeAgo: '1시간 전', questTitle: '엄마한테 사과하기', caption: '미뤄왔던 사과, 오늘 드디어 했어요. 마음이 한결 가벼워졌습니다.', likeCount: 16, commentCount: 2 },
];

const COMMENTS = {
  p1: [
    { user: '@haneul_92', initial: '하', color: COLORS.gold, text: '멋져요! 저도 오늘 해봐야겠어요' },
    { user: '@doyoon_j', initial: '도', color: COLORS.primary, text: '이런 작은 배려가 큰 힘이 되는 것 같아요' },
  ],
  p2: [{ user: '@min_kindness', initial: '민', color: COLORS.mint, text: '저도 다음 달에 도전할게요!' }],
  p3: [{ user: '@haneul_92', initial: '하', color: COLORS.gold, text: '용기 내신 거 대단해요' }],
};

export default function CommunityScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [likes, setLikes] = useState({});
  const [commentsPostId, setCommentsPostId] = useState(null);
  const [postMenuId, setPostMenuId] = useState(null);

  const toggleLike = (id) => setLikes((s) => ({ ...s, [id]: !s[id] }));
  const openProfile = (post) => navigation.navigate('UserDetail', { userId: post.userId, nickname: post.userId.replace('@', ''), avatarInitial: post.avatarInitial, avatarColor: post.avatarColor });

  const activeComments = commentsPostId ? COMMENTS[commentsPostId] || [] : [];

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={{ flex: 1 }} />
          <TouchableOpacity style={styles.challengeButton} onPress={() => navigation.navigate('TeamChallenge')}>
            <Text style={styles.challengeButtonText}>팀 챌린지</Text>
          </TouchableOpacity>
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView>
          {POSTS.map((post) => {
            const liked = !!likes[post.id];
            const count = post.likeCount + (liked ? 1 : 0);
            return (
              <View key={post.id} style={styles.postBlock}>
                <View style={styles.postHeaderRow}>
                  <TouchableOpacity onPress={() => openProfile(post)}>
                    <View style={[styles.avatar, { backgroundColor: post.avatarColor }]}>
                      <Text style={styles.avatarText}>{post.avatarInitial}</Text>
                    </View>
                  </TouchableOpacity>
                  <TouchableOpacity style={{ flex: 1, flexDirection: 'row', alignItems: 'baseline', gap: 5 }} onPress={() => openProfile(post)}>
                    <Text style={styles.userId}>{post.userId}</Text>
                    <Text style={styles.timeAgo}>· {post.timeAgo}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={() => setPostMenuId(post.id)} hitSlop={8}>
                    <MoreHorizontal size={18} color={COLORS.ink} />
                  </TouchableOpacity>
                </View>

                <View style={styles.mediaPlaceholder}>
                  <Text style={styles.mediaPlaceholderText}>{post.questTitle} 인증 사진</Text>
                </View>

                <View style={styles.actionsRow}>
                  <TouchableOpacity onPress={() => toggleLike(post.id)}>
                    <Heart size={24} color={liked ? '#FF3B30' : COLORS.ink} fill={liked ? '#FF3B30' : 'none'} strokeWidth={1.8} />
                  </TouchableOpacity>
                  <TouchableOpacity onPress={() => setCommentsPostId(post.id)}>
                    <MessageCircle size={24} color={COLORS.ink} strokeWidth={1.8} />
                  </TouchableOpacity>
                </View>

                <Text style={styles.likeCount}>좋아요 {count}개</Text>
                <Text style={styles.caption}>
                  <Text style={{ fontWeight: '700' }}>{post.userId}</Text> {post.caption}
                </Text>
                <TouchableOpacity onPress={() => setCommentsPostId(post.id)}>
                  <Text style={styles.commentLink}>댓글 {post.commentCount}개 모두 보기</Text>
                </TouchableOpacity>
              </View>
            );
          })}
        </ScrollView>

        <BottomNav navigation={navigation} active="community" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {/* 댓글 바텀시트 */}
        <Modal statusBarTranslucent visible={!!commentsPostId} transparent animationType="slide" onRequestClose={() => setCommentsPostId(null)}>
          <View style={styles.sheetOverlay}>
            <Pressable style={{ flex: 1 }} onPress={() => setCommentsPostId(null)} />
            <View style={[styles.sheet, { height: '62%' }]}>
              <View style={styles.sheetHandle} />
              <Text style={styles.sheetTitle}>댓글 {activeComments.length}개</Text>
              <ScrollView style={{ marginTop: 12 }} contentContainerStyle={{ gap: 16, paddingBottom: 20 }}>
                {activeComments.map((c, i) => (
                  <View key={i} style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
                    <View style={[styles.avatar, { width: 30, height: 30, backgroundColor: c.color }]}>
                      <Text style={[styles.avatarText, { fontSize: 12 }]}>{c.initial}</Text>
                    </View>
                    <View style={{ gap: 2, flex: 1 }}>
                      <Text style={{ fontSize: 13, fontWeight: '600', color: COLORS.ink }}>{c.user}</Text>
                      <Text style={{ fontSize: 14, color: COLORS.ink, lineHeight: 19 }}>{c.text}</Text>
                    </View>
                  </View>
                ))}
              </ScrollView>
            </View>
          </View>
        </Modal>

        {/* 게시물 옵션 바텀시트 */}
        <Modal statusBarTranslucent visible={!!postMenuId} transparent animationType="slide" onRequestClose={() => setPostMenuId(null)}>
          <View style={styles.sheetOverlay}>
            <Pressable style={{ flex: 1 }} onPress={() => setPostMenuId(null)} />
            <View style={styles.sheet}>
              <View style={styles.sheetHandle} />
              <TouchableOpacity style={styles.optionRow} onPress={() => setPostMenuId(null)}>
                <ThumbsUp size={19} color={COLORS.primary} />
                <Text style={styles.optionText}>선호</Text>
              </TouchableOpacity>
              <View style={styles.optionDivider} />
              <TouchableOpacity style={styles.optionRow} onPress={() => setPostMenuId(null)}>
                <ThumbsDown size={19} color={COLORS.inkMuted48} />
                <Text style={styles.optionText}>비선호</Text>
              </TouchableOpacity>
              <View style={styles.optionDivider} />
              <TouchableOpacity style={styles.optionRow} onPress={() => setPostMenuId(null)}>
                <Flag size={19} color="#E24C4C" />
                <Text style={[styles.optionText, { color: '#E24C4C' }]}>신고하기</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.cancelRow} onPress={() => setPostMenuId(null)}>
                <Text style={styles.optionText}>취소</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

