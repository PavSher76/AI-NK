import React, { useState, useEffect } from 'react';
import { 
  X, 
  Database, 
  Cpu, 
  Hash, 
  Layers, 
  Zap, 
  BarChart3, 
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { fetchDocumentTokens } from './api';

const DocumentTokensModal = ({ document, isOpen, onClose }) => {
  const [tokensData, setTokensData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && document) {
      loadTokensData();
    }
  }, [isOpen, document]);

  const loadTokensData = async () => {
    if (!document?.id) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchDocumentTokens(document.id);
      setTokensData(data);
    } catch (err) {
      setError('Ошибка загрузки данных о токенах');
      console.error('Error loading tokens data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Заголовок */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Информация о документе
              </h2>
              <p className="text-sm text-gray-500">
                {document?.title || document?.original_filename || 'Без названия'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Содержимое */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <span className="ml-3 text-gray-600">Загрузка данных...</span>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12">
              <XCircle className="w-8 h-8 text-red-500" />
              <span className="ml-3 text-red-600">{error}</span>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Основная информация о документе */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Основная информация</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Название:</span>
                    <span className="text-sm font-medium">{document?.title || document?.original_filename || 'Без названия'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">Категория:</span>
                    <span className="text-sm font-medium">{document?.category || 'Не указана'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Дата загрузки:</span>
                    <span className="text-sm font-medium">
                      {document?.upload_date ? new Date(document.upload_date).toLocaleDateString('ru-RU') : 'Не указана'}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">Размер файла:</span>
                    <span className="text-sm font-medium">
                      {document?.file_size ? `${(document.file_size / 1024 / 1024).toFixed(2)} МБ` : 'Неизвестен'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Статистика токенов и индексов */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Статистика токенов и индексов</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Токены */}
                  <div className="bg-white p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Cpu className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-medium text-gray-900">Токены</span>
                    </div>
                    <div className="text-2xl font-bold text-blue-600">
                      {document?.token_count ? document.token_count.toLocaleString() : '0'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {document?.token_count ? 'Подсчитано' : 'Не подсчитано'}
                    </div>
                  </div>

                  {/* Чанки */}
                  <div className="bg-white p-4 rounded-lg border border-purple-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Hash className="w-5 h-5 text-purple-600" />
                      <span className="text-sm font-medium text-gray-900">Чанки</span>
                    </div>
                    <div className="text-2xl font-bold text-purple-600">
                      {document?.chunks_count ? document.chunks_count.toLocaleString() : '0'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {document?.chunks_count ? 'Создано' : 'Не создано'}
                    </div>
                  </div>

                  {/* Векторы */}
                  <div className="bg-white p-4 rounded-lg border border-orange-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Layers className="w-5 h-5 text-orange-600" />
                      <span className="text-sm font-medium text-gray-900">Векторы</span>
                    </div>
                    <div className="text-2xl font-bold text-orange-600">
                      {document?.vector_count ? document.vector_count.toLocaleString() : '0'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {document?.vector_count ? 'Индексировано' : 'Не индексировано'}
                    </div>
                  </div>

                  {/* Статус индексации */}
                  <div className="bg-white p-4 rounded-lg border border-green-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Database className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-medium text-gray-900">Индексация</span>
                    </div>
                    <div className="text-2xl font-bold text-green-600">
                      {document?.vector_indexed ? 'Да' : 'Нет'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {document?.vector_indexed ? 'Векторная БД' : 'Не в БД'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Статус обработки */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Статус обработки</h3>
                <div className="flex items-center space-x-3">
                  {getStatusIcon(document?.processing_status)}
                  <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(document?.processing_status)}`}>
                    {document?.processing_status === 'completed' ? 'Обработан' : 
                     document?.processing_status === 'processing' ? 'Обрабатывается' : 
                     document?.processing_status === 'failed' ? 'Ошибка обработки' : 'Загружен'}
                  </span>
                </div>
              </div>

              {/* Детальная информация о чанках */}
              {tokensData && tokensData.chunks && tokensData.chunks.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Детальная информация о чанках</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            ID
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Страница
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Раздел
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Подраздел
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Длина
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {tokensData.chunks.slice(0, 10).map((chunk, index) => (
                          <tr key={chunk.chunk_id || index} className="hover:bg-gray-50">
                            <td className="px-3 py-2 text-sm text-gray-900">
                              {chunk.chunk_id || index + 1}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-600">
                              {chunk.page_number || '-'}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-600">
                              {chunk.section_title || '-'}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-600">
                              {chunk.subsection_title || '-'}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-600">
                              {chunk.content ? `${chunk.content.length} символов` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {tokensData.chunks.length > 10 && (
                      <div className="mt-3 text-sm text-gray-500 text-center">
                        Показано 10 из {tokensData.chunks.length} чанков
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Дополнительная информация */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Дополнительная информация</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">ID документа:</span>
                    <span className="ml-2 font-mono text-gray-900">{document?.id}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Тип файла:</span>
                    <span className="ml-2 text-gray-900">{document?.file_type || 'Неизвестен'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Оригинальное имя:</span>
                    <span className="ml-2 text-gray-900">{document?.original_filename || 'Не указано'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Дата создания:</span>
                    <span className="ml-2 text-gray-900">
                      {document?.created_at ? new Date(document.created_at).toLocaleString('ru-RU') : 'Не указана'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Футер */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentTokensModal;
