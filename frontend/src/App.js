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
// import AuthModal from './components/AuthModal'; // Отключено

// Pages
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import NormcontrolPage from './pages/NormcontrolPage';
import CalculationsPage from './pages/CalculationsPage';
import StructuralCalculationsPage from './pages/StructuralCalculationsPage';
import DocumentsPage from './pages/DocumentsPage';
import NTDConsultation from './components/NTDConsultation';

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

  // Отключена авторизация - автоматически устанавливаем как авторизованного
  useEffect(() => {
    console.log('🔍 [DEBUG] App.js: Авторизация отключена - устанавливаем как авторизованного');
    
    // Устанавливаем пользователя как авторизованного без проверки токена
    const userInfo = {
      token: 'disabled-auth',
      username: 'user',
      method: 'disabled',
      expiresAt: Date.now() + (24 * 60 * 60 * 1000) // 24 часа
    };
    
    setUserInfo(userInfo);
    setAuthToken(userInfo.token);
    setAuthMethod(userInfo.method);
    setIsAuthenticated(true);
    setShowAuthModal(false);
    
    // Сохраняем в localStorage
    localStorage.setItem('userInfo', JSON.stringify(userInfo));
    
    console.log('🔍 [DEBUG] App.js: Пользователь установлен как авторизованный');
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

      // Проверка Ollama (авторизация отключена)
      try {
        const ollamaResponse = await axios.get('/api/chat/health', {
          timeout: 300000 // 5 минут (300 секунд)
        });
        setSystemStatus(prev => ({ ...prev, ollama: true }));
      } catch (error) {
        console.log('🔍 [DEBUG] App.js: Ollama health check failed:', error.message);
        setSystemStatus(prev => ({ ...prev, ollama: false }));
      }

      // Проверка Keycloak (авторизация отключена)
      setSystemStatus(prev => ({ ...prev, keycloak: true }));
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
        console.log('loadModels: Загружаем модели от VLLM сервиса...');
        
        // Получаем модели напрямую от VLLM сервиса
        const response = await axios.get('http://localhost:8005/models', {
          timeout: 10000 // 10 секунд
        });
        
        console.log('loadModels: Получен ответ от VLLM:', response.status, response.data);
        
        if (response.data.status === 'success' && response.data.models) {
          // Преобразуем формат данных из VLLM в формат, ожидаемый фронтендом
          const modelsData = response.data.models.map(model => ({
            id: model.name,
            name: model.name,
            status: model.status,
            type: model.type
          }));
          
          console.log('loadModels: Преобразованные данные:', modelsData);
          
          setModels(modelsData);
          if (modelsData.length > 0 && !selectedModel) {
            setSelectedModel(modelsData[0].id);
            console.log('loadModels: Установлена первая модель:', modelsData[0].id);
          }
          setError(null); // Очищаем ошибки при успешной загрузке
          console.log('loadModels: Модели загружены', modelsData.length);
        } else {
          console.error('loadModels: Неверный формат ответа от VLLM:', response.data);
          setError('Неверный формат ответа от сервиса моделей');
        }
      } catch (error) {
        console.error('🔍 [DEBUG] App.js: Error loading models:', error);
        console.error('🔍 [DEBUG] App.js: Error response:', error.response?.data);
        console.error('🔍 [DEBUG] App.js: Error status:', error.response?.status);
        setError('Ошибка загрузки моделей от VLLM сервиса');
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
      const response = await axios.post(`http://localhost:8005/chat`, {
        message: content,
        model: selectedModel
      }, {
        timeout: 120000 // 2 минуты
      });

      if (response.data.status === 'success') {
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date().toISOString(),
          usage: {
            prompt_tokens: response.data.prompt_tokens || 0,
            completion_tokens: response.data.response_tokens || 0,
            total_tokens: response.data.tokens_used || 0
          }
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(response.data.response || 'Ошибка генерации ответа');
      }
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
        },
        timeout: 300000 // 5 минут (300 секунд)
      });

      if (uploadResponse.data.success) {
        // Получаем содержимое файла
        const fileContent = uploadResponse.data.content;
        
        // Отправляем запрос к AI с содержимым файла
        const prompt = `Файл: ${fileName}\n\nСодержимое файла:\n${fileContent}\n\nЗапрос пользователя: ${formData.get('message') || 'Обработай этот файл'}`;
        
        const response = await axios.post(`http://localhost:8005/chat`, {
          message: prompt,
          model: selectedModel
        }, {
          timeout: 120000 // 2 минуты
        });

        if (response.data.status === 'success') {
          const assistantMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: response.data.response,
            timestamp: new Date().toISOString(),
            usage: {
              prompt_tokens: response.data.prompt_tokens || 0,
              completion_tokens: response.data.response_tokens || 0,
              total_tokens: response.data.tokens_used || 0
            }
          };

          setMessages(prev => [...prev, assistantMessage]);
        } else {
          throw new Error(response.data.response || 'Ошибка генерации ответа');
        }
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

          {currentPage === 'ntd-consultation' && (
            <NTDConsultation
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}
        </main>
      </div>

      {/* Модальное окно авторизации отключено */}
      {/* <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onAuthSuccess={handleAuthSuccess}
      /> */}
    </div>
  );
}

export default App;
