import React from 'react';
import { Database, FileText, Tag, Archive, Loader2 } from 'lucide-react';

const StatsSection = ({ stats, isLoadingStats }) => {
  if (isLoadingStats) {
    return (
      <div className="bg-white p-8 rounded-lg border shadow-sm text-center">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
        <p className="mt-2 text-gray-500">Загрузка статистики...</p>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Статистика нормативных документов от RAG сервиса */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Database className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Документы</p>
              <p className="text-2xl font-bold text-gray-900">{stats.documents || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <FileText className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Чанки</p>
              <p className="text-2xl font-bold text-gray-900">{stats.chunks || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Tag className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Векторы</p>
              <p className="text-2xl font-bold text-gray-900">{stats.vectors || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Archive className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Токены</p>
              <p className="text-2xl font-bold text-gray-900">
                {(stats.tokens || 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Информация о времени обновления */}
      {stats.timestamp && (
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="text-center">
            <p className="text-sm text-gray-500">
              <strong>Последнее обновление:</strong> {new Date(stats.timestamp).toLocaleString('ru-RU')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default StatsSection;
