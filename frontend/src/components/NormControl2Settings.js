import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Save, 
  RotateCcw, 
  CheckCircle, 
  AlertCircle,
  Info,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';

const NormControl2Settings = ({ isAuthenticated, authToken, onSettingsChange }) => {
  const [settings, setSettings] = useState({
    // Настройки валидации
    criticalThreshold: 1,
    highThreshold: 5,
    mediumThreshold: 10,
    
    // Настройки файлов
    maxFileSize: 100,
    timeoutSeconds: 300,
    
    // Включение/отключение стандартов
    eskd21_501_enabled: true,
    eskdR_21_101_enabled: true,
    spds48_13330_enabled: true,
    spds70_13330_enabled: true,
    
    // Настройки шрифтов
    minFontSize: 2.5,
    maxFontSize: 14.0,
    
    // Настройки масштабов
    allowCustomScales: false,
    maxScaleValue: 10000,
    
    // Настройки единиц измерений
    metricSystemRequired: true,
    
    // Настройки интерфейса
    autoValidation: true,
    saveResults: true,
    notificationEnabled: true,
    showDetailedResults: true
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const API_BASE = process.env.REACT_APP_API_BASE || '/api';

  // Загрузка настроек
  const loadSettings = async () => {
    if (!isAuthenticated || !authToken) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/normcontrol2/settings`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({ ...prev, ...data.settings }));
      }
    } catch (err) {
      console.error('Ошибка загрузки настроек:', err);
    } finally {
      setLoading(false);
    }
  };

  // Сохранение настроек
  const saveSettings = async () => {
    if (!isAuthenticated || !authToken) return;

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_BASE}/normcontrol2/settings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings })
      });

      if (response.ok) {
        setSuccess('Настройки успешно сохранены');
        if (onSettingsChange) {
          onSettingsChange(settings);
        }
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Ошибка сохранения настроек');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // Сброс настроек
  const resetSettings = () => {
    setSettings({
      criticalThreshold: 1,
      highThreshold: 5,
      mediumThreshold: 10,
      maxFileSize: 100,
      timeoutSeconds: 300,
      eskd21_501_enabled: true,
      eskdR_21_101_enabled: true,
      spds48_13330_enabled: true,
      spds70_13330_enabled: true,
      minFontSize: 2.5,
      maxFontSize: 14.0,
      allowCustomScales: false,
      maxScaleValue: 10000,
      metricSystemRequired: true,
      autoValidation: true,
      saveResults: true,
      notificationEnabled: true,
      showDetailedResults: true
    });
  };

  // Обработка изменений
  const handleChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  // Обработка переключателей
  const handleToggle = (key) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
  };

  useEffect(() => {
    loadSettings();
  }, [isAuthenticated, authToken]);

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Требуется авторизация</h3>
        <p className="text-gray-600">Войдите в систему для доступа к настройкам</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Settings className="w-6 h-6 mr-2" />
            Настройки Нормоконтроль - 2
          </h2>
          <p className="text-gray-600">Настройка параметров валидации и интерфейса</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={resetSettings}
            className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 flex items-center"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Сбросить
          </button>
          <button
            onClick={saveSettings}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {saving ? (
              <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Сохранить
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Загрузка настроек...</p>
        </div>
      )}

      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Настройки валидации */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Info className="w-5 h-5 mr-2 text-blue-600" />
              Пороги валидации
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Критические проблемы (блокируют приемку)
                </label>
                <input
                  type="number"
                  min="0"
                  value={settings.criticalThreshold}
                  onChange={(e) => handleChange('criticalThreshold', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Высокий приоритет (требует исправления)
                </label>
                <input
                  type="number"
                  min="0"
                  value={settings.highThreshold}
                  onChange={(e) => handleChange('highThreshold', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Средний приоритет (рекомендуется исправить)
                </label>
                <input
                  type="number"
                  min="0"
                  value={settings.mediumThreshold}
                  onChange={(e) => handleChange('mediumThreshold', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Настройки файлов */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Info className="w-5 h-5 mr-2 text-green-600" />
              Ограничения файлов
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Максимальный размер файла (МБ)
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={settings.maxFileSize}
                  onChange={(e) => handleChange('maxFileSize', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Таймаут валидации (секунды)
                </label>
                <input
                  type="number"
                  min="30"
                  max="1800"
                  value={settings.timeoutSeconds}
                  onChange={(e) => handleChange('timeoutSeconds', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Стандарты ЕСКД */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Info className="w-5 h-5 mr-2 text-purple-600" />
              Стандарты ЕСКД
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">ГОСТ 21.501-2018</div>
                  <div className="text-sm text-gray-600">Правила выполнения чертежей</div>
                </div>
                <button
                  onClick={() => handleToggle('eskd21_501_enabled')}
                  className="text-2xl"
                >
                  {settings.eskd21_501_enabled ? (
                    <ToggleRight className="text-green-600" />
                  ) : (
                    <ToggleLeft className="text-gray-400" />
                  )}
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">ГОСТ Р 21.101-2020</div>
                  <div className="text-sm text-gray-600">Система проектной документации</div>
                </div>
                <button
                  onClick={() => handleToggle('eskdR_21_101_enabled')}
                  className="text-2xl"
                >
                  {settings.eskdR_21_101_enabled ? (
                    <ToggleRight className="text-green-600" />
                  ) : (
                    <ToggleLeft className="text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Стандарты СПДС */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Info className="w-5 h-5 mr-2 text-orange-600" />
              Стандарты СПДС
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">СП 48.13330.2019</div>
                  <div className="text-sm text-gray-600">Организация строительства</div>
                </div>
                <button
                  onClick={() => handleToggle('spds48_13330_enabled')}
                  className="text-2xl"
                >
                  {settings.spds48_13330_enabled ? (
                    <ToggleRight className="text-green-600" />
                  ) : (
                    <ToggleLeft className="text-gray-400" />
                  )}
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">СП 70.13330.2012</div>
                  <div className="text-sm text-gray-600">Несущие и ограждающие конструкции</div>
                </div>
                <button
                  onClick={() => handleToggle('spds70_13330_enabled')}
                  className="text-2xl"
                >
                  {settings.spds70_13330_enabled ? (
                    <ToggleRight className="text-green-600" />
                  ) : (
                    <ToggleLeft className="text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Настройки шрифтов */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Info className="w-5 h-5 mr-2 text-indigo-600" />
              Настройки шрифтов
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Минимальный размер шрифта
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  step="0.5"
                  value={settings.minFontSize}
                  onChange={(e) => handleChange('minFontSize', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Максимальный размер шрифта
                </label>
                <input
                  type="number"
                  min="5"
                  max="50"
                  step="0.5"
                  value={settings.maxFontSize}
                  onChange={(e) => handleChange('maxFontSize', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Настройки интерфейса */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Info className="w-5 h-5 mr-2 text-cyan-600" />
              Настройки интерфейса
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Автоматическая валидация</div>
                  <div className="text-sm text-gray-600">Проверка при загрузке файла</div>
                </div>
                <button
                  onClick={() => handleToggle('autoValidation')}
                  className="text-2xl"
                >
                  {settings.autoValidation ? (
                    <ToggleRight className="text-green-600" />
                  ) : (
                    <ToggleLeft className="text-gray-400" />
                  )}
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Сохранять результаты</div>
                  <div className="text-sm text-gray-600">Сохранение результатов валидации</div>
                </div>
                <button
                  onClick={() => handleToggle('saveResults')}
                  className="text-2xl"
                >
                  {settings.saveResults ? (
                    <ToggleRight className="text-green-600" />
                  ) : (
                    <ToggleLeft className="text-gray-400" />
                  )}
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Уведомления</div>
                  <div className="text-sm text-gray-600">Уведомления о результатах</div>
                </div>
                <button
                  onClick={() => handleToggle('notificationEnabled')}
                  className="text-2xl"
                >
                  {settings.notificationEnabled ? (
                    <ToggleRight className="text-green-600" />
                  ) : (
                    <ToggleLeft className="text-gray-400" />
                  )}
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Детальные результаты</div>
                  <div className="text-sm text-gray-600">Показывать подробную информацию</div>
                </div>
                <button
                  onClick={() => handleToggle('showDetailedResults')}
                  className="text-2xl"
                >
                  {settings.showDetailedResults ? (
                    <ToggleRight className="text-green-600" />
                  ) : (
                    <ToggleLeft className="text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Уведомления */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            <span className="text-green-800">{success}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default NormControl2Settings;


