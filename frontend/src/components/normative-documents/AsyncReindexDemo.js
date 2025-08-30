import React, { useState, useEffect } from 'react';
import { Database, CheckCircle, XCircle, Loader } from 'lucide-react';

const AsyncReindexDemo = ({ authToken }) => {
  const [isReindexing, setIsReindexing] = useState(false);
  const [progress, setProgress] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [statusInterval, setStatusInterval] = useState(null);

  // Очистка интервала при размонтировании
  useEffect(() => {
    return () => {
      if (statusInterval) {
        clearInterval(statusInterval);
      }
    };
  }, [statusInterval]);

  const startAsyncReindex = async () => {
    setIsReindexing(true);
    setProgress({ message: 'Запуск асинхронной реиндексации...', progress: 0 });
    
    try {
      // Сначала пробуем асинхронную реиндексацию
      const response = await fetch('/api/reindex-documents/async', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.status === 'started' && result.task_id) {
          setTaskId(result.task_id);
          setProgress({
            message: `Реиндексация запущена для ${result.total_documents} документов...`,
            progress: 10,
            total_documents: result.total_documents
          });
          
          // Запускаем опрос статуса
          const interval = setInterval(async () => {
            try {
              const statusResponse = await fetch(`/api/reindex-documents/status/${result.task_id}`, {
                headers: {
                  'Authorization': `Bearer ${authToken}`,
                }
              });
              
              if (statusResponse.ok) {
                const status = await statusResponse.json();
                
                if (status.status === 'completed') {
                  clearInterval(interval);
                  setProgress({
                    message: status.message,
                    progress: 100,
                    result: status,
                    completed: true
                  });
                  
                  setTimeout(() => {
                    setIsReindexing(false);
                    setProgress(null);
                    setTaskId(null);
                    setStatusInterval(null);
                  }, 3000);
                  
                } else if (status.status === 'error') {
                  clearInterval(interval);
                  setProgress({
                    message: 'Ошибка реиндексации',
                    progress: 0,
                    error: true,
                    errorDetails: status.error
                  });
                  
                  setTimeout(() => {
                    setIsReindexing(false);
                    setProgress(null);
                    setTaskId(null);
                    setStatusInterval(null);
                  }, 3000);
                  
                } else {
                  // Обновляем прогресс
                  const progressValue = Math.min(90, 10 + (status.reindexed_count || 0) / (result.total_documents || 1) * 80);
                  setProgress({
                    message: `Обработано ${status.reindexed_count || 0} из ${result.total_documents} документов...`,
                    progress: progressValue,
                    current_document: status.current_document,
                    reindexed_count: status.reindexed_count,
                    total_documents: result.total_documents
                  });
                }
              }
            } catch (error) {
              console.error('Error checking reindex status:', error);
            }
          }, 2000);
          
          setStatusInterval(interval);
          
        } else {
          setProgress({
            message: result.message,
            progress: 100,
            result: result,
            completed: true
          });
          
          setTimeout(() => {
            setIsReindexing(false);
            setProgress(null);
          }, 2000);
        }
      } else {
        // Если асинхронная реиндексация недоступна, используем синхронную
        console.log('Async reindex not available, falling back to sync');
        await startSyncReindex();
      }
      
    } catch (error) {
      console.error('Error starting async reindex:', error);
      // Fallback к синхронной реиндексации
      await startSyncReindex();
    }
  };

  const startSyncReindex = async () => {
    setProgress({ message: 'Запуск синхронной реиндексации...', progress: 0 });
    
    try {
      const response = await fetch('/api/reindex-documents', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        setProgress({
          message: result.message,
          progress: 100,
          result: result,
          completed: true
        });
        
        setTimeout(() => {
          setIsReindexing(false);
          setProgress(null);
        }, 2000);
      } else {
        throw new Error('Ошибка синхронной реиндексации');
      }
    } catch (error) {
      setProgress({
        message: 'Ошибка запуска реиндексации',
        progress: 0,
        error: true,
        errorDetails: error.message
      });
      
      setTimeout(() => {
        setIsReindexing(false);
        setProgress(null);
      }, 3000);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Асинхронная реиндексация</h3>
          <p className="text-sm text-gray-600">Демонстрация полноценной асинхронной реиндексации документов</p>
        </div>
        
        <button
          onClick={startAsyncReindex}
          disabled={isReindexing}
          className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Database className="w-4 h-4" />
          <span>{isReindexing ? 'Реиндексация...' : 'Запустить реиндексацию'}</span>
        </button>
      </div>

      {/* Прогресс реиндексации */}
      {progress && (
        <div className={`p-4 rounded-lg border shadow-sm ${
          progress.error ? 'bg-red-50 border-red-200' : 
          progress.completed ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center space-x-3">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">{progress.message}</p>
              
              {/* Детали прогресса */}
              {progress.total_documents && (
                <div className="mt-2 text-sm text-gray-600">
                  <p>Всего документов: {progress.total_documents}</p>
                  {progress.reindexed_count !== undefined && (
                    <p>Обработано: {progress.reindexed_count}</p>
                  )}
                  {progress.current_document && (
                    <p>Текущий документ: {progress.current_document}</p>
                  )}
                </div>
              )}
              
              {/* Результат */}
              {progress.result && progress.completed && (
                <div className="mt-2 text-sm text-gray-600">
                  <p>Документов: {progress.result.total_documents}</p>
                  <p>Обновлено: {progress.result.reindexed_count}</p>
                  <p>Токенов: {progress.result.total_tokens?.toLocaleString()}</p>
                </div>
              )}
              
              {/* Ошибка */}
              {progress.error && progress.errorDetails && (
                <div className="mt-2 text-sm text-red-600">
                  <p>Детали ошибки: {progress.errorDetails}</p>
                </div>
              )}
            </div>
            
            {/* Иконка статуса */}
            <div className="flex-shrink-0">
              {progress.error ? (
                <XCircle className="w-6 h-6 text-red-500" />
              ) : progress.completed ? (
                <CheckCircle className="w-6 h-6 text-green-500" />
              ) : (
                <Loader className="w-6 h-6 text-blue-500 animate-spin" />
              )}
            </div>
          </div>
          
          {/* Прогресс-бар */}
          {!progress.error && (
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  progress.completed ? 'bg-green-600' : 'bg-blue-600'
                }`}
                style={{ width: `${progress.progress}%` }}
              ></div>
            </div>
          )}
        </div>
      )}

      {/* Информация о возможностях */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">Возможности асинхронной реиндексации:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Запуск реиндексации в фоновом режиме</li>
          <li>• Отслеживание прогресса в реальном времени</li>
          <li>• Автоматическое обновление статуса</li>
          <li>• Fallback к синхронной реиндексации</li>
          <li>• Детальная информация о процессе</li>
          <li>• Обработка ошибок с детализацией</li>
        </ul>
      </div>
    </div>
  );
};

export default AsyncReindexDemo;
