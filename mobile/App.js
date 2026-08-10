  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Wardrobe Ingestion</Text>
        <Text style={styles.subtitle}>API Host: {getApiHostHint()}</Text>
        <TextInput
          style={styles.input}
          value={userId}
          onChangeText={setUserId}
          placeholder="User ID"
          autoCapitalize="none"
          autoCorrect={false}
        />

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

function DigitalClosetScreen({ userId }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Enter a user ID and fetch completed wardrobe items.');

  const fetchItems = async () => {
    if (!userId) {
      Alert.alert('User ID required', 'Enter a user ID to load the digital closet.');
      return;
    }
    setLoading(true);
    setStatusMessage('Loading completed items...');
    try {
      const response = await api.get(`/wardrobe/completed`, { params: { user_id: userId } });
      setItems(response.data);
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
        <Text style={styles.subtitle}>Completed items are displayed with processed images.</Text>
        <Button title="Refresh Closet" onPress={fetchItems} disabled={loading} />
        <Text style={styles.statusText}>{statusMessage}</Text>

        <View style={styles.grid}>
          {items.map((item) => (
            <View key={item.item_id} style={styles.card}>
              <Image source={{ uri: `${apiBaseUrl}${item.processed_image_url}` }} style={styles.cardImage} />
              <Text style={styles.cardLabel}>{item.category || 'Unknown'}</Text>
              <Text style={styles.cardMeta}>Color: {item.primary_color || 'N/A'}</Text>
              <Text style={styles.cardMeta}>{item.sub_category || 'No subtype'}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function AIStylistScreen({ userId }) {
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
      setSelection(response.data);
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

        {selection ? (
          <View style={styles.resultBox}>
            <Text style={styles.resultTitle}>Styling Notes</Text>
            <Text style={styles.resultText}>{selection.styling_notes}</Text>
            <View style={styles.grid}>
              {Object.entries(selection.image_urls).map(([itemId, imageUrl]) => (
                <View key={itemId} style={styles.card}>
                  <Image source={{ uri: imageUrl }} style={styles.cardImage} />
                  <Text style={styles.cardLabel}>{itemId}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

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
