// 15-QuestChatbot.js — React Native (Expo) AI 추천 챗봇 (대화형 퀘스트 추천)
// 선행퀘스트 / 스토리보드 15번 기준
// 경로: 메인 -> (커스텀 추천 버튼) -> 이 화면

import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Animated, Easing } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Send } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon } from '../../../shared/기능/components';
import { styles } from '../디자인/QuestChatbot.styles';

const CATEGORIES = [
  { id: 'family', label: '가족', quests: [{ title: '엄마한테 사과하기' }] },
  { id: 'neighbor', label: '이웃', quests: [{ title: '이웃 어르신 짐 들어드리기' }, { title: '노약자 자리 양보하기' }] },
  { id: 'environment', label: '환경', quests: [{ title: '동네 쓰레기 줍기' }] },
  { id: 'animal', label: '동물', quests: [{ title: '유기동물 보호소 봉사' }] },
  { id: 'vulnerable', label: '취약계층', quests: [{ title: '헌혈하기' }, { title: '노약자 자리 양보하기' }] },
];
const TIME_OPTIONS = [{ id: 't5', label: '5분 이내' }, { id: 't30', label: '30분 이내' }, { id: 't60', label: '1시간 이상' }];

let seq = 0;
function nextId() { seq += 1; return 'm' + seq; }

function TypingDot({ delay }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 330, delay, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration: 770, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, []);
  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, -4] });
  return <Animated.View style={[styles.typingDot, { transform: [{ translateY }] }]} />;
}

export default function QuestChatbotScreen({ navigation }) {
  const [step, setStep] = useState('category');
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState([{ id: nextId(), from: 'bot', text: '안녕하세요! 어떤 선행을 해볼까요? 관심 있는 분야를 골라주세요.' }]);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const selectCategory = (cat) => {
    setMessages((m) => [...m, { id: nextId(), from: 'user', text: cat.label }]);
    setSelectedCategoryId(cat.id);
    setStep('thinking');
    setTimeout(() => {
      setMessages((m) => [...m, { id: nextId(), from: 'bot', text: '좋아요! 오늘 얼마나 시간을 낼 수 있나요?' }]);
      setStep('time');
    }, 500);
  };

  const selectTime = (t) => {
    setMessages((m) => [...m, { id: nextId(), from: 'user', text: t.label }]);
    setStep('searching');
    const typingId = nextId();
    setMessages((m) => [...m, { id: typingId, from: 'bot', typing: true }]);
    setTimeout(() => {
      const cat = CATEGORIES.find((c) => c.id === selectedCategoryId);
      const quests = (cat ? cat.quests : []).slice(0, 2);
      setMessages((m) => [...m.filter((x) => x.id !== typingId), { id: nextId(), from: 'bot', text: '회원님께 어울리는 퀘스트를 찾았어요!', quests }]);
      setStep('result');
    }, 1200);
  };

  const restart = () => {
    setStep('category');
    setSelectedCategoryId(null);
    setMessages((m) => [...m, { id: nextId(), from: 'bot', text: '좋아요, 다시 골라볼까요? 관심 있는 분야를 선택해주세요.' }]);
  };

  const sendFreeText = () => {
    const text = inputText.trim();
    if (!text) return;
    setMessages((m) => [...m, { id: nextId(), from: 'user', text }]);
    setInputText('');
    setTimeout(() => {
      setMessages((m) => [...m, { id: nextId(), from: 'bot', text: '네, 참고할게요! 아래 선택지 중에서 골라주시면 더 정확하게 추천해드릴 수 있어요.' }]);
    }, 500);
  };

  const goToQuestDetail = (title) => navigation.navigate('QuestDetail', { quest: { title, exp: 20, points: 30 } });

  let chipOptions = [];
  if (step === 'category') chipOptions = CATEGORIES.map((c) => ({ ...c, onClick: () => selectCategory(c) }));
  else if (step === 'time') chipOptions = TIME_OPTIONS.map((t) => ({ ...t, onClick: () => selectTime(t) }));
  else if (step === 'result') chipOptions = [{ id: 'restart', label: '다시 추천 받기', onClick: restart }];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.navigate('Main')} hitSlop={10} style={{ padding: 4 }}>
          <ChevronLeft size={22} color={COLORS.ink} />
        </TouchableOpacity>
        <View style={styles.logoBadge}>
          <CareIcon size={18} />
        </View>
        <View>
          <Text style={styles.logo}>선·퀘</Text>
          <Text style={styles.subLogo}>AI 맞춤 추천</Text>
        </View>
      </View>

      <ScrollView ref={scrollRef} contentContainerStyle={styles.chatArea}>
        {messages.map((msg) => {
          if (msg.from === 'user') {
            return (
              <View key={msg.id} style={styles.userBubble}>
                <Text style={styles.userBubbleText}>{msg.text}</Text>
              </View>
            );
          }
          return (
            <View key={msg.id} style={styles.botRow}>
              <View style={styles.botAvatar}>
                <CareIcon size={14} color={COLORS.mint} />
              </View>
              <View style={{ gap: 10, minWidth: 0, flex: 1 }}>
                {msg.typing && (
                  <View style={styles.typingBubble}>
                    <TypingDot delay={0} />
                    <TypingDot delay={150} />
                    <TypingDot delay={300} />
                  </View>
                )}
                {!msg.typing && msg.text && (
                  <View style={styles.botBubble}>
                    <Text style={styles.botBubbleText}>{msg.text}</Text>
                  </View>
                )}
                {msg.quests && msg.quests.length > 0 && (
                  <View style={{ gap: 8 }}>
                    {msg.quests.map((q, i) => (
                      <View key={i} style={styles.questRecRow}>
                        <View style={styles.questRecIcon}>
                          <CareIcon size={17} color={COLORS.gold} />
                        </View>
                        <Text style={styles.questRecTitle} numberOfLines={1}>
                          {q.title}
                        </Text>
                        <TouchableOpacity style={styles.questRecButton} onPress={() => goToQuestDetail(q.title)}>
                          <Text style={styles.questRecButtonText}>상세보기</Text>
                        </TouchableOpacity>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            </View>
          );
        })}
      </ScrollView>

      {chipOptions.length > 0 && (
        <View style={styles.chipsRow}>
          {chipOptions.map((chip) => (
            <TouchableOpacity key={chip.id} style={styles.chip} onPress={chip.onClick}>
              <Text style={styles.chipText}>{chip.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          placeholder="메시지를 입력하세요"
          placeholderTextColor={COLORS.inkMuted48}
          value={inputText}
          onChangeText={setInputText}
          onSubmitEditing={sendFreeText}
        />
        <TouchableOpacity style={styles.sendButton} onPress={sendFreeText}>
          <Send size={19} color="#fff" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

