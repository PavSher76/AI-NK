import React from 'react';
import { CheckCircle, XCircle, Wifi, WifiOff } from 'lucide-react';

const StatusIndicator = ({ status }) => {
  const getStatusColor = (isOnline) => {
    return isOnline ? 'text-green-500' : 'text-red-500';
  };

  const getStatusIcon = (isOnline) => {
    return isOnline ? (
      <CheckCircle className="w-4 h-4" />
    ) : (
      <XCircle className="w-4 h-4" />
    );
  };

  const getServiceName = (key) => {
    const names = {
      gateway: 'Gateway',
      ollama: 'Ollama',
      keycloak: 'Keycloak'
    };
    return names[key] || key;
  };

  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center space-x-1">
        {status.gateway ? (
          <Wifi className="w-4 h-4 text-green-500" />
        ) : (
          <WifiOff className="w-4 h-4 text-red-500" />
        )}
      </div>
      
      <div className="hidden sm:flex items-center space-x-1">
        {Object.entries(status).map(([service, isOnline]) => (
          <div
            key={service}
            className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
              isOnline ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
            title={`${getServiceName(service)}: ${isOnline ? 'Online' : 'Offline'}`}
          >
            {getStatusIcon(isOnline)}
            <span className="hidden md:inline">{getServiceName(service)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatusIndicator;
