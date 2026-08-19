import { useState } from 'react';
import { ActivityIndicator, Button, FlatList, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import api from '../api';
import WardrobeCard from '../components/WardrobeCard';

export default function DigitalClosetScreen({ userId }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Enter a user ID and fetch completed wardrobe items.');

  const fetchItems = async () => {
    if (!userId) {
      setStatusMessage('User ID is required.');
      return;
    }
    setLoading(true);
    setStatusMessage('Loading completed items...');
    try {
      const response = await api.get('/wardrobe/completed', { params: { user_id: userId } });
      setItems(response.data.map((item) => ({ ...item, processed_image_url: `${api.defaults.baseURL}${item.processed_image_url}` })));
      setStatusMessage(`Loaded ${response.data.length} completed items.`);
    } catch (error) {
      console.error(error);
      setStatusMessage('Failed to load wardrobe. Confirm the backend and user ID.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Digital Wardrobe</Text>
        <Text style={styles.subtitle}>Browse completed wardrobe items with processed images.</Text>
        <Button title="Refresh Closet" onPress={fetchItems} disabled={loading} />
        <Text style={styles.statusText}>{statusMessage}</Text>
        {loading ? (
          <ActivityIndicator style={styles.spinner} />
        ) : (
          <FlatList
            data={items}
            keyExtractor={(item) => item.item_id}
            numColumns={2}
            columnWrapperStyle={styles.row}
            renderItem={({ item }) => <WardrobeCard item={item} />}
          />
        )}
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
  statusText: {
    marginVertical: 12,
    color: '#333',
  },
  spinner: {
    marginVertical: 16,
  },
  row: {
    justifyContent: 'space-between',
  },
});
