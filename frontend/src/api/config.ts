const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/v1';

export const API_BASE_URL = rawBaseUrl.replace(/\/$/, '');

export const REFRESH_THRESHOLD_MS = 30_000;
