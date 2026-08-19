import { useState } from 'react';
import { ActivityIndicator, Alert, Button, FlatList, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import api from '../api';
import WardrobeCard from '../components/WardrobeCard';

export default function AIStylistScreen({ userId }) {
  const [query, setQuery] = useState('Create an outfit for a casual brunch.');
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Ask the AI stylist to create an outfit.');
  const [selection, setSelection] = useState(null);

  const runStylist = async () => {
    if (!userId) {
      Alert.alert('User ID required', 'Enter a user ID to request outfit recommendations.');
      return;
    }
    setLoading(true);
    setStatusMessage('Requesting outfit recommendation...');
    try {
      const response = await api.post('/recommendations', { user_id: userId, query });
      const imageUrls = Object.entries(response.data.image_urls).map(([item_id, uri]) => ({ item_id, uri }));
      setSelection({ styling_notes: response.data.styling_notes, imageUrls });
      setStatusMessage('Outfit recommendation received.');
    } catch (error) {
      console.error(error);
      setStatusMessage('Failed to get recommendation. Check backend and wardrobe items.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>AI Stylist</Text>
        <Text style={styles.subtitle}>Ask for outfit recommendations from your closet.</Text>
        <TextInput
          style={[styles.input, styles.queryInput]}
          value={query}
          onChangeText={setQuery}
          placeholder="Describe the look you want..."
          multiline
        />
        <Button title="Get Outfit" onPress={runStylist} disabled={loading} />
        <Text style={styles.statusText}>{statusMessage}</Text>
        {loading && <ActivityIndicator style={styles.spinner} />}
        {selection ? (
          <View style={styles.resultBox}>
            <Text style={styles.resultTitle}>Styling Notes</Text>
            <Text style={styles.resultText}>{selection.styling_notes}</Text>
            <FlatList
              data={selection.imageUrls}
              keyExtractor={(item) => item.item_id}
              numColumns={2}
              columnWrapperStyle={styles.row}
              renderItem={({ item }) => <WardrobeCard item={{ item_id: item.item_id, processed_image_url: item.uri }} />}
            />
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
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
  statusText: {
    marginVertical: 12,
    color: '#333',
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
  resultText: {
    color: '#333',
    marginBottom: 12,
  },
  spinner: {
    marginVertical: 16,
  },
  row: {
    justifyContent: 'space-between',
  },
});
