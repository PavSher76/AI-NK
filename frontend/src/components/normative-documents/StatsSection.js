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
      {/* Основная статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Database className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Всего документов</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_documents || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <FileText className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Проиндексировано</p>
              <p className="text-2xl font-bold text-gray-900">{stats.indexed_documents || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Tag className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Прогресс индексации</p>
              <p className="text-2xl font-bold text-gray-900">{stats.indexing_progress || '0%'}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Archive className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Категорий</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.category_distribution ? Object.keys(stats.category_distribution).length : 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Детализированная статистика */}
      {stats.category_distribution && (
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Распределение по категориям</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(stats.category_distribution).map(([category, count]) => (
              <div key={category} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-700">{category}</span>
                <span className="text-lg font-bold text-blue-600">{count}</span>
              </div>
            ))}
          </div>
          
          {/* Дополнительная информация */}
          <div className="mt-4 space-y-3">
            {stats.total_tokens && (
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-sm text-green-800">
                  <strong>Общее количество токенов:</strong> {stats.total_tokens.toLocaleString()}
                </p>
              </div>
            )}
            {stats.collection_name && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Коллекция:</strong> {stats.collection_name}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StatsSection;
