import { API_BASE_URL } from './config';

export interface ApiError extends Error {
  status?: number;
  body?: unknown;
}

interface ApiFetchOptions extends RequestInit {
  token?: string | null;
}

const isJsonLike = (
  body: unknown
): body is Record<string, unknown> | unknown[] => {
  return (
    typeof body === 'object' &&
    body !== null &&
    !(body instanceof FormData) &&
    !(body instanceof Blob) &&
    !(body instanceof ArrayBuffer)
  );
};

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { token, headers, body, ...rest } = options;
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;

  const finalHeaders = new Headers(headers ?? {});
  if (token) {
    finalHeaders.set('Authorization', `Bearer ${token}`);
  }
  if (
    body !== undefined &&
    isJsonLike(body) &&
    !finalHeaders.has('Content-Type')
  ) {
    finalHeaders.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...rest,
    body:
      body && isJsonLike(body)
        ? JSON.stringify(body)
        : (body as BodyInit | null | undefined),
    headers: finalHeaders,
  });

  if (!response.ok) {
    let errorBody: unknown = undefined;
    try {
      errorBody = await response.json();
    } catch {
      try {
        errorBody = await response.text();
      } catch {
        errorBody = undefined;
      }
    }
    const error: ApiError = new Error(
      ((errorBody as Record<string, unknown>)?.detail as string) ??
        `Request failed with status ${response.status}`
    );
    error.status = response.status;
    error.body = errorBody;
    throw error;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type');
  if (contentType?.includes('application/json')) {
    return (await response.json()) as T;
  }
  if (contentType?.includes('text/')) {
    return (await response.text()) as unknown as T;
  }
  return (await response.blob()) as unknown as T;
}
