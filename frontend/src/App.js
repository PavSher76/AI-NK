import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User, 
  Settings, 
  Zap, 
  Loader2,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  LogOut,
  Shield,
  BookOpen,
  Upload
} from 'lucide-react';

// Components
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import SettingsPanel from './components/SettingsPanel';
import AuthModal from './components/AuthModal';

// Pages
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import NormcontrolPage from './pages/NormcontrolPage';
import CalculationsPage from './pages/CalculationsPage';
import StructuralCalculationsPage from './pages/StructuralCalculationsPage';
import DocumentsPage from './pages/DocumentsPage';

function App() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState('');
  const [authMethod, setAuthMethod] = useState('');
  const [userInfo, setUserInfo] = useState(null);
  const [currentPage, setCurrentPage] = useState('dashboard'); // 'dashboard', 'chat', 'normcontrol', 'documents'
  const [systemStatus, setSystemStatus] = useState({
    gateway: false,
    ollama: false,
    keycloak: false
  });
  const [refreshTabs, setRefreshTabs] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Отладочные логи для отслеживания изменений состояния
  useEffect(() => {
    console.log('🔍 [DEBUG] App.js: currentPage changed to:', currentPage);
    // Закрываем боковое меню на мобильных устройствах при смене страницы
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false);
    }
  }, [currentPage]);

  useEffect(() => {
    console.log('🔍 [DEBUG] App.js: systemStatus updated:', systemStatus);
  }, [systemStatus]);

  useEffect(() => {
    console.log('🔍 [DEBUG] App.js: models updated:', models);
  }, [models]);

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

  // Проверка авторизации при загрузке
  useEffect(() => {
    const savedUserInfo = localStorage.getItem('userInfo');
    
    if (savedUserInfo) {
      try {
        const user = JSON.parse(savedUserInfo);
        const now = Date.now();
        
        // Проверяем, не истек ли токен
        if (user.expiresAt && user.expiresAt > now) {
          setUserInfo(user);
          setAuthToken(user.token);
          setAuthMethod(user.method);
          setIsAuthenticated(true);
        } else {
          // Токен истек, очищаем данные
          localStorage.removeItem('userInfo');
          setShowAuthModal(true);
        }
      } catch (error) {
        console.error('Error parsing saved user info:', error);
        localStorage.removeItem('userInfo');
        setShowAuthModal(true);
      }
    } else {
      setShowAuthModal(true);
    }
  }, []);

  // Проверка статуса сервисов
  const checkSystemStatus = async () => {
    console.log('🔍 [DEBUG] App.js: checkSystemStatus started');
    try {
      // Проверка Gateway (всегда доступен)
      try {
        const gatewayResponse = await axios.get('/api/documents');
        setSystemStatus(prev => ({ ...prev, gateway: true }));
      } catch (error) {
        // Gateway может требовать авторизации, но это нормально
        if (error.response && error.response.status === 401) {
          setSystemStatus(prev => ({ ...prev, gateway: true }));
        } else {
          setSystemStatus(prev => ({ ...prev, gateway: false }));
        }
      }

      // Проверка Ollama (через Gateway с авторизацией)
      try {
        if (isAuthenticated && authToken) {
          const ollamaResponse = await axios.get('/ollama/api/tags', {
            headers: { Authorization: `Bearer ${authToken}` }
          });
          setSystemStatus(prev => ({ ...prev, ollama: true }));
        } else {
          // Если не авторизован, проверяем через Gateway без токена
          // Gateway вернет 401, но это означает что сервис доступен
          try {
            const ollamaResponse = await axios.get('/ollama/api/tags');
            setSystemStatus(prev => ({ ...prev, ollama: true }));
          } catch (gatewayError) {
            if (gatewayError.response && gatewayError.response.status === 401) {
              // Gateway доступен, но требует авторизации - это нормально
              setSystemStatus(prev => ({ ...prev, ollama: true }));
            } else {
              setSystemStatus(prev => ({ ...prev, ollama: false }));
            }
          }
        }
      } catch (error) {
        setSystemStatus(prev => ({ ...prev, ollama: false }));
      }

      // Проверка Keycloak (всегда доступен)
      try {
        const keycloakResponse = await axios.get('/keycloak/realms/ai-nk');
        setSystemStatus(prev => ({ ...prev, keycloak: true }));
      } catch (error) {
        console.log('Keycloak realm not found yet');
        setSystemStatus(prev => ({ ...prev, keycloak: false }));
      }
    } catch (error) {
      console.error('🔍 [DEBUG] App.js: Error checking system status:', error);
      setSystemStatus({ gateway: false, ollama: false, keycloak: false });
    }
  };

  // Обработка успешной авторизации
  const handleAuthSuccess = (userInfo, method) => {
    console.log('🔍 [DEBUG] App.js: handleAuthSuccess called with:', { userInfo, method });
    console.log('🔍 [DEBUG] App.js: userInfo.token length:', userInfo.token?.length);
    console.log('🔍 [DEBUG] App.js: userInfo.token starts with:', userInfo.token?.substring(0, 20));
    
    setUserInfo(userInfo);
    setAuthToken(userInfo.token);
    setAuthMethod(method);
    setIsAuthenticated(true);
    setShowAuthModal(false);
    setError(null); // Очищаем ошибки при успешной авторизации
    
    // Сохраняем в localStorage
    localStorage.setItem('userInfo', JSON.stringify(userInfo));
    
    console.log('🔍 [DEBUG] App.js: Авторизация завершена, вызываем loadModels');
    console.log('🔍 [DEBUG] App.js: Состояние после установки:', { 
      isAuthenticated: true, 
      authToken: !!userInfo.token, 
      authMethod: method 
    });
    
    // Загружаем модели после авторизации
    loadModels();
    
    // Устанавливаем флаг для обновления данных вкладок
    setRefreshTabs(true);
  };

  // Выход из системы
  const handleLogout = () => {
    setUserInfo(null);
    setAuthToken('');
    setAuthMethod('');
    setIsAuthenticated(false);
    setModels([]);
    setSelectedModel('');
    setMessages([]);
    
    // Очищаем localStorage
    localStorage.removeItem('userInfo');
    
    // Показываем модальное окно авторизации
    setShowAuthModal(true);
  };

  // Загрузка моделей
  const loadModels = async () => {
    console.log('🔍 [DEBUG] App.js: loadModels started');
    console.log('🔍 [DEBUG] App.js: loadModels auth state:', { 
      isAuthenticated, 
      authToken: !!authToken, 
      authTokenLength: authToken?.length,
      authMethod,
      userInfo: !!userInfo
    });
    
    if (!isAuthenticated || !authToken) {
      console.log('loadModels: Не авторизован', { isAuthenticated, authToken: !!authToken });
      return;
    }

    try {
      console.log('loadModels: Загружаем модели...');
      console.log('loadModels: Метод авторизации:', authMethod);
      console.log('loadModels: Отправляем запрос к /ollama/api/tags с токеном:', authToken.substring(0, 20) + '...');
      
      const response = await axios.get('/ollama/api/tags', {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      console.log('loadModels: Получен ответ:', response.status, response.data);
      
      // Преобразуем формат данных из Ollama в формат, ожидаемый фронтендом
      const modelsData = response.data.models.map(model => ({
        id: model.name,
        name: model.name,
        size: model.size,
        modified_at: model.modified_at
      }));
      
      console.log('loadModels: Преобразованные данные:', modelsData);
      
      setModels(modelsData);
      if (modelsData.length > 0 && !selectedModel) {
        setSelectedModel(modelsData[0].id);
        console.log('loadModels: Установлена первая модель:', modelsData[0].id);
      }
      setError(null); // Очищаем ошибки при успешной загрузке
      console.log('loadModels: Модели загружены', modelsData.length);
    } catch (error) {
      console.error('🔍 [DEBUG] App.js: Error loading models:', error);
      console.error('🔍 [DEBUG] App.js: Error response:', error.response?.data);
      console.error('🔍 [DEBUG] App.js: Error status:', error.response?.status);
      setError('Ошибка загрузки моделей');
    }
  };

  // Отправка сообщения
  const sendMessage = async (content) => {
    if (!content.trim() || !selectedModel) return;
    if (!isAuthenticated || !authToken) {
      console.log('sendMessage: Не авторизован', { isAuthenticated, authToken: !!authToken });
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: content,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(`/ollama/api/generate`, {
        model: selectedModel,
        prompt: content,
        stream: false
      }, {
        headers: { 
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        usage: {
          prompt_tokens: response.data.prompt_eval_count,
          completion_tokens: response.data.eval_count,
          total_tokens: response.data.prompt_eval_count + response.data.eval_count
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setError('Ошибка отправки сообщения');
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Отправка сообщения с файлом
  const sendMessageWithFile = async (formData, fileName) => {
    if (!isAuthenticated || !authToken) {
      setError('Требуется авторизация');
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: `📎 ${fileName}\n${formData.get('message') || 'Обработай этот файл'}`,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // Сначала загружаем файл в document-parser
      const uploadResponse = await axios.post(`/api/upload/chat`, formData, {
        headers: { 
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      if (uploadResponse.data.success) {
        // Получаем содержимое файла
        const fileContent = uploadResponse.data.content;
        
        // Отправляем запрос к AI с содержимым файла
        const prompt = `Файл: ${fileName}\n\nСодержимое файла:\n${fileContent}\n\nЗапрос пользователя: ${formData.get('message') || 'Обработай этот файл'}`;
        
        const response = await axios.post(`/ollama/api/generate`, {
          model: selectedModel,
          prompt: prompt,
          stream: false
        }, {
          headers: { 
            Authorization: `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        });

        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date().toISOString(),
          usage: {
            prompt_tokens: response.data.prompt_eval_count,
            completion_tokens: response.data.eval_count,
            total_tokens: response.data.prompt_eval_count + response.data.eval_count
          }
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Ошибка обработки файла');
      }
    } catch (error) {
      setError('Ошибка обработки файла');
      console.error('Error processing file:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Очистка чата
  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  useEffect(() => {
    console.log('🔍 [DEBUG] App.js: Initial useEffect triggered');
    console.log('🔍 [DEBUG] App.js: Current auth state:', { isAuthenticated, authToken: !!authToken });
    
    const initializeApp = async () => {
      setIsLoading(true);
      console.log('🔍 [DEBUG] App.js: Starting app initialization');
      
      // Проверяем статус системы всегда
      await checkSystemStatus();
      
      // Загружаем модели только если авторизованы
      if (isAuthenticated && authToken) {
        console.log('🔍 [DEBUG] App.js: User is authenticated, loading models');
        await loadModels();
      } else {
        console.log('🔍 [DEBUG] App.js: User is not authenticated, skipping models load');
      }
      
      setIsLoading(false);
      console.log('🔍 [DEBUG] App.js: App initialization completed');
    };
    initializeApp();
  }, [isAuthenticated, authToken]);

  console.log('🔍 [DEBUG] App.js: Rendering with currentPage:', currentPage, 'isLoading:', isLoading);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Mobile overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-75 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 lg:static lg:z-auto ${isSidebarOpen ? 'block' : 'hidden'} lg:block`}>
        <Sidebar
          currentPage={currentPage}
          onPageChange={setCurrentPage}
          systemStatus={systemStatus}
          isAuthenticated={isAuthenticated}
          userInfo={userInfo}
          authMethod={authMethod}
          onLogout={handleLogout}
          onClose={() => setIsSidebarOpen(false)}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <Header
          currentPage={currentPage}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          isSidebarOpen={isSidebarOpen}
        />

        {/* Page Content */}
        <main className="flex-1 p-6">
          {currentPage === 'dashboard' && (
            <DashboardPage
              systemStatus={systemStatus}
              models={models}
              isAuthenticated={isAuthenticated}
              userInfo={userInfo}
              authMethod={authMethod}
              onPageChange={setCurrentPage}
            />
          )}

          {currentPage === 'chat' && (
            <ChatPage
              models={models}
              selectedModel={selectedModel}
              onModelSelect={setSelectedModel}
              onRefreshModels={loadModels}
              messages={messages}
              onSendMessage={sendMessage}
              onSendMessageWithFile={sendMessageWithFile}
              isLoading={isLoading}
              error={error}
              onClearChat={clearChat}
              isAuthenticated={isAuthenticated}
              showSettings={showSettings}
              SettingsPanel={
                <SettingsPanel
                  onClose={() => setShowSettings(false)}
                  systemStatus={systemStatus}
                  onRefreshStatus={checkSystemStatus}
                />
              }
            />
          )}

          {currentPage === 'normcontrol' && (
            <NormcontrolPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
              refreshTrigger={refreshTabs}
              onRefreshComplete={() => setRefreshTabs(false)}
            />
          )}

          {currentPage === 'calculations' && (
            <CalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'structural-calculations' && (
            <StructuralCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'electrical-calculations' && (
            <CalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
              calculationType="electrical"
            />
          )}

          {currentPage === 'mechanical-calculations' && (
            <CalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
              calculationType="mechanical"
            />
          )}

          {currentPage === 'thermal-calculations' && (
            <CalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
              calculationType="thermal"
            />
          )}

          {currentPage === 'safety-calculations' && (
            <CalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
              calculationType="safety"
            />
          )}

          {currentPage === 'documents' && (
            <DocumentsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
              refreshTrigger={refreshTabs}
              onRefreshComplete={() => setRefreshTabs(false)}
            />
          )}
        </main>
      </div>

      {/* Модальное окно авторизации */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </div>
  );
}

export default App;
