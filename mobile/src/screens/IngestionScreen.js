import { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Button, Image, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import api from '../api';
import { apiBaseUrl } from '../api';

export default function IngestionScreen({ userId }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Select or capture a photo to begin ingestion.');
  const [itemData, setItemData] = useState(null);

  useEffect(() => {
    requestPermissions();
  }, []);

  const requestPermissions = async () => {
    const mediaResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    const cameraResult = await ImagePicker.requestCameraPermissionsAsync();

    if (!mediaResult.granted || !cameraResult.granted) {
      Alert.alert('Permissions required', 'Camera and media library permissions are required for wardrobe ingestion.');
    }
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!result.canceled) {
      setSelectedImage(result.assets[0]);
      setStatusMessage('Image selected. Ready to upload.');
      setItemData(null);
    }
  };

  const takePhoto = async () => {
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!result.canceled) {
      setSelectedImage(result.assets[0]);
      setStatusMessage('Photo captured. Ready to upload.');
      setItemData(null);
    }
  };

  const buildFormData = () => {
    const uri = selectedImage.uri;
    const filename = uri.split('/').pop();
    const match = filename.match(/\.(\w+)$/);
    const type = match ? `image/${match[1].toLowerCase()}` : 'image/jpeg';

    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('image', {
      uri,
      name: filename,
      type,
    });
    return formData;
  };

  const uploadImage = async () => {
    if (!selectedImage) {
      Alert.alert('No image selected', 'Please select or capture an image first.');
      return;
    }
    setUploading(true);
    setStatusMessage('Uploading image...');

    try {
      const response = await api.post('/wardrobe/ingest', buildFormData(), {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setStatusMessage('Ingestion request accepted. Polling status...');
      await pollItemStatus(response.data.item_id);
    } catch (error) {
      console.error(error);
      Alert.alert('Upload failed', 'Unable to send image to the wardrobe backend.');
      setStatusMessage('Upload failed. Check network and API configuration.');
    } finally {
      setUploading(false);
    }
  };

  const pollItemStatus = async (id) => {
    const maxAttempts = 20;
    let attempt = 0;

    while (attempt < maxAttempts) {
      attempt += 1;
      await new Promise((resolve) => setTimeout(resolve, 3000));
      try {
        const response = await api.get(`/wardrobe/${id}`);
        setItemData(response.data);
        setStatusMessage(`Current status: ${response.data.status}`);
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          return;
        }
      } catch (error) {
        console.error(error);
        setStatusMessage('Polling failed. Will retry...');
      }
    }

    setStatusMessage('Polling timed out. Please check the backend and try again.');
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Wardrobe Ingestion</Text>
        <Text style={styles.subtitle}>API Host: {apiBaseUrl}</Text>
        <View style={styles.buttonGroup}>
          <Button title="Pick from Library" onPress={pickImage} />
          <View style={styles.buttonSpacer} />
          <Button title="Take Photo" onPress={takePhoto} />
        </View>

        {selectedImage ? (
          <Image source={{ uri: selectedImage.uri }} style={styles.preview} />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>No image selected</Text>
          </View>
        )}

        <Button title="Upload & Process" onPress={uploadImage} disabled={uploading || !selectedImage} />
        {uploading && <ActivityIndicator style={styles.spinner} />}

        <View style={styles.statusBox}>
          <Text style={styles.statusLabel}>Status</Text>
          <Text style={styles.statusText}>{statusMessage}</Text>
        </View>

        {itemData && itemData.processed_image_url ? (
          <View style={styles.resultBox}>
            <Text style={styles.resultTitle}>Ingested Item</Text>
            <Image source={{ uri: `${apiBaseUrl}${itemData.processed_image_url}` }} style={styles.resultImage} />
            <Text style={styles.resultText}>Category: {itemData.category || 'N/A'}</Text>
            <Text style={styles.resultText}>Primary color: {itemData.primary_color || 'N/A'}</Text>
            <Text style={styles.resultText}>Status: {itemData.status}</Text>
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
});
