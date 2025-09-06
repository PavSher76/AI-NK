import React from 'react';
import { Bot, Trash2, Settings, Zap, Brain } from 'lucide-react';
import ModelSelector from '../ModelSelector';

const ChatHeader = ({ 
  selectedModel,
  models,
  onModelSelect,
  onRefreshModels,
  isAuthenticated,
  turboMode,
  onTurboModeChange,
  reasoningDepth,
  onReasoningDepthChange,
  reasoningModes,
  onClearChat,
  onOpenSettings
}) => {
  return (
    <div className="flex items-center justify-between pb-6 border-b border-gray-100">
      <div className="flex items-center space-x-4">
        <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center shadow-soft">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900 tracking-tight">Чат с ИИ</h2>
          <div className="flex items-center space-x-3 mt-2">
            <span className="text-sm text-gray-500 font-medium">Модель:</span>
            <ModelSelector
              models={models}
              selectedModel={selectedModel}
              onModelChange={onModelSelect}
              onRefresh={onRefreshModels}
              isAuthenticated={isAuthenticated}
            />
          </div>
        </div>
      </div>
      
      {/* Управление чатом */}
      <div className="flex items-center space-x-3">
        {/* Турбо режим и настройки рассуждения */}
        <div className="flex items-center space-x-3">
          {/* Кнопка турбо режима */}
          <button
            onClick={() => onTurboModeChange(!turboMode)}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 transform hover:-translate-y-0.5 ${
              turboMode 
                ? 'bg-gradient-to-r from-warning-500 to-warning-600 text-white shadow-soft hover:shadow-glow' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:shadow-soft'
            }`}
            title={turboMode ? 'Отключить турбо режим' : 'Включить турбо режим'}
          >
            <Zap className={`w-4 h-4 ${turboMode ? 'text-white' : 'text-gray-500'}`} />
            <span>Турбо</span>
          </button>
          
          {/* Выбор глубины рассуждения (только когда турбо выключен) */}
          {!turboMode && reasoningModes && Object.keys(reasoningModes).length > 0 && (
            <div className="flex items-center space-x-2">
              <Brain className="w-4 h-4 text-gray-500" />
              <select
                value={reasoningDepth}
                onChange={(e) => onReasoningDepthChange(e.target.value)}
                className="text-sm border border-gray-200 rounded-xl px-3 py-2 bg-white shadow-soft focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-300"
                title="Глубина рассуждения"
              >
                {Object.entries(reasoningModes).map(([key, mode]) => (
                  <option key={key} value={key}>
                    {mode.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Кнопки управления */}
        <div className="flex items-center space-x-2">
          {/* Настройки */}
          <button
            onClick={onOpenSettings}
            className="p-2.5 text-gray-400 hover:text-primary-500 hover:bg-primary-50 rounded-xl transition-all duration-300 group"
            title="Настройки чата"
          >
            <Settings className="w-4 h-4 group-hover:scale-110 transition-transform" />
          </button>
          
          {/* Очистить чат */}
          <button
            onClick={onClearChat}
            className="p-2.5 text-gray-400 hover:text-error-500 hover:bg-error-50 rounded-xl transition-all duration-300 group"
            title="Очистить чат"
          >
            <Trash2 className="w-4 h-4 group-hover:scale-110 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;
