import { Image, StyleSheet, Text, View } from 'react-native';

export default function WardrobeCard({ item }) {
  return (
    <View style={styles.card}>
      <Image source={{ uri: item.processed_image_url }} style={styles.image} />
      <View style={styles.body}>
        <Text style={styles.category}>{item.category || 'Unknown'}</Text>
        <Text style={styles.meta}>Color: {item.primary_color || 'N/A'}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '48%',
    marginBottom: 16,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#fff',
    borderColor: '#eee',
    borderWidth: 1,
  },
  image: {
    width: '100%',
    height: 140,
  },
  body: {
    padding: 10,
  },
  category: {
    fontWeight: '700',
    marginBottom: 4,
  },
  meta: {
    color: '#555',
  },
});
