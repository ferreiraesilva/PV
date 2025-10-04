import { Navigate, Outlet, Route, Routes } from 'react-router-dom';

import { AppLayout } from './components/AppLayout';
import { LoadingScreen } from './components/LoadingScreen';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import SimulationsPage from './pages/SimulationsPage';
import ValuationsPage from './pages/ValuationsPage';
import BenchmarkingPage from './pages/BenchmarkingPage';
import RecommendationsPage from './pages/RecommendationsPage';
import AuditPage from './pages/AuditPage';
import { AuthProvider } from './providers/AuthProvider';
import { useAuth } from './hooks/useAuth';

function ProtectedOutlet() {
  const { isAuthenticated, loading, logout } = useAuth();

  if (loading) {
    return <LoadingScreen message="Validação de sessão" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <AppLayout onLogout={logout}>
      <Outlet />
    </AppLayout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedOutlet />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/simulations" element={<SimulationsPage />} />
          <Route path="/valuations" element={<ValuationsPage />} />
          <Route path="/benchmarking" element={<BenchmarkingPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
