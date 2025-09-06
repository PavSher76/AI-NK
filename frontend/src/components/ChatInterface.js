import React, { useState } from 'react';
import ChatHeader from './chat/ChatHeader';
import ChatMessages from './chat/ChatMessages';
import ChatInput from './chat/ChatInput';
import ChatSettings from './chat/ChatSettings';

const ChatInterface = ({ 
  messages, 
  onSendMessage, 
  onSendMessageWithFile, 
  isLoading, 
  error, 
  onClearChat, 
  selectedModel,
  models,
  onModelSelect,
  onRefreshModels,
  isAuthenticated,
  // Турбо режим рассуждения
  turboMode,
  onTurboModeChange,
  reasoningDepth,
  onReasoningDepthChange,
  reasoningModes
}) => {
  const [showSettings, setShowSettings] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);

  const handleResetSettings = (defaultSettings) => {
    setTemperature(defaultSettings.temperature);
    setMaxTokens(defaultSettings.maxTokens);
  };

  return (
    <>
      <div className="card-elevated h-[700px] flex flex-col animate-fade-in">
        {/* Header */}
        <ChatHeader
          selectedModel={selectedModel}
          models={models}
          onModelSelect={onModelSelect}
          onRefreshModels={onRefreshModels}
          isAuthenticated={isAuthenticated}
          turboMode={turboMode}
          onTurboModeChange={onTurboModeChange}
          reasoningDepth={reasoningDepth}
          onReasoningDepthChange={onReasoningDepthChange}
          reasoningModes={reasoningModes}
          onClearChat={onClearChat}
          onOpenSettings={() => setShowSettings(true)}
        />

        {/* Messages */}
        <ChatMessages
          messages={messages}
          isLoading={isLoading}
          reasoningModes={reasoningModes}
        />

        {/* Input */}
        <ChatInput
          onSendMessage={onSendMessage}
          onSendMessageWithFile={onSendMessageWithFile}
          isLoading={isLoading}
          error={error}
        />
      </div>

      {/* Settings Modal */}
      <ChatSettings
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        turboMode={turboMode}
        onTurboModeChange={onTurboModeChange}
        reasoningDepth={reasoningDepth}
        onReasoningDepthChange={onReasoningDepthChange}
        reasoningModes={reasoningModes}
        temperature={temperature}
        onTemperatureChange={setTemperature}
        maxTokens={maxTokens}
        onMaxTokensChange={setMaxTokens}
        onResetSettings={handleResetSettings}
      />
    </>
  );
};

export default ChatInterface;
