import { FormEvent, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { useAuth } from '../hooks/useAuth';
import './LoginPage.css';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated, loading } = useAuth();
  const [tenantId, setTenantId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated && !loading) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!tenantId || !email || !password) {
      setError('Preencha todos os campos para continuar.');
      return;
    }
    try {
      setSubmitting(true);
      await login(tenantId.trim(), email.trim(), password);
      navigate('/', { replace: true });
    } catch (err) {
      const detail = (err as Error).message ?? 'Falha ao autenticar.';
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="login-card card">
        <header>
          <h1>Entrar no SAFV</h1>
          <p>
            Informe o tenant e suas credenciais para acessar as simulações e
            dashboards.
          </p>
        </header>
        <form className="stack" onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="tenant">Tenant ID</label>
            <input
              id="tenant"
              value={tenantId}
              onChange={(event) => setTenantId(event.target.value)}
              placeholder="d4f6a9cf-..."
              autoComplete="off"
            />
            <small>Use o GUID do tenant provisionado no backend.</small>
          </div>
          <div className="form-field">
            <label htmlFor="email">E-mail</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="analista@empresa.com"
              autoComplete="username"
            />
          </div>
          <div className="form-field">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>
          {error && <div className="alert error">{error}</div>}
          <button className="button" type="submit" disabled={submitting}>
            {submitting ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
}
