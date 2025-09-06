import React, { useState } from 'react';
import { 
  Settings, 
  X, 
  Zap, 
  Brain, 
  Clock, 
  Thermometer, 
  Hash,
  Save,
  RotateCcw
} from 'lucide-react';

const ChatSettings = ({ 
  isOpen, 
  onClose, 
  turboMode, 
  onTurboModeChange,
  reasoningDepth,
  onReasoningDepthChange,
  reasoningModes,
  temperature,
  onTemperatureChange,
  maxTokens,
  onMaxTokensChange,
  onResetSettings
}) => {
  const [localSettings, setLocalSettings] = useState({
    turboMode,
    reasoningDepth,
    temperature: temperature || 0.7,
    maxTokens: maxTokens || 2048
  });

  const handleSave = () => {
    onTurboModeChange(localSettings.turboMode);
    onReasoningDepthChange(localSettings.reasoningDepth);
    if (onTemperatureChange) onTemperatureChange(localSettings.temperature);
    if (onMaxTokensChange) onMaxTokensChange(localSettings.maxTokens);
    onClose();
  };

  const handleReset = () => {
    const defaultSettings = {
      turboMode: false,
      reasoningDepth: 'balanced',
      temperature: 0.7,
      maxTokens: 2048
    };
    setLocalSettings(defaultSettings);
    onResetSettings && onResetSettings(defaultSettings);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-large max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center">
              <Settings className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Настройки чата</h2>
              <p className="text-sm text-gray-500">Настройте параметры запросов и режимы работы</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all duration-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-8">
          {/* Режимы рассуждения */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Brain className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold text-gray-900">Режимы рассуждения</h3>
            </div>
            
            {/* Турбо режим */}
            <div className="bg-gradient-to-r from-warning-50 to-warning-100 rounded-xl p-4 border border-warning-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-warning-500 to-warning-600 rounded-lg flex items-center justify-center">
                    <Zap className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Турбо режим</h4>
                    <p className="text-sm text-gray-600">Максимально быстрые ответы</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={localSettings.turboMode}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, turboMode: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-warning-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-warning-500"></div>
                </label>
              </div>
            </div>

            {/* Глубина рассуждения */}
            {!localSettings.turboMode && reasoningModes && Object.keys(reasoningModes).length > 0 && (
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Глубина рассуждения
                </label>
                <div className="grid grid-cols-1 gap-3">
                  {Object.entries(reasoningModes).map(([key, mode]) => (
                    <label key={key} className="relative">
                      <input
                        type="radio"
                        name="reasoningDepth"
                        value={key}
                        checked={localSettings.reasoningDepth === key}
                        onChange={(e) => setLocalSettings(prev => ({ ...prev, reasoningDepth: e.target.value }))}
                        className="sr-only peer"
                      />
                      <div className="p-4 border border-gray-200 rounded-xl cursor-pointer transition-all duration-300 peer-checked:border-primary-500 peer-checked:bg-primary-50 hover:border-gray-300">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold text-gray-900">{mode.name}</h4>
                            <p className="text-sm text-gray-600">{mode.description}</p>
                          </div>
                          <div className="text-right">
                            <div className="flex items-center space-x-1 text-xs text-gray-500">
                              <Clock className="w-3 h-3" />
                              <span>{mode.estimated_time}</span>
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {mode.max_tokens} токенов
                            </div>
                          </div>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Дополнительные параметры */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Settings className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold text-gray-900">Дополнительные параметры</h3>
            </div>

            {/* Temperature */}
            <div className="space-y-2">
              <label className="flex items-center space-x-2 text-sm font-medium text-gray-700">
                <Thermometer className="w-4 h-4" />
                <span>Температура (креативность)</span>
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={localSettings.temperature}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Консервативно (0.0)</span>
                  <span className="font-medium">{localSettings.temperature}</span>
                  <span>Креативно (2.0)</span>
                </div>
              </div>
            </div>

            {/* Max Tokens */}
            <div className="space-y-2">
              <label className="flex items-center space-x-2 text-sm font-medium text-gray-700">
                <Hash className="w-4 h-4" />
                <span>Максимум токенов</span>
              </label>
              <div className="grid grid-cols-4 gap-2">
                {[512, 1024, 2048, 4096].map((tokens) => (
                  <button
                    key={tokens}
                    onClick={() => setLocalSettings(prev => ({ ...prev, maxTokens: tokens }))}
                    className={`p-3 text-sm font-medium rounded-xl border transition-all duration-300 ${
                      localSettings.maxTokens === tokens
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    {tokens}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-100 bg-gray-50 rounded-b-2xl">
          <button
            onClick={handleReset}
            className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-xl transition-all duration-300"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Сбросить</span>
          </button>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="btn-secondary"
            >
              Отмена
            </button>
            <button
              onClick={handleSave}
              className="btn-primary flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>Сохранить</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatSettings;
