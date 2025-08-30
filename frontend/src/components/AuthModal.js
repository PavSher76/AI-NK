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

      // Проверяем токен через Gateway - используем защищенный endpoint
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
    setUsername('admin');
    setPassword('admin');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Авторизация</h2>
          <p className="text-gray-600">Войдите в систему для продолжения работы</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Логин
            </label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Введите логин"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Пароль
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Введите пароль"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div className="space-y-3">
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Вход...
                </>
              ) : (
                'Войти'
              )}
            </button>

            <button
              type="button"
              onClick={handleTestLogin}
              className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Заполнить тестовые данные (admin/admin)
            </button>
          </div>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-sm"
          >
            Отмена
          </button>
        </div>

        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Тестовые учетные данные:</h3>
          <div className="text-xs text-blue-800 space-y-1">
            <p><strong>Администратор:</strong> admin / admin</p>
            <p><strong>Пользователь:</strong> user / password123</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
