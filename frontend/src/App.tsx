import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from '@/layouts/MainLayout';
import Home from '@/pages/Home';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import Stocks from '@/pages/Stocks';
import StockDetail from '@/pages/StockDetail';
import Factors from '@/pages/Factors';
import FactorDetail from '@/pages/FactorDetail';
import Strategies from '@/pages/Strategies';
import StrategyDetail from '@/pages/StrategyDetail';
import Sandbox from '@/pages/Sandbox';
import SandboxDetail from '@/pages/SandboxDetail';
import { useAuthStore } from '@/stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Home />} />
            <Route path="stocks" element={<Stocks />} />
            <Route path="stocks/:code" element={<StockDetail />} />
            <Route path="factors" element={<Factors />} />
            <Route path="factors/:id" element={<FactorDetail />} />
            <Route path="strategies" element={<Strategies />} />
            <Route path="strategies/:id" element={<StrategyDetail />} />
            <Route path="sandbox" element={<Sandbox />} />
            <Route path="sandbox/:id" element={<SandboxDetail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
