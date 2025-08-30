import React from 'react';
import { 
  Eye, 
  Trash2, 
  BarChart3, 
  Calendar, 
  Hash, 
  Loader2, 
  FileText,
  Database,
  Cpu,
  Layers,
  Zap
} from 'lucide-react';
import { 
  getFileIcon, 
  getFileTypeName, 
  getCategoryInfo, 
  getStatusInfo 
} from './utils';

const DocumentsList = ({ 
  documents, 
  isLoading, 
  onViewDocument, 
  onDeleteDocument, 
  onViewTokens,
  icons 
}) => {
  if (isLoading) {
    return (
      <div className="bg-white p-8 rounded-lg border shadow-sm text-center">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
        <p className="mt-2 text-gray-500">Загрузка документов...</p>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="bg-white p-8 rounded-lg border shadow-sm text-center">
        <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-500">Документы не найдены</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">
          Документы ({documents.length})
        </h3>
      </div>
      
      <div className="divide-y divide-gray-200">
        {documents.map((doc) => (
          <div key={doc.id} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center justify-center w-10 h-10 bg-gray-100 rounded-lg">
                  {getFileIcon(doc.file_type, icons)}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h4 className="font-medium text-gray-900">
                      {doc.title || doc.original_filename || 'Без названия'}
                    </h4>
                    <span className={`px-2 py-1 rounded-full text-xs ${getCategoryInfo(doc.category || 'other').color}`}>
                      {getCategoryInfo(doc.category || 'other').label}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusInfo(doc.status || doc.processing_status || 'uploaded').color}`}>
                      {getStatusInfo(doc.status || doc.processing_status || 'uploaded').label}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>{getFileTypeName(doc.file_type || 'pdf')}</span>
                    <span>
                      {doc.chunks_count ? `${doc.chunks_count} чанков` : (doc.file_size ? `${(doc.file_size / 1024 / 1024).toFixed(2)} МБ` : 'Размер неизвестен')}
                    </span>
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3 h-3" />
                      <span>
                        {doc.upload_date ? new Date(doc.upload_date).toLocaleDateString('ru-RU') : 'Дата неизвестна'}
                      </span>
                    </span>
                  </div>
                  
                  {/* Информация об индексах и токенах */}
                  <div className="mt-2 flex items-center space-x-6 text-xs">
                    {/* Токены */}
                    <div className="flex items-center space-x-1 text-blue-600">
                      <Cpu className="w-3 h-3" />
                      <span>
                        {doc.token_count ? `${doc.token_count.toLocaleString()} токенов` : 'Токены не подсчитаны'}
                      </span>
                    </div>
                    
                    {/* Чанки */}
                    {doc.chunks_count > 0 && (
                      <div className="flex items-center space-x-1 text-purple-600">
                        <Hash className="w-3 h-3" />
                        <span>{doc.chunks_count.toLocaleString()} чанков</span>
                      </div>
                    )}
                    
                    {/* Индексация */}
                    <div className="flex items-center space-x-1 text-green-600">
                      <Database className="w-3 h-3" />
                      <span>
                        {doc.vector_indexed ? 'Индексирован' : 'Не индексирован'}
                      </span>
                    </div>
                    
                    {/* Векторы */}
                    {doc.vector_count && (
                      <div className="flex items-center space-x-1 text-orange-600">
                        <Layers className="w-3 h-3" />
                        <span>{doc.vector_count.toLocaleString()} векторов</span>
                      </div>
                    )}
                    
                    {/* Статус обработки */}
                    <div className="flex items-center space-x-1 text-gray-600">
                      <Zap className="w-3 h-3" />
                      <span>
                        {doc.processing_status === 'completed' ? 'Обработан' : 
                         doc.processing_status === 'processing' ? 'Обрабатывается' : 
                         doc.processing_status === 'failed' ? 'Ошибка' : 'Загружен'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onViewDocument(doc)}
                  className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                  title="Просмотр"
                >
                  <Eye className="w-4 h-4" />
                </button>
                
                {doc.chunks_count > 0 && (
                  <button
                    onClick={() => onViewTokens(doc.id)}
                    className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
                    title="Информация о чанках"
                  >
                    <BarChart3 className="w-4 h-4" />
                  </button>
                )}
                
                <button
                  onClick={() => onDeleteDocument(doc.id)}
                  className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                  title="Удалить"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DocumentsList;
