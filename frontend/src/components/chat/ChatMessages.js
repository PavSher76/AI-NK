import React, { useRef, useEffect } from 'react';
import { Bot, User, Loader2, Zap, Brain, Clock } from 'lucide-react';

const ChatMessages = ({ 
  messages, 
  isLoading, 
  reasoningModes 
}) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatUsage = (message) => {
    if (!message.usage) return null;
    
    return (
      <div className="text-xs text-gray-500 mt-2 space-y-1">
        <div>
          Токены: {message.usage.prompt_tokens} + {message.usage.completion_tokens} = {message.usage.total_tokens}
        </div>
        
        {/* Метаданные турбо режима */}
        {message.turbo_mode !== undefined && (
          <div className="flex items-center space-x-2">
            {message.turbo_mode ? (
              <span className="flex items-center space-x-1 text-warning-600">
                <Zap className="w-3 h-3" />
                <span>Турбо режим</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-primary-600">
                <Brain className="w-3 h-3" />
                <span>{reasoningModes[message.reasoning_depth]?.name || message.reasoning_depth}</span>
              </span>
            )}
            
            {message.reasoning_steps && (
              <span className="flex items-center space-x-1 text-gray-600">
                <span>Шагов: {message.reasoning_steps}</span>
              </span>
            )}
            
            {message.generation_time_ms && (
              <span className="flex items-center space-x-1 text-gray-600">
                <Clock className="w-3 h-3" />
                <span>{(message.generation_time_ms / 1000).toFixed(1)}с</span>
              </span>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 py-16">
          <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 rounded-3xl flex items-center justify-center mx-auto mb-6">
            <Bot className="w-10 h-10 text-primary-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Начните разговор с ИИ</h3>
          <p className="text-sm text-gray-500">Задайте любой вопрос или попросите о помощи</p>
        </div>
      ) : (
        messages.map((message, index) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
            style={{animationDelay: `${index * 100}ms`}}
          >
            <div
              className={`max-w-[80%] rounded-2xl p-4 shadow-soft ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              <div className="flex items-start space-x-3">
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className="flex-1">
                  <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  {formatUsage(message)}
                  <p className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-white/70' : 'text-gray-400'
                  }`}>
                    {formatTime(message.timestamp)}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            </div>
          </div>
        ))
      )}
      
      {isLoading && (
        <div className="flex justify-start animate-slide-up">
          <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-soft">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                <Loader2 className="w-4 h-4 text-white animate-spin" />
              </div>
              <span className="text-gray-600 font-medium">ИИ думает...</span>
            </div>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatMessages;
