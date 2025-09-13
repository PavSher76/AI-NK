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
import SystemSettings from './components/SystemSettings';
// import AuthModal from './components/AuthModal'; // Отключено

// Pages
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import NormcontrolPage from './pages/NormcontrolPage';
import CalculationsPage from './pages/CalculationsPage';
import StructuralCalculationsPage from './pages/StructuralCalculationsPage';
import FoundationCalculationsPage from './pages/FoundationCalculationsPage';
import ThermalCalculationsPage from './pages/ThermalCalculationsPage';
import VentilationCalculationsPage from './pages/VentilationCalculationsPage';
import ElectricalCalculationsPage from './pages/ElectricalCalculationsPage';
import DegasificationCalculationsPage from './pages/DegasificationCalculationsPage';
import WaterSupplyCalculationsPage from './pages/WaterSupplyCalculationsPage';
import FireSafetyCalculationsPage from './pages/FireSafetyCalculationsPage';
import AcousticCalculationsPage from './pages/AcousticCalculationsPage';
import LightingCalculationsPage from './pages/LightingCalculationsPage';
import GeologicalCalculationsPage from './pages/GeologicalCalculationsPage';
import UAVProtectionCalculationsPage from './pages/UAVProtectionCalculationsPage';
import OutgoingControlPage from './pages/OutgoingControlPage';
import DocumentsPage from './pages/DocumentsPage';
import NTDConsultation from './components/NTDConsultation';

function App() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showSystemSettings, setShowSystemSettings] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState('');
  const [authMethod, setAuthMethod] = useState('');
  const [userInfo, setUserInfo] = useState(null);
  const [currentPage, setCurrentPage] = useState('dashboard'); // 'dashboard', 'chat', 'normcontrol', 'documents'
  
  // Состояние для турбо режима рассуждения
  const [turboMode, setTurboMode] = useState(false);
  const [reasoningDepth, setReasoningDepth] = useState('balanced');
  const [reasoningModes, setReasoningModes] = useState({});
  
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
    try {
      // Проверка Gateway (авторизация отключена)
      try {
        const gatewayResponse = await axios.get('/api/health', {
          timeout: 10000
        });
        setSystemStatus(prev => ({ ...prev, gateway: true }));
      } catch (error) {
        if (error.response && error.response.status === 401) {
          setSystemStatus(prev => ({ ...prev, gateway: true }));
        } else {
          setSystemStatus(prev => ({ ...prev, gateway: false }));
        }
      }

      // Проверка Ollama через VLLM (авторизация отключена)
      try {
        const ollamaResponse = await axios.get('http://localhost:8005/health', {
          timeout: 10000 // 10 секунд
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
      console.log('loadModels: Загружаем модели через Gateway...');
      
      // Получаем модели через Gateway
      const response = await axios.get('/api/chat/tags', {
        timeout: 10000, // 10 секунд
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      console.log('loadModels: Получен ответ от Gateway:', response.status, response.data);
      
      if (response.data.models && Array.isArray(response.data.models)) {
        // Преобразуем формат данных из Gateway в формат, ожидаемый фронтендом
        const modelsData = response.data.models.map(model => ({
          id: model.name,
          name: model.name,
          status: 'available',
          type: model.details?.family || 'unknown',
          size: model.size,
          parameter_size: model.details?.parameter_size || 'unknown',
          owned_by: model.details?.family || 'Ollama'
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
        console.error('loadModels: Неверный формат ответа от Gateway:', response.data);
        setError('Неверный формат ответа от сервиса моделей');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] App.js: Error loading models:', error);
      console.error('🔍 [DEBUG] App.js: Error response:', error.response?.data);
      console.error('🔍 [DEBUG] App.js: Error status:', error.response?.status);
      setError('Ошибка загрузки моделей через Gateway');
    }
  };

  // Загрузка режимов рассуждения
  const loadReasoningModes = async () => {
    try {
      const response = await axios.get(`/rag/reasoning-modes`);
      if (response.data.status === 'success') {
        setReasoningModes(response.data.reasoning_modes);
      }
    } catch (error) {
      console.error('Error loading reasoning modes:', error);
      // Fallback на мок-данные для тестирования
      setReasoningModes({
        "fast": {
          "name": "Быстрый",
          "description": "Краткие ответы, простые рассуждения",
          "temperature": 0.4,
          "max_tokens": 1024,
          "estimated_time": "5-15 секунд"
        },
        "balanced": {
          "name": "Сбалансированный",
          "description": "Подробные ответы с логическими рассуждениями",
          "temperature": 0.6,
          "max_tokens": 2048,
          "estimated_time": "15-30 секунд"
        },
        "deep": {
          "name": "Глубокий",
          "description": "Детальный анализ с пошаговыми рассуждениями",
          "temperature": 0.7,
          "max_tokens": 3072,
          "estimated_time": "30-60 секунд"
        },
        "turbo": {
          "name": "Турбо",
          "description": "Максимально быстрые ответы",
          "temperature": 0.3,
          "max_tokens": 1024,
          "estimated_time": "3-10 секунд"
        }
      });
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
      // Используем RAG сервис для поддержки турбо режима
      const response = await axios.post(`/rag/chat`, {
        message: content,
        model: selectedModel,
        turbo_mode: turboMode,
        reasoning_depth: reasoningDepth
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
          },
          // Метаданные турбо режима
          turbo_mode: response.data.turbo_mode || false,
          reasoning_depth: response.data.reasoning_depth || 'balanced',
          reasoning_steps: response.data.reasoning_steps || 0,
          generation_time_ms: response.data.generation_time_ms || 0
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
      // Отправляем файл напрямую в VLLM сервис для обработки
      const response = await axios.post(`http://localhost:8005/chat_with_document`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data'
        },
        timeout: 600000 // 10 минут для больших файлов
      });

      if (response.data.status === 'success') {
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.data.ai_response.response,
          timestamp: new Date().toISOString(),
          usage: {
            prompt_tokens: response.data.ai_response.prompt_tokens || 0,
            completion_tokens: response.data.ai_response.response_tokens || 0,
            total_tokens: response.data.ai_response.tokens_used || 0
          },
          document_info: {
            document_id: response.data.document_id,
            file_name: response.data.file_name,
            chunks_count: response.data.chunks_count
          }
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // Показываем информацию об обработанном документе
        console.log(`✅ Документ ${fileName} обработан успешно:`, {
          document_id: response.data.document_id,
          chunks_count: response.data.chunks_count
        });
      } else {
        throw new Error(response.data.error || 'Ошибка обработки документа');
      }
    } catch (error) {
      console.error('Error processing document:', error);
      
      let errorMessage = 'Ошибка обработки документа';
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
      
      // Добавляем сообщение об ошибке в чат
      const errorMessageObj = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `❌ Ошибка обработки документа: ${errorMessage}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessageObj]);
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
        await loadReasoningModes();
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
          onSystemSettingsClick={() => setShowSystemSettings(true)}
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
              // Турбо режим рассуждения
              turboMode={turboMode}
              onTurboModeChange={setTurboMode}
              reasoningDepth={reasoningDepth}
              onReasoningDepthChange={setReasoningDepth}
              reasoningModes={reasoningModes}
            />
          )}

          {currentPage === 'outgoing-control' && (
            <OutgoingControlPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
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

          {currentPage === 'foundation-calculations' && (
            <FoundationCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'degasification-calculations' && (
            <DegasificationCalculationsPage />
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

          {currentPage === 'foundation-calculations' && (
            <FoundationCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'thermal-calculations' && (
            <ThermalCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'ventilation-calculations' && (
            <VentilationCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'electrical-calculations' && (
            <ElectricalCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'water-supply-calculations' && (
            <WaterSupplyCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'fire-safety-calculations' && (
            <FireSafetyCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'acoustic-calculations' && (
            <AcousticCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'lighting-calculations' && (
            <LightingCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'geological-calculations' && (
            <GeologicalCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
            />
          )}

          {currentPage === 'uav-protection-calculations' && (
            <UAVProtectionCalculationsPage
              isAuthenticated={isAuthenticated}
              authToken={authToken}
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

      {/* Системные настройки */}
      <SystemSettings
        isOpen={showSystemSettings}
        onClose={() => setShowSystemSettings(false)}
        authToken={authToken}
      />
    </div>
  );
}

export default App;
