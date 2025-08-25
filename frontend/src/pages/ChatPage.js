import React from 'react';
import ChatInterface from '../components/ChatInterface';

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
      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 gap-8">
          {/* Chat Interface */}
          <div className="w-full">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <ChatInterface
                messages={messages}
                onSendMessage={onSendMessage}
                onSendMessageWithFile={onSendMessageWithFile}
                isLoading={isLoading}
                error={error}
                onClearChat={onClearChat}
                selectedModel={selectedModel}
                models={models}
                onModelSelect={onModelSelect}
                onRefreshModels={onRefreshModels}
                isAuthenticated={isAuthenticated}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
