import React from 'react';
import ChatInterface from '../components/ChatInterface';
import ModelSelector from '../components/ModelSelector';

const ChatPage = ({
  models,
  selectedModel,
  onModelSelect,
  onRefreshModels,
  messages,
  onSendMessage,
  onSendMessageWithFile,
  isLoading,
  error,
  onClearChat,
  isAuthenticated,
  showSettings,
  SettingsPanel
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Page Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Чат с AI</h1>
              <p className="text-gray-600 mt-1">
                Общайтесь с искусственным интеллектом для решения задач нормоконтроля
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <ModelSelector
              models={models}
              selectedModel={selectedModel}
              onModelSelect={onModelSelect}
              onRefresh={onRefreshModels}
              isAuthenticated={isAuthenticated}
            />
            
            {showSettings && SettingsPanel}
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <ChatInterface
                messages={messages}
                onSendMessage={onSendMessage}
                onSendMessageWithFile={onSendMessageWithFile}
                isLoading={isLoading}
                error={error}
                onClearChat={onClearChat}
                selectedModel={selectedModel}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
