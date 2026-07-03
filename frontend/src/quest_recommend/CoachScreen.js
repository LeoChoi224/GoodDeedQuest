import React, { useState } from 'react';
import { StyleSheet, Text, View, ScrollView, TextInput, TouchableOpacity, ActivityIndicator } from 'react-native';
import api from '../common/api';
import { MessageSquare, Send, BookOpen } from 'lucide-react-native';

export default function CoachScreen() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  const handleSend = async () => {
    if (!question.trim()) return;

    const userMsg = question;
    setChatHistory((prev) => [...prev, { role: 'user', content: userMsg }]);
    setQuestion('');
    setLoading(true);

    try {
      // AI 코치 통합 API 엔드포인트 호출 (/quest-recommend/coach)
      const res = await api.post('/quest-recommend/coach', { question: userMsg });
      if (res.success) {
        setChatHistory((prev) => [
          ...prev,
          { role: 'assistant', content: res.data.answer, sources: res.data.sources },
        ]);
      }
    } catch (err) {
      console.error(err);
      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', content: 'AI 코치가 답변 중 에러를 발생시켰습니다.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <MessageSquare size={20} color="#10b981" />
        <Text style={styles.headerTitle}> AI 선행 코치 (추천 통합)</Text>
      </View>
      <Text style={styles.subtitle}>
        봉사 혜택, 기부 연계, 안전 가이드라인 등에 대해 무엇이든 질문하세요.
      </Text>

      <ScrollView style={styles.chatArea} contentContainerStyle={styles.chatContent}>
        {chatHistory.map((chat, idx) => (
          <View
            key={idx}
            style={[
              styles.bubble,
              chat.role === 'user' ? styles.userBubble : styles.assistantBubble,
            ]}
          >
            <Text style={styles.bubbleText}>{chat.content}</Text>
            {chat.sources && chat.sources.length > 0 && (
              <View style={styles.sourcesBox}>
                <View style={styles.sourcesHeader}>
                  <BookOpen size={10} color="#6b7280" />
                  <Text style={styles.sourcesHeaderTitle}>참고 출처</Text>
                </View>
                {chat.sources.map((src, sIdx) => (
                  <Text key={sIdx} style={styles.sourceText}>
                    • {src}
                  </Text>
                ))}
              </View>
            )}
          </View>
        ))}
        {loading && (
          <View style={[styles.bubble, styles.assistantBubble]}>
            <ActivityIndicator size="small" color="#10b981" />
          </View>
        )}
      </ScrollView>

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          placeholder="질문 내용을 입력해 주세요."
          placeholderTextColor="#6b7280"
          value={question}
          onChangeText={setQuestion}
          onSubmitEditing={handleSend}
        />
        <TouchableOpacity style={styles.sendBtn} onPress={handleSend}>
          <Send size={18} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b0f19',
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 15,
  },
  chatArea: {
    flex: 1,
    marginBottom: 15,
  },
  chatContent: {
    gap: 15,
  },
  bubble: {
    padding: 12,
    borderRadius: 12,
    maxWidth: '85%',
  },
  userBubble: {
    backgroundColor: 'rgba(99, 102, 241, 0.15)',
    alignSelf: 'flex-end',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.3)',
  },
  assistantBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: '#10b981',
  },
  bubbleText: {
    color: '#fff',
    fontSize: 14,
    lineHeight: 20,
  },
  sourcesBox: {
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
    marginTop: 8,
    paddingTop: 8,
  },
  sourcesHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 4,
  },
  sourcesHeaderTitle: {
    fontSize: 10,
    color: '#9ca3af',
    fontWeight: 'bold',
  },
  sourceText: {
    fontSize: 10,
    color: '#6b7280',
    lineHeight: 14,
  },
  inputRow: {
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
  },
  input: {
    flex: 1,
    backgroundColor: '#161d30',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 12,
    padding: 12,
    color: '#fff',
    fontSize: 14,
  },
  sendBtn: {
    backgroundColor: '#10b981',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
