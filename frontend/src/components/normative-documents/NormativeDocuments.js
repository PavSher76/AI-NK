import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Plus, 
  Database, 
  Settings, 
  FileText, 
  FileImage, 
  FileCode, 
  File 
} from 'lucide-react';

// Импортируем модули
import { filterDocuments, sortDocuments } from './utils';
import { 
  fetchDocuments, 
  fetchStats, 
  uploadDocument, 
  deleteDocument, 
  fetchDocumentTokens,
  reindexDocuments,
  startAsyncReindex,
  getReindexStatus,
  fetchSettings,
  updateSetting,
  deleteSetting
} from './api';
import StatsSection from './StatsSection';
import FiltersSection from './FiltersSection';
import DocumentsList from './DocumentsList';
import UploadModal from './UploadModal';
import AsyncReindexDemo from './AsyncReindexDemo';
import DocumentTokensModal from './DocumentTokensModal';
import IndexingStats from './IndexingStats';

const NormativeDocuments = ({ isAuthenticated, authToken, refreshTrigger, onRefreshComplete }) => {
  // Состояния для документов
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);

  // Состояния для статистики
  const [stats, setStats] = useState(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  // Состояния для поиска и фильтрации
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [sortBy, setSortBy] = useState('filename');
  const [sortDirection, setSortDirection] = useState('asc');

  // Состояния для загрузки
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [file, setFile] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('gost');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState('upload');
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Состояния для реиндексации
  const [isReindexing, setIsReindexing] = useState(false);
  const [reindexProgress, setReindexProgress] = useState(null);
  const [reindexTaskId, setReindexTaskId] = useState(null);
  const [reindexStatusInterval, setReindexStatusInterval] = useState(null);

  // Состояния для токенов
  const [selectedDocumentTokens, setSelectedDocumentTokens] = useState(null);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [selectedDocumentForTokens, setSelectedDocumentForTokens] = useState(null);

  // Состояния для настроек
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [settings, setSettings] = useState([]);
  const [isLoadingSettings, setIsLoadingSettings] = useState(false);

  // Иконки для компонентов
  const icons = {
    FileText: <FileText className="w-4 h-4" />,
    FileImage: <FileImage className="w-4 h-4" />,
    FileCode: <FileCode className="w-4 h-4" />,
    File: <File className="w-4 h-4" />
  };

  // Загрузка списка документов
  const loadDocuments = async () => {
    setIsLoading(true);
    const docs = await fetchDocuments(authToken);
    setDocuments(docs);
    setIsLoading(false);
  };

  // Загрузка статистики
  const loadStats = async () => {
    setIsLoadingStats(true);
    const statsData = await fetchStats(authToken);
    setStats(statsData);
    setIsLoadingStats(false);
  };

  // Обработка загрузки документа
  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStage('upload');
    setUploadError(null);
    setUploadSuccess(false);

    try {
      const result = await uploadDocument(file, selectedCategory, authToken, setUploadProgress);
      
      setUploadProgress(100);
      
      if (result.upload_complete && result.document_id) {
        setUploadStage('processing');
        setUploadProgress(0);
        
        // Имитируем прогресс обработки
        let processingProgress = 0;
        const processingInterval = setInterval(() => {
          processingProgress += Math.random() * 10;
          if (processingProgress >= 90) {
            processingProgress = 90;
            clearInterval(processingInterval);
          }
          setUploadProgress(processingProgress);
        }, 500);
        
        setTimeout(async () => {
          setUploadProgress(100);
          setUploadSuccess(true);
          setFile(null);
          
          // Очищаем input file
          const fileInput = document.getElementById('file-input');
          if (fileInput) fileInput.value = '';
          
          // Обновляем список документов
          await loadDocuments();
          await loadStats();
          
          clearInterval(processingInterval);
          setShowUploadModal(false);
        }, 3000);
      } else {
        setUploadSuccess(true);
        setFile(null);
        
        // Очищаем input file
        const fileInput = document.getElementById('file-input');
        if (fileInput) fileInput.value = '';
        
        // Обновляем список документов
        await loadDocuments();
        await loadStats();
        
        setIsUploading(false);
        setUploadProgress(0);
        setShowUploadModal(false);
      }
    } catch (error) {
      setUploadError(error.message);
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // Обработка удаления документа
  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот документ?')) {
      return;
    }

    const success = await deleteDocument(documentId, authToken);
    if (success) {
      await loadDocuments();
      await loadStats();
    }
  };

  // Обработка просмотра токенов документа
  const handleViewTokens = async (documentId) => {
    const document = documents.find(doc => doc.id === documentId);
    if (document) {
      setSelectedDocumentForTokens(document);
      setShowTokenModal(true);
    }
  };

  // Обработка реиндексации
  const handleReindex = async () => {
    setIsReindexing(true);
    setReindexProgress({ message: 'Запуск асинхронной реиндексации...', progress: 0 });
    
    try {
      // Запускаем асинхронную реиндексацию
      const result = await startAsyncReindex(authToken);
      
      if (result.status === 'started' && result.task_id) {
        setReindexTaskId(result.task_id);
        setReindexProgress({
          message: `Реиндексация запущена для ${result.total_documents} документов...`,
          progress: 10,
          total_documents: result.total_documents
        });
        
        // Запускаем опрос статуса
        const interval = setInterval(async () => {
          try {
            const status = await getReindexStatus(result.task_id, authToken);
            
            if (status.status === 'completed') {
              clearInterval(interval);
              setReindexProgress({
                message: status.message,
                progress: 100,
                result: status,
                completed: true
              });
              
              // Обновляем данные
              await loadDocuments();
              await loadStats();
              
              setTimeout(() => {
                setIsReindexing(false);
                setReindexProgress(null);
                setReindexTaskId(null);
                setReindexStatusInterval(null);
              }, 3000);
              
            } else if (status.status === 'error') {
              clearInterval(interval);
              setReindexProgress({
                message: 'Ошибка реиндексации',
                progress: 0,
                error: true,
                errorDetails: status.error
              });
              
              setTimeout(() => {
                setIsReindexing(false);
                setReindexProgress(null);
                setReindexTaskId(null);
                setReindexStatusInterval(null);
              }, 3000);
              
            } else {
              // Обновляем прогресс
              const progress = Math.min(90, 10 + (status.reindexed_count || 0) / (result.total_documents || 1) * 80);
              setReindexProgress({
                message: `Обработано ${status.reindexed_count || 0} из ${result.total_documents} документов...`,
                progress: progress,
                current_document: status.current_document,
                reindexed_count: status.reindexed_count,
                total_documents: result.total_documents
              });
            }
          } catch (error) {
            console.error('Error checking reindex status:', error);
          }
        }, 2000); // Проверяем каждые 2 секунды
        
        setReindexStatusInterval(interval);
        
      } else {
        setReindexProgress({
          message: result.message,
          progress: 100,
          result: result,
          completed: true
        });
        
        setTimeout(() => {
          loadDocuments();
          loadStats();
          setIsReindexing(false);
          setReindexProgress(null);
        }, 2000);
      }
      
    } catch (error) {
      setReindexProgress({
        message: 'Ошибка запуска реиндексации',
        progress: 0,
        error: true,
        errorDetails: error.message
      });
      
      setTimeout(() => {
        setIsReindexing(false);
        setReindexProgress(null);
      }, 3000);
    }
  };

  // Фильтрация и сортировка документов
  const filteredDocuments = filterDocuments(documents, searchQuery, filterCategory, filterStatus);
  const sortedDocuments = sortDocuments(filteredDocuments, sortBy, sortDirection);

  // Загрузка данных при монтировании компонента
  useEffect(() => {
    if (isAuthenticated) {
      loadDocuments();
      loadStats();
    }
  }, [isAuthenticated]);

  // Обработка обновления данных после авторизации
  useEffect(() => {
    if (refreshTrigger && isAuthenticated) {
      loadDocuments();
      loadStats();
      if (onRefreshComplete) {
        onRefreshComplete();
      }
    }
  }, [refreshTrigger, isAuthenticated, onRefreshComplete]);

  // Очистка интервала при размонтировании
  useEffect(() => {
    return () => {
      if (reindexStatusInterval) {
        clearInterval(reindexStatusInterval);
      }
    };
  }, [reindexStatusInterval]);

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
            <BookOpen className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Нормативные документы</h2>
            <p className="text-sm text-gray-500">Управление базой нормативных документов</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Добавить документ</span>
          </button>
          
          <button
            onClick={handleReindex}
            disabled={isReindexing}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Database className="w-4 h-4" />
            <span>{isReindexing ? 'Реиндексация...' : 'Реиндексация (Синхр.)'}</span>
          </button>
          
          <button
            onClick={() => setShowSettingsModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span>Настройки</span>
          </button>
        </div>
      </div>

      {/* Прогресс реиндексации */}
      {reindexProgress && (
        <div className={`p-4 rounded-lg border shadow-sm ${
          reindexProgress.error ? 'bg-red-50 border-red-200' : 
          reindexProgress.completed ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center space-x-3">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">{reindexProgress.message}</p>
              
              {/* Детали прогресса */}
              {reindexProgress.total_documents && (
                <div className="mt-2 text-sm text-gray-600">
                  <p>Всего документов: {reindexProgress.total_documents}</p>
                  {reindexProgress.reindexed_count !== undefined && (
                    <p>Обработано: {reindexProgress.reindexed_count}</p>
                  )}
                  {reindexProgress.current_document && (
                    <p>Текущий документ: {reindexProgress.current_document}</p>
                  )}
                </div>
              )}
              
              {/* Результат */}
              {reindexProgress.result && reindexProgress.completed && (
                <div className="mt-2 text-sm text-gray-600">
                  <p>Документов: {reindexProgress.result.total_documents}</p>
                  <p>Обновлено: {reindexProgress.result.reindexed_count}</p>
                  <p>Токенов: {reindexProgress.result.total_tokens?.toLocaleString()}</p>
                </div>
              )}
              
              {/* Ошибка */}
              {reindexProgress.error && reindexProgress.errorDetails && (
                <div className="mt-2 text-sm text-red-600">
                  <p>Детали ошибки: {reindexProgress.errorDetails}</p>
                </div>
              )}
            </div>
            
            {/* Иконка статуса */}
            <div className="flex-shrink-0">
              {reindexProgress.error ? (
                <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs">✕</span>
                </div>
              ) : reindexProgress.completed ? (
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs">✓</span>
                </div>
              ) : (
                <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                </div>
              )}
            </div>
          </div>
          
          {/* Прогресс-бар */}
          {!reindexProgress.error && (
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  reindexProgress.completed ? 'bg-green-600' : 'bg-blue-600'
                }`}
                style={{ width: `${reindexProgress.progress}%` }}
              ></div>
            </div>
          )}
        </div>
      )}

      {/* Статистика */}
      <StatsSection stats={stats} isLoadingStats={isLoadingStats} />

      {/* Статистика индексации */}
      <IndexingStats documents={documents} />

      {/* Демонстрация асинхронной реиндексации */}
      <AsyncReindexDemo authToken={authToken} />

      {/* Фильтры */}
      <FiltersSection
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        filterCategory={filterCategory}
        setFilterCategory={setFilterCategory}
        filterStatus={filterStatus}
        setFilterStatus={setFilterStatus}
        sortBy={sortBy}
        setSortBy={setSortBy}
        sortDirection={sortDirection}
        setSortDirection={setSortDirection}
      />

      {/* Список документов */}
      <DocumentsList
        documents={sortedDocuments}
        isLoading={isLoading}
        onViewDocument={setSelectedDocument}
        onDeleteDocument={handleDeleteDocument}
        onViewTokens={handleViewTokens}
        icons={icons}
      />

      {/* Модальное окно загрузки */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        file={file}
        setFile={setFile}
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
        isUploading={isUploading}
        uploadProgress={uploadProgress}
        uploadStage={uploadStage}
        uploadError={uploadError}
        uploadSuccess={uploadSuccess}
        onUpload={handleUpload}
        icons={icons}
      />

      {/* Модальное окно с информацией о токенах и индексах */}
      <DocumentTokensModal
        document={selectedDocumentForTokens}
        isOpen={showTokenModal}
        onClose={() => {
          setShowTokenModal(false);
          setSelectedDocumentForTokens(null);
        }}
      />
    </div>
  );
};

export default NormativeDocuments;
