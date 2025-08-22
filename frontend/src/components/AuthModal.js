import React, { useState } from 'react';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

const AuthModal = ({ isOpen, onClose, onAuthSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Keycloak configuration
  const KEYCLOAK_URL = 'https://localhost:8081';
  const REALM = 'ai-nk';
  const CLIENT_ID = 'ai-nk-frontend';

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!username.trim() || !password.trim()) {
      setError('Введите логин и пароль');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Получаем токен через Keycloak
      const tokenResponse = await fetch(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'password',
          client_id: CLIENT_ID,
          username: username,
          password: password,
        }),
      });

      if (!tokenResponse.ok) {
        const errorData = await tokenResponse.json();
        throw new Error(errorData.error_description || 'Ошибка авторизации');
      }

      const tokenData = await tokenResponse.json();
      const accessToken = tokenData.access_token;

      // Проверяем токен через Gateway
      const gatewayResponse = await fetch('/api/documents', {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (gatewayResponse.ok) {
        // Сохраняем информацию о пользователе
        const userInfo = {
          token: accessToken,
          username: username,
          method: 'keycloak',
          expiresAt: Date.now() + (tokenData.expires_in * 1000)
        };
        
        onAuthSuccess(userInfo, 'keycloak');
        onClose();
      } else {
        throw new Error('Ошибка проверки токена в Gateway');
      }
    } catch (error) {
      console.error('Login error:', error);
      setError(error.message || 'Ошибка авторизации');
    } finally {
      setLoading(false);
    }
  };

  const handleTestLogin = () => {
    setUsername('testuser');
    setPassword('password123');
  };

  const handleDemoMode = () => {
    // Демо режим без реальной авторизации
    const demoUser = {
      token: 'demo-token',
      username: 'demo-user',
      method: 'demo',
      expiresAt: Date.now() + (3600 * 1000) // 1 час
    };
    onAuthSuccess(demoUser, 'demo');
    onClose();
  };

  const handleTestTokenMode = () => {
    // Тестовый режим с простым токеном
    const testUser = {
      token: 'test-token',
      username: 'test-user',
      method: 'test',
      expiresAt: Date.now() + (3600 * 1000) // 1 час
    };
    onAuthSuccess(testUser, 'test');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <img 
              src="/logo.png" 
              alt="AI-НК Logo" 
              className="w-8 h-8 object-contain"
            />
            <h2 className="text-xl font-bold text-gray-900">Авторизация</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Логин
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Введите логин..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Пароль
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Введите пароль..."
                className="w-full p-3 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                disabled={loading}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex space-x-2">
            <button
              type="button"
              onClick={handleTestLogin}
              className="flex-1 py-2 px-4 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              disabled={loading}
            >
              Тестовые данные
            </button>
            <button
              type="submit"
              className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Вход...
                </>
              ) : (
                'Войти'
              )}
            </button>
          </div>
        </form>

        <div className="mt-6 space-y-3">
          <button
            onClick={handleTestTokenMode}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            disabled={loading}
          >
            Тестовый токен
          </button>
          
          <button
            onClick={handleDemoMode}
            className="w-full py-2 px-4 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
            disabled={loading}
          >
            Демо режим
          </button>

          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">
              <strong>Информация:</strong><br />
              • Тестовые данные: testuser / password123<br />
              • Тестовый токен: простой доступ с test-token<br />
              • Демо режим: доступ с demo-token<br />
              • Данные сохраняются в localStorage
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
