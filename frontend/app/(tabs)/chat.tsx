import React, { useState, useEffect } from 'react';
import { View, Text, Button, StyleSheet, TouchableOpacity, ActivityIndicator, FlatList } from 'react-native';
import { Audio } from 'expo-av';
import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import { Ionicons } from '@expo/vector-icons';

const Chat = () => {
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<Array<{ type: 'user' | 'bot'; text?: string; audioUri?: string }>>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Function to start recording
  const startRecording = async () => {
    try {
      console.log('Requesting permissions...');
      const permission = await Audio.requestPermissionsAsync();

      if (permission.status !== 'granted') {
        alert('Permission to access microphone is required!');
        return;
      }

      console.log('Starting recording...');
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const newRecording = new Audio.Recording();
      await newRecording.prepareToRecordAsync(
        Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
      );
      await newRecording.startAsync();

      setRecording(newRecording);
      setIsRecording(true);
      console.log('Recording started');
    } catch (err) {
      console.error('Failed to start recording', err);
    }
  };

  // Function to stop recording
  const stopRecording = async () => {
    console.log('Stopping recording...');
    if (!recording) return;

    setIsRecording(false);
    await recording.stopAndUnloadAsync();

    const uri = recording.getURI();
    console.log('Recording stopped and stored at', uri);

    setRecording(null);

    if (uri) {
      // Add user's message to the chat
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: 'user', audioUri: uri },
      ]);

      // Send audio to backend
      await sendAudioToBackend(uri);
    }
  };

  // Function to send audio to backend
  const sendAudioToBackend = async (audioUri: string) => {
    try {
      setIsProcessing(true);
      const fileInfo = await FileSystem.getInfoAsync(audioUri);
      const fileUri = fileInfo.uri;
      const formData = new FormData();

      formData.append('file', {
        uri: fileUri,
        name: 'audio.m4a',
        type: 'audio/m4a',
      } as any);

      console.log('Sending audio to backend...');

      const response = await axios.post('http://your-backend-server-url/process_audio', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { text_response, audio_response_url } = response.data;

      // Add bot's message to the chat
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: 'bot', text: text_response, audioUri: audio_response_url },
      ]);

      setIsProcessing(false);
    } catch (error) {
      console.error('Error sending audio to backend', error);
      setIsProcessing(false);
    }
  };

  // Function to play audio messages
  const playAudio = async (audioUri: string) => {
    try {
      const { sound } = await Audio.Sound.createAsync({ uri: audioUri });
      await sound.playAsync();
    } catch (error) {
      console.error('Error playing audio', error);
    }
  };

  // Render a single message item
  const renderMessageItem = ({ item }: { item: { type: 'user' | 'bot'; text?: string; audioUri?: string } }) => {
    return (
      <View
        style={[
          styles.messageContainer,
          item.type === 'user' ? styles.userMessage : styles.botMessage,
        ]}
      >
        {item.text && <Text style={styles.messageText}>{item.text}</Text>}
        {item.audioUri && (
          <TouchableOpacity onPress={() => playAudio(item.audioUri)}>
            <Ionicons name="play-circle-outline" size={32} color="blue" />
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Messages List */}
      <FlatList
        data={messages}
        renderItem={renderMessageItem}
        keyExtractor={(_, index) => index.toString()}
        style={styles.chatList}
      />

      {/* Processing Indicator */}
      {isProcessing && (
        <ActivityIndicator size="large" color="#0000ff" />
      )}

      {/* Record Button */}
      <TouchableOpacity
        style={styles.recordButton}
        onPress={isRecording ? stopRecording : startRecording}
      >
        <Ionicons
          name={isRecording ? 'stop-circle' : 'mic-circle'}
          size={64}
          color={isRecording ? 'red' : 'green'}
        />
      </TouchableOpacity>
    </View>
  );
};

export default Chat;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  chatList: {
    flex: 1,
    padding: 10,
  },
  messageContainer: {
    marginVertical: 5,
    padding: 10,
    borderRadius: 10,
    maxWidth: '80%',
  },
  userMessage: {
    backgroundColor: '#dcf8c6',
    alignSelf: 'flex-end',
  },
  botMessage: {
    backgroundColor: '#ececec',
    alignSelf: 'flex-start',
  },
  messageText: {
    fontSize: 16,
  },
  recordButton: {
    alignSelf: 'center',
    marginBottom: 20,
  },
});
