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
  SettingsPanel,
  // Турбо режим рассуждения
  turboMode,
  onTurboModeChange,
  reasoningDepth,
  onReasoningDepthChange,
  reasoningModes
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 animate-fade-in">
      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 gap-8">
          {/* Chat Interface */}
          <div className="w-full">
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
              // Турбо режим рассуждения
              turboMode={turboMode}
              onTurboModeChange={onTurboModeChange}
              reasoningDepth={reasoningDepth}
              onReasoningDepthChange={onReasoningDepthChange}
              reasoningModes={reasoningModes}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
