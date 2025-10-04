import { createContext, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { REFRESH_THRESHOLD_MS } from '../api/config';
import { login as loginRequest, logout as logoutRequest, refresh as refreshRequest } from '../api/auth';
import type { AuthTokens } from '../api/auth';

interface AuthState {
  tenantId: string;
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

interface AuthContextValue {
  tenantId: string | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (tenantId: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const STORAGE_KEY = 'safv.auth.state';

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface Props {
  children: ReactNode;
}

export function AuthProvider({ children }: Props) {
  const [state, setState] = useState<AuthState | null>(null);
  const [loading, setLoading] = useState(true);
  const refreshTimer = useRef<number | null>(null);
  const refreshRef = useRef<() => Promise<void>>(async () => undefined);

  const persistState = useCallback((value: AuthState | null) => {
    if (value) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as AuthState;
        if (parsed.expiresAt > Date.now()) {
          setState(parsed);
        } else {
          sessionStorage.removeItem(STORAGE_KEY);
        }
      } catch {
        sessionStorage.removeItem(STORAGE_KEY);
      }
    }
    setLoading(false);
  }, []);

  const scheduleRefresh = useCallback((authState: AuthState | null) => {
    if (refreshTimer.current) {
      window.clearTimeout(refreshTimer.current);
    }
    if (!authState) {
      refreshTimer.current = null;
      return;
    }
    const delay = authState.expiresAt - Date.now() - REFRESH_THRESHOLD_MS;
    const invokeRefresh = () => {
      void refreshRef.current();
    };
    if (delay <= 0) {
      invokeRefresh();
      return;
    }
    refreshTimer.current = window.setTimeout(invokeRefresh, delay);
  }, []);

  useEffect(() => {
    return () => {
      if (refreshTimer.current) {
        window.clearTimeout(refreshTimer.current);
      }
    };
  }, []);

  const updateState = useCallback(
    (tenantId: string, tokens: AuthTokens, refreshTokenOverride?: string) => {
      const refreshToken = refreshTokenOverride ?? tokens.refreshToken;
      const authState: AuthState = {
        tenantId,
        accessToken: tokens.accessToken,
        refreshToken,
        expiresAt: Date.now() + tokens.expiresIn * 1000,
      };
      setState(authState);
      persistState(authState);
      scheduleRefresh(authState);
    },
    [persistState, scheduleRefresh],
  );

  const login = useCallback(
    async (tenantId: string, email: string, password: string) => {
      const tokens = await loginRequest(tenantId, { email, password });
      updateState(tenantId, tokens);
    },
    [updateState],
  );

  const logout = useCallback(async () => {
    if (state) {
      try {
        await logoutRequest(state.tenantId, state.refreshToken);
      } catch (error) {
        console.warn('Logout request failed', error);
      }
    }
    setState(null);
    persistState(null);
    scheduleRefresh(null);
  }, [state, persistState, scheduleRefresh]);

  const refresh = useCallback(async () => {
    if (!state) {
      return;
    }
    try {
      const tokens = await refreshRequest(state.tenantId, state.refreshToken);
      updateState(state.tenantId, tokens, state.refreshToken);
    } catch (error) {
      console.error('Failed to refresh token', error);
      await logout();
    }
  }, [state, updateState, logout]);

  useEffect(() => {
    refreshRef.current = refresh;
  }, [refresh]);

  useEffect(() => {
    scheduleRefresh(state);
  }, [state, scheduleRefresh]);

  const value = useMemo<AuthContextValue>(
    () => ({
      tenantId: state?.tenantId ?? null,
      accessToken: state?.accessToken ?? null,
      isAuthenticated: !!state && state.expiresAt > Date.now(),
      loading,
      login,
      logout,
      refresh,
    }),
    [state, loading, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
