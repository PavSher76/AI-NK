import React from 'react';
import { X, RefreshCw, Server, Database, Shield } from 'lucide-react';

const SettingsPanel = ({ onClose, systemStatus, onRefreshStatus }) => {
  const getServiceIcon = (service) => {
    const icons = {
      gateway: Server,
      ollama: Database,
      keycloak: Shield
    };
    return icons[service] || Server;
  };

  const getServiceName = (service) => {
    const names = {
      gateway: 'API Gateway',
      ollama: 'Ollama LLM',
      keycloak: 'Keycloak Auth'
    };
    return names[service] || service;
  };

  const getServiceUrl = (service) => {
    const urls = {
      gateway: 'http://localhost:8080',
      ollama: 'http://localhost:11434',
      keycloak: 'http://localhost:8081'
    };
    return urls[service] || '';
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Настройки системы</h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Статус сервисов</span>
          <button
            onClick={onRefreshStatus}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="Обновить статус"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-3">
          {Object.entries(systemStatus).map(([service, isOnline]) => {
            const Icon = getServiceIcon(service);
            return (
              <div
                key={service}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  isOnline
                    ? 'border-green-200 bg-green-50'
                    : 'border-red-200 bg-red-50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-5 h-5 ${
                    isOnline ? 'text-green-600' : 'text-red-600'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-900">
                      {getServiceName(service)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {getServiceUrl(service)}
                    </p>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                  isOnline
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}>
                  {isOnline ? 'Online' : 'Offline'}
                </div>
              </div>
            );
          })}
        </div>

        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Информация</h4>
          <div className="text-xs text-gray-500 space-y-1">
            <p>• API Gateway: Прокси для LLM запросов</p>
            <p>• Ollama: Локальный LLM сервер</p>
            <p>• Keycloak: Система авторизации</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
