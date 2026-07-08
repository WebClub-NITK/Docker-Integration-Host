import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import NetworkDashboard from './pages/networks/NetworkDashboard';
import NetworkDetail from './pages/networks/NetworkDetail';
import PrivateRoute from './components/PrivateRoute';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={
          <PrivateRoute><DashboardPage /></PrivateRoute>
        } />
        <Route path="/hosts/:hostId/networks" element={<PrivateRoute><NetworkDashboard /></PrivateRoute>} />
        <Route path="/hosts/:hostId/networks/:networkId" element={<PrivateRoute><NetworkDetail /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}