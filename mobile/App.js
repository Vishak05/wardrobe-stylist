import React, { useState } from 'react';
import { SafeAreaView, View, TextInput, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import IngestionScreen from './src/screens/IngestionScreen';
import DigitalClosetScreen from './src/screens/DigitalClosetScreen';
import AIStylistScreen from './src/screens/AIStylistScreen';

const Tab = createBottomTabNavigator();

// Local screen implementations removed; using modular screen components in ./src/screens

export default function App() {
  const [userId, setUserId] = useState('00000000-0000-0000-0000-000000000001');

  return (
    <NavigationContainer>
      <SafeAreaView style={{ flex: 1 }}>
        <View style={styles.headerBar}>
          <TextInput
            style={styles.userInput}
            value={userId}
            onChangeText={setUserId}
            placeholder="User ID"
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>
        <Tab.Navigator>
          <Tab.Screen name="Ingestion">
            {() => <IngestionScreen userId={userId} />}
          </Tab.Screen>
          <Tab.Screen name="Closet">
            {() => <DigitalClosetScreen userId={userId} />}
          </Tab.Screen>
          <Tab.Screen name="Stylist">
            {() => <AIStylistScreen userId={userId} />}
          </Tab.Screen>
        </Tab.Navigator>
      </SafeAreaView>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 28,
    marginBottom: 12,
    fontWeight: '700',
  },
  subtitle: {
    marginBottom: 18,
    color: '#555',
  },
  input: {
    height: 50,
    borderColor: '#ccc',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 14,
    marginBottom: 18,
  },
  queryInput: {
    minHeight: 100,
    textAlignVertical: 'top',
  },
  buttonGroup: {
    flexDirection: 'row',
    marginBottom: 18,
  },
  buttonSpacer: {
    width: 14,
  },
  preview: {
    width: '100%',
    height: 320,
    borderRadius: 12,
    marginBottom: 18,
  },
  placeholder: {
    width: '100%',
    height: 320,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#ddd',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
  },
  placeholderText: {
    color: '#888',
  },
  statusBox: {
    marginTop: 18,
    padding: 16,
    backgroundColor: '#f8f8ff',
    borderRadius: 10,
  },
  statusLabel: {
    fontWeight: '700',
    marginBottom: 8,
  },
  statusText: {
    color: '#333',
    marginTop: 12,
  },
  resultBox: {
    marginTop: 22,
    padding: 16,
    backgroundColor: '#f1fdf5',
    borderRadius: 10,
  },
  resultTitle: {
    fontWeight: '700',
    marginBottom: 10,
  },
  resultImage: {
    width: '100%',
    height: 240,
    borderRadius: 12,
    marginBottom: 12,
  },
  resultText: {
    marginBottom: 6,
  },
  spinner: {
    marginVertical: 16,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  card: {
    width: '48%',
    marginBottom: 16,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#fff',
    borderColor: '#eee',
    borderWidth: 1,
  },
  cardImage: {
    width: '100%',
    height: 140,
  },
  cardLabel: {
    fontWeight: '700',
    padding: 10,
  },
  cardMeta: {
    paddingHorizontal: 10,
    paddingBottom: 8,
    color: '#555',
  },
  headerBar: {
    padding: 14,
    backgroundColor: '#f9fafb',
  },
  userInput: {
    height: 44,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 10,
    paddingHorizontal: 12,
    backgroundColor: '#fff',
  },
});
