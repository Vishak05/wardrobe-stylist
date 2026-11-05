import axios from 'axios';

let apiBaseUrl = 'http://10.0.2.2:8000';
try {
  // attempt to read Expo constants if available; tolerate absence during npm install
  // using require so the module load doesn't fail when not installed
  // eslint-disable-next-line global-require
  const Constants = require('expo-constants').default;
  apiBaseUrl = Constants?.expoConfig?.extra?.apiBaseUrl || Constants?.manifest?.extra?.apiBaseUrl || apiBaseUrl;
} catch (e) {
  // expo-constants not available — fall back to default apiBaseUrl
}

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
});

// Worker-produced URLs are relative (/media/...); seeded ones are already absolute.
const resolveMediaUrl = (url) => (url && url.startsWith('/') ? `${apiBaseUrl}${url}` : url);

export { apiBaseUrl, resolveMediaUrl };
export default api;
