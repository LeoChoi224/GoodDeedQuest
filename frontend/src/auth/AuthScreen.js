import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, Alert } from 'react-native';
import api, { setAuthToken } from '../common/api';

export default function AuthScreen() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [msg, setMsg] = useState('');

  const handleSubmit = async () => {
    if (!email || !password || (!isLogin && !name)) {
      Alert.alert('오류', '모든 필드를 입력해 주세요.');
      return;
    }
    setMsg('');
    try {
      if (isLogin) {
        const res = await api.post('/auth/login', { email, password });
        if (res.success) {
          setAuthToken(res.data.access_token);
          setMsg('로그인 성공! 환영합니다.');
        }
      } else {
        const res = await api.post('/auth/register', { email, password, name });
        if (res.success) {
          setMsg('회원가입 성공! 로그인 해주세요.');
          setIsLogin(true);
        }
      }
    } catch (err) {
      setMsg(err.response?.data?.detail || '오류가 발생했습니다.');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>{isLogin ? '🔑 로그인' : '🌱 회원가입'}</Text>
        
        {!isLogin && (
          <TextInput
            style={styles.input}
            placeholder="이름 입력"
            placeholderTextColor="#6b7280"
            value={name}
            onChangeText={setName}
          />
        )}
        <TextInput
          style={styles.input}
          placeholder="이메일 입력"
          placeholderTextColor="#6b7280"
          keyboardType="email-address"
          autoCapitalize="none"
          value={email}
          onChangeText={setEmail}
        />
        <TextInput
          style={styles.input}
          placeholder="비밀번호 입력"
          placeholderTextColor="#6b7280"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        <TouchableOpacity style={styles.button} onPress={handleSubmit}>
          <Text style={styles.buttonText}>{isLogin ? '로그인' : '회원가입'}</Text>
        </TouchableOpacity>

        {msg ? <Text style={styles.message}>{msg}</Text> : null}

        <TouchableOpacity onPress={() => setIsLogin(!isLogin)} style={styles.toggleContainer}>
          <Text style={styles.toggleText}>
            {isLogin ? '계정이 없으신가요? 회원가입' : '이미 계정이 있으신가요? 로그인'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b0f19',
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#f3f4f6',
    textAlign: 'center',
    marginBottom: 20,
  },
  input: {
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    marginBottom: 15,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#10b981',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  message: {
    color: '#f59e0b',
    textAlign: 'center',
    marginTop: 15,
    fontSize: 14,
  },
  toggleContainer: {
    marginTop: 20,
    alignItems: 'center',
  },
  toggleText: {
    color: '#10b981',
    textDecorationLine: 'underline',
    fontSize: 14,
  },
});
