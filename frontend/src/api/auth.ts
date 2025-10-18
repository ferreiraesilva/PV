import { apiFetch } from './http';
import type { TokenPairResponse, TokenRefreshResponse } from './types';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

const mapTokenPair = (payload: TokenPairResponse): AuthTokens => ({
  accessToken: payload.access_token,
  refreshToken: payload.refresh_token,
  expiresIn: payload.expires_in,
});

export async function login(payload: LoginPayload): Promise<AuthTokens> {
  const response = await apiFetch<TokenPairResponse>('/login', {
    method: 'POST',
    body: payload,
  });
  return mapTokenPair(response);
}

export async function refresh(
  tenantId: string,
  refreshToken: string
): Promise<AuthTokens> {
  const response = await apiFetch<TokenRefreshResponse>(
    `/t/${encodeURIComponent(tenantId)}/refresh`,
    {
      method: 'POST',
      body: { refreshToken },
    }
  );
  return {
    accessToken: response.access_token,
    refreshToken,
    expiresIn: response.expires_in,
  };
}

export async function logout(
  tenantId: string,
  refreshToken: string
): Promise<void> {
  await apiFetch(`/t/${encodeURIComponent(tenantId)}/logout`, {
    method: 'POST',
    body: { refreshToken },
  });
}
