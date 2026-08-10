import Constants from 'expo-constants';
import axios from 'axios';

export const apiBaseUrl =
  Constants.expoConfig?.extra?.apiBaseUrl ||
  Constants.manifest?.extra?.apiBaseUrl ||
  'http://10.0.2.2:8000';

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
});

export default api;
