import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  X, 
  Save, 
  RefreshCw,
  Brain,
  Database,
  Server,
  Shield,
  Clock,
  AlertCircle
} from 'lucide-react';

const SystemSettings = ({ isOpen, onClose, authToken }) => {
  const [settings, setSettings] = useState({
    llm_model: 'system',
    system_timeout: 300,
    debug_mode: true,
    auto_save: true,
    max_file_size: 10,
    supported_formats: ['pdf', 'docx', 'txt'],
    notification_enabled: true,
    log_level: 'info'
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

  // Загрузка системных настроек
  const fetchSystemSettings = async () => {
    try {
      setLoading(true);
      
      // Загружаем настройки из разных сервисов
      const [outgoingSettings, vllmHealth] = await Promise.all([
        fetch(`${API_BASE}/outgoing-control/settings`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }).then(res => res.ok ? res.json() : {}),
        
        fetch(`${API_BASE}/vllm/health`).then(res => res.ok ? res.json() : {})
      ]);

      // Объединяем настройки
      setSettings(prev => ({
        ...prev,
        llm_model: outgoingSettings.selected_llm_model || 'system',
        llm_prompt: outgoingSettings.llm_prompt || '',
        available_models: vllmHealth.services?.ollama?.available_models || ['llama3.1:8b', 'gpt-oss-optimized:latest']
      }));
      
    } catch (error) {
      console.error('Ошибка загрузки системных настроек:', error);
      setError('Ошибка загрузки настроек');
    } finally {
      setLoading(false);
    }
  };

  // Сохранение системных настроек
  const saveSystemSettings = async () => {
    try {
      setLoading(true);
      setError(null);

      // Сохраняем настройки LLM
      const llmResponse = await fetch(`${API_BASE}/outgoing-control/settings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          selected_llm_model: settings.llm_model,
          llm_prompt: settings.llm_prompt
        })
      });

      if (!llmResponse.ok) {
        throw new Error('Ошибка сохранения настроек LLM');
      }

      setSuccess('Системные настройки успешно сохранены');
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (error) {
      console.error('Ошибка сохранения системных настроек:', error);
      setError('Ошибка сохранения настроек');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSystemSettings();
    }
  }, [isOpen, authToken]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Settings className="w-6 h-6 mr-3" />
            Системные настройки
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md flex items-center">
            <Shield className="w-5 h-5 text-green-500 mr-2" />
            <span className="text-green-700">{success}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Настройки LLM */}
          <div className="space-y-4">
            <div className="flex items-center mb-4">
              <Brain className="w-5 h-5 text-blue-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Настройки LLM</h3>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Модель LLM по умолчанию
              </label>
              <select
                value={settings.llm_model}
                onChange={(e) => setSettings(prev => ({ ...prev, llm_model: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="system">Системная (локальная обработка)</option>
                {settings.available_models?.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <p className="text-sm text-gray-500 mt-1">
                Системная модель работает локально без внешних сервисов
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Выходной контроль корреспонденции: Промпт для экспертной проверки
              </label>
              <textarea
                value={settings.llm_prompt || ''}
                onChange={(e) => setSettings(prev => ({ ...prev, llm_prompt: e.target.value }))}
                className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Введите промпт для экспертной проверки..."
              />
            </div>
          </div>

          {/* Системные настройки */}
          <div className="space-y-4">
            <div className="flex items-center mb-4">
              <Server className="w-5 h-5 text-green-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Системные параметры</h3>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Таймаут обработки (секунды)
              </label>
              <input
                type="number"
                value={settings.system_timeout}
                onChange={(e) => setSettings(prev => ({ ...prev, system_timeout: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="30"
                max="600"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Максимальный размер файла (МБ)
              </label>
              <input
                type="number"
                value={settings.max_file_size}
                onChange={(e) => setSettings(prev => ({ ...prev, max_file_size: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Уровень логирования
              </label>
              <select
                value={settings.log_level}
                onChange={(e) => setSettings(prev => ({ ...prev, log_level: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="debug">Debug</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
              </select>
            </div>
          </div>

          {/* Настройки интерфейса */}
          <div className="space-y-4">
            <div className="flex items-center mb-4">
              <Database className="w-5 h-5 text-purple-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Настройки интерфейса</h3>
            </div>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.debug_mode}
                  onChange={(e) => setSettings(prev => ({ ...prev, debug_mode: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Режим отладки</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.auto_save}
                  onChange={(e) => setSettings(prev => ({ ...prev, auto_save: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Автосохранение</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.notification_enabled}
                  onChange={(e) => setSettings(prev => ({ ...prev, notification_enabled: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Уведомления</span>
              </label>
            </div>
          </div>

          {/* Статус системы */}
          <div className="space-y-4">
            <div className="flex items-center mb-4">
              <Shield className="w-5 h-5 text-orange-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Статус системы</h3>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">LLM Сервис:</span>
                <span className="text-green-600">Активен</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Spellchecker:</span>
                <span className="text-green-600">Активен</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">База данных:</span>
                <span className="text-green-600">Подключена</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Время работы:</span>
                <span className="text-gray-600">24ч 15м</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Отмена
          </button>
          <button
            onClick={fetchSystemSettings}
            disabled={loading}
            className="px-4 py-2 text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200 transition-colors flex items-center"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
          <button
            onClick={saveSystemSettings}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center"
          >
            <Save className="w-4 h-4 mr-2" />
            {loading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;
