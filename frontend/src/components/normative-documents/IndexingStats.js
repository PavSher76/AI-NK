import React from 'react';
import { 
  Database, 
  Cpu, 
  Hash, 
  Layers, 
  TrendingUp, 
  CheckCircle, 
  XCircle,
  AlertCircle
} from 'lucide-react';

const IndexingStats = ({ documents }) => {
  // Подсчитываем статистику
  const stats = React.useMemo(() => {
    if (!documents || documents.length === 0) {
      return {
        totalDocuments: 0,
        indexedDocuments: 0,
        processingDocuments: 0,
        failedDocuments: 0,
        totalTokens: 0,
        totalChunks: 0,
        totalVectors: 0,
        indexingProgress: 0
      };
    }

    const totalDocuments = documents.length;
    const indexedDocuments = documents.filter(doc => doc.vector_indexed).length;
    const processingDocuments = documents.filter(doc => doc.processing_status === 'processing').length;
    const failedDocuments = documents.filter(doc => doc.processing_status === 'failed').length;
    
    const totalTokens = documents.reduce((sum, doc) => sum + (doc.token_count || 0), 0);
    const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunks_count || 0), 0);
    const totalVectors = documents.reduce((sum, doc) => sum + (doc.vector_count || 0), 0);
    
    const indexingProgress = totalDocuments > 0 ? (indexedDocuments / totalDocuments) * 100 : 0;

    return {
      totalDocuments,
      indexedDocuments,
      processingDocuments,
      failedDocuments,
      totalTokens,
      totalChunks,
      totalVectors,
      indexingProgress
    };
  }, [documents]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'processing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
          <Database className="w-5 h-5 text-blue-600" />
          <span>Статистика индексации</span>
        </h3>
      </div>
      
      <div className="p-4">
        {/* Основные метрики */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Документы */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Database className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-900">Документы</span>
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {stats.totalDocuments.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">
              Всего загружено
            </div>
          </div>

          {/* Индексированные */}
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-sm font-medium text-gray-900">Индексированы</span>
            </div>
            <div className="text-2xl font-bold text-green-600">
              {stats.indexedDocuments.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">
              {stats.indexingProgress.toFixed(1)}% от общего
            </div>
          </div>

          {/* Обрабатываются */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <AlertCircle className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-900">Обрабатываются</span>
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {stats.processingDocuments.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">
              В процессе
            </div>
          </div>

          {/* Ошибки */}
          <div className="bg-red-50 p-4 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <XCircle className="w-5 h-5 text-red-600" />
              <span className="text-sm font-medium text-gray-900">Ошибки</span>
            </div>
            <div className="text-2xl font-bold text-red-600">
              {stats.failedDocuments.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">
              Требуют внимания
            </div>
          </div>
        </div>

        {/* Прогресс индексации */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-900">Прогресс индексации</span>
            <span className="text-sm text-gray-500">{stats.indexingProgress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-green-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${stats.indexingProgress}%` }}
            ></div>
          </div>
        </div>

        {/* Детальная статистика */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Токены */}
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <div className="flex items-center space-x-2 mb-2">
              <Cpu className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-900">Токены</span>
            </div>
            <div className="text-xl font-bold text-blue-600">
              {stats.totalTokens.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">
              {stats.totalDocuments > 0 ? `${Math.round(stats.totalTokens / stats.totalDocuments).toLocaleString()} в среднем` : '0 в среднем'}
            </div>
          </div>

          {/* Чанки */}
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <div className="flex items-center space-x-2 mb-2">
              <Hash className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-gray-900">Чанки</span>
            </div>
            <div className="text-xl font-bold text-purple-600">
              {stats.totalChunks.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">
              {stats.totalDocuments > 0 ? `${Math.round(stats.totalChunks / stats.totalDocuments).toLocaleString()} в среднем` : '0 в среднем'}
            </div>
          </div>

          {/* Векторы */}
          <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
            <div className="flex items-center space-x-2 mb-2">
              <Layers className="w-5 h-5 text-orange-600" />
              <span className="text-sm font-medium text-gray-900">Векторы</span>
            </div>
            <div className="text-xl font-bold text-orange-600">
              {stats.totalVectors.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">
              {stats.indexedDocuments > 0 ? `${Math.round(stats.totalVectors / stats.indexedDocuments).toLocaleString()} в среднем` : '0 в среднем'}
            </div>
          </div>
        </div>

        {/* Статусы документов */}
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Статусы документов</h4>
          <div className="space-y-2">
            {documents && documents.length > 0 && (
              <>
                {documents.filter(doc => doc.processing_status === 'completed').length > 0 && (
                  <div className="flex items-center justify-between p-2 bg-green-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-gray-900">Обработаны</span>
                    </div>
                    <span className="text-sm font-medium text-green-600">
                      {documents.filter(doc => doc.processing_status === 'completed').length}
                    </span>
                  </div>
                )}
                
                {documents.filter(doc => doc.processing_status === 'processing').length > 0 && (
                  <div className="flex items-center justify-between p-2 bg-blue-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 text-blue-600" />
                      <span className="text-sm text-gray-900">Обрабатываются</span>
                    </div>
                    <span className="text-sm font-medium text-blue-600">
                      {documents.filter(doc => doc.processing_status === 'processing').length}
                    </span>
                  </div>
                )}
                
                {documents.filter(doc => doc.processing_status === 'failed').length > 0 && (
                  <div className="flex items-center justify-between p-2 bg-red-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <XCircle className="w-4 h-4 text-red-600" />
                      <span className="text-sm text-gray-900">Ошибки</span>
                    </div>
                    <span className="text-sm font-medium text-red-600">
                      {documents.filter(doc => doc.processing_status === 'failed').length}
                    </span>
                  </div>
                )}
                
                {documents.filter(doc => !doc.processing_status || doc.processing_status === 'uploaded').length > 0 && (
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Database className="w-4 h-4 text-gray-600" />
                      <span className="text-sm text-gray-900">Загружены</span>
                    </div>
                    <span className="text-sm font-medium text-gray-600">
                      {documents.filter(doc => !doc.processing_status || doc.processing_status === 'uploaded').length}
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default IndexingStats;
