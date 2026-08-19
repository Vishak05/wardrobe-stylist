import axios from 'axios';

let apiBaseUrl = 'http://10.0.2.2:8000';
try {
  // attempt to read Expo constants if available; tolerate absence during npm install
  // using require so the module load doesn't fail when not installed
  // eslint-disable-next-line global-require
  const Constants = require('expo-constants');
  apiBaseUrl = Constants?.expoConfig?.extra?.apiBaseUrl || Constants?.manifest?.extra?.apiBaseUrl || apiBaseUrl;
} catch (e) {
  // expo-constants not available — fall back to default apiBaseUrl
}

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
});

export { apiBaseUrl };
export default api;
