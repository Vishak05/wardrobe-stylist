import 'dotenv/config';

export default ({ config }) => ({
  ...config,
  extra: {
    apiBaseUrl:
      process.env.EXPO_PUBLIC_API_BASE_URL ||
      process.env.API_BASE_URL ||
      config.extra?.apiBaseUrl ||
      'http://10.0.2.2:8000',
  },
});
