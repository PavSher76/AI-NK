import React, { useState, useEffect } from 'react';
import { getDefaultNormcontrolPrompt } from '../utils/settings';
import { 
  FileText, 
  Upload, 
  Download, 
  Trash2, 
  Search, 
  Database, 
  File, 
  FileImage, 
  FileCode,
  Loader2,
  AlertCircle,
  CheckCircle,
  Plus,
  Edit,
  Eye,
  BookOpen,
  Archive,
  Tag,
  Calendar,
  User,
  RefreshCw,
  Hash,
  BarChart3,
  Settings
} from 'lucide-react';

const NormativeDocuments = ({ isAuthenticated, authToken, refreshTrigger, onRefreshComplete }) => {
  console.log('🔍 [DEBUG] NormativeDocuments.js: Component rendered');

  // Состояния для загрузки документов
  const [file, setFile] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('gost'); // По умолчанию ГОСТ
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Состояния для управления документами
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Состояния для поиска и фильтрации
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [sortBy, setSortBy] = useState('upload_date');

  // Состояния для статистики
  const [stats, setStats] = useState(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  
  // Состояния для токенов и реиндексации
  const [isReindexing, setIsReindexing] = useState(false);
  const [reindexProgress, setReindexProgress] = useState(null);
  const [selectedDocumentTokens, setSelectedDocumentTokens] = useState(null);
  const [showTokenModal, setShowTokenModal] = useState(false);
  
  // Состояния для настроек
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [settings, setSettings] = useState([]);
  const [isLoadingSettings, setIsLoadingSettings] = useState(false);
  const [settingsError, setSettingsError] = useState(null);

  // Категории нормативных документов
  const categories = [
    { value: 'gost', label: 'ГОСТ', color: 'bg-red-100 text-red-800' },
    { value: 'sp', label: 'СП', color: 'bg-blue-100 text-blue-800' },
    { value: 'snip', label: 'СНиП', color: 'bg-green-100 text-green-800' },
    { value: 'tr', label: 'ТР', color: 'bg-purple-100 text-purple-800' },
    { value: 'corporate', label: 'Корпоративные', color: 'bg-orange-100 text-orange-800' },
    { value: 'other', label: 'Прочие', color: 'bg-gray-100 text-gray-800' }
  ];

  // Статусы документов
  const statuses = [
    { value: 'uploaded', label: 'Загружен', color: 'bg-blue-100 text-blue-800' },
    { value: 'processing', label: 'Обрабатывается', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'indexed', label: 'Проиндексирован', color: 'bg-green-100 text-green-800' },
    { value: 'error', label: 'Ошибка', color: 'bg-red-100 text-red-800' }
  ];

  // Поддерживаемые форматы файлов
  const supportedFormats = [
    { ext: 'pdf', name: 'PDF документ', icon: <FileText className="w-4 h-4" /> },
    { ext: 'docx', name: 'Word документ', icon: <FileText className="w-4 h-4" /> },
    { ext: 'dwg', name: 'AutoCAD чертеж', icon: <FileImage className="w-4 h-4" /> },
    { ext: 'ifc', name: 'IFC модель', icon: <FileCode className="w-4 h-4" /> },
    { ext: 'txt', name: 'Текстовый файл', icon: <FileText className="w-4 h-4" /> }
  ];

  // Отладочные логи для отслеживания изменений состояния
  useEffect(() => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: documents state changed:', documents.length, 'documents');
  }, [documents]);

  useEffect(() => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: settings state changed:', settings);
  }, [settings]);

  useEffect(() => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: stats state changed:', stats);
  }, [stats]);

  // Загрузка списка документов
  const fetchDocuments = async () => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: fetchDocuments started');
    setIsLoading(true);
    try {
      const response = await fetch('/api/documents', {
      headers: {
        'Authorization': 'Bearer test-token'
      }
    });
      console.log('🔍 [DEBUG] NormativeDocuments.js: fetchDocuments response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('🔍 [DEBUG] NormativeDocuments.js: fetchDocuments success, documents count:', data.length);
        setDocuments(data.documents || data);
      } else {
        console.error('🔍 [DEBUG] NormativeDocuments.js: fetchDocuments failed with status:', response.status);
        setDocuments([]);
      }
    } catch (err) {
      console.error('🔍 [DEBUG] NormativeDocuments.js: fetchDocuments error:', err);
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Загрузка статистики
  const fetchStats = async () => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: fetchStats started');
    setIsLoadingStats(true);
    try {
      const response = await fetch('/api/rag/stats', {
        headers: {
          'Authorization': 'Bearer test-token'
        }
      });
      console.log('🔍 [DEBUG] NormativeDocuments.js: fetchStats response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('🔍 [DEBUG] NormativeDocuments.js: fetchStats success:', data);
        console.log('🔍 [DEBUG] NormativeDocuments.js: Setting stats to:', data);
        setStats(data);
      } else {
        console.warn('🔍 [DEBUG] NormativeDocuments.js: fetchStats failed with status:', response.status);
        // Если статистика недоступна, устанавливаем базовые значения
        setStats({
          total_documents: documents.length,
          indexed_documents: 0,
          indexing_progress: '0%',
          category_distribution: {},
          collection_name: 'N/A'
        });
      }
    } catch (err) {
      console.error('🔍 [DEBUG] NormativeDocuments.js: fetchStats error:', err);
      // Устанавливаем базовые значения при ошибке
      setStats({
        total_documents: documents.length,
        indexed_documents: 0,
        indexing_progress: '0%',
        category_distribution: {},
        collection_name: 'N/A'
      });
    } finally {
      setIsLoadingStats(false);
    }
  };

  // Реиндексация документов
  const reindexDocuments = async () => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: reindexDocuments started');
    setIsReindexing(true);
    setReindexProgress({ message: 'Начинаем реиндексацию...', progress: 0 });
    
    try {
      const response = await fetch('/api/reindex-documents', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test-token',
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        setReindexProgress({
          message: result.message,
          progress: 100,
          result: result
        });
        
        // Обновляем список документов после реиндексации
        setTimeout(() => {
          fetchDocuments();
          fetchStats();
        }, 1000);
      } else {
        setReindexProgress({
          message: 'Ошибка реиндексации',
          progress: 0,
          error: true
        });
      }
    } catch (err) {
      console.error('🔍 [DEBUG] NormativeDocuments.js: reindexDocuments error:', err);
      setReindexProgress({
        message: 'Ошибка реиндексации: ' + err.message,
        progress: 0,
        error: true
      });
    } finally {
      setTimeout(() => {
        setIsReindexing(false);
        setReindexProgress(null);
      }, 3000);
    }
  };

  // Получение информации о токенах документа
  const fetchDocumentTokens = async (documentId) => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: fetchDocumentTokens started for ID:', documentId);
    try {
      const response = await fetch(`/api/documents/${documentId}/tokens`, {
        headers: {
          'Authorization': 'Bearer test-token'
        }
      });
      console.log('🔍 [DEBUG] NormativeDocuments.js: fetchDocumentTokens response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        setSelectedDocumentTokens(data);
        setShowTokenModal(true);
      } else {
        console.error('🔍 [DEBUG] NormativeDocuments.js: fetchDocumentTokens failed with status:', response.status);
      }
    } catch (err) {
      console.error('🔍 [DEBUG] NormativeDocuments.js: fetchDocumentTokens error:', err);
    }
  };

  // Загрузка настроек системы
  const fetchSettings = async () => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: fetchSettings started');
    setIsLoadingSettings(true);
    setSettingsError(null);
    try {
      const response = await fetch('/api/settings', {
        headers: {
          'Authorization': 'Bearer test-token'
        }
      });
      console.log('🔍 [DEBUG] NormativeDocuments.js: fetchSettings response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('🔍 [DEBUG] NormativeDocuments.js: fetchSettings success:', data);
        setSettings(data.settings || []);
      } else {
        setSettingsError('Ошибка загрузки настроек');
      }
    } catch (err) {
      console.error('🔍 [DEBUG] NormativeDocuments.js: fetchSettings error:', err);
      setSettingsError('Ошибка загрузки настроек');
    } finally {
      setIsLoadingSettings(false);
    }
  };

  // Обновление настройки
  const updateSetting = async (settingKey, newValue) => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: updateSetting started:', { settingKey, newValue });
    
    try {
      // Сначала пытаемся обновить существующую настройку
      let response = await fetch(`/api/settings/${settingKey}`, {
        method: 'PUT',
        headers: {
          'Authorization': 'Bearer test-token',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ setting_value: newValue })
      });
      
      // Если настройка не найдена, создаем новую
      if (response.status === 404) {
        response = await fetch('/api/settings', {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            setting_key: settingKey,
            setting_value: newValue,
            setting_type: 'text',
            setting_description: settingKey === 'normcontrol_prompt' ? 'Промпт для проверки нормоконтроля' : 'Системная настройка'
          })
        });
      }
      
      if (response.ok) {
        // Обновляем локальное состояние
        setSettings(prevSettings => {
          const existingSetting = prevSettings.find(s => s.setting_key === settingKey);
          if (existingSetting) {
            return prevSettings.map(setting => 
              setting.setting_key === settingKey 
                ? { ...setting, setting_value: newValue }
                : setting
            );
          } else {
            return [...prevSettings, {
              setting_key: settingKey,
              setting_value: newValue,
              setting_type: 'text',
              setting_description: settingKey === 'normcontrol_prompt' ? 'Промпт для проверки нормоконтроля' : 'Системная настройка'
            }];
          }
        });
        return true;
      } else {
        console.error('🔍 [DEBUG] NormativeDocuments.js: updateSetting failed with status:', response.status);
        return false;
      }
    } catch (err) {
      console.error('🔍 [DEBUG] NormativeDocuments.js: updateSetting error:', err);
      return false;
    }
  };

  // Удаление настройки
  const deleteSetting = async (settingKey) => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: deleteSetting started:', { settingKey });
    
    if (!window.confirm(`Вы уверены, что хотите удалить настройку "${settingKey}"?`)) {
      console.log('🔍 [DEBUG] NormativeDocuments.js: deleteSetting cancelled by user');
      return false;
    }
    
    try {
      const response = await fetch(`/api/settings/${settingKey}`, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer test-token',
        }
      });
      
      if (response.ok) {
        // Удаляем из локального состояния
        setSettings(prevSettings => 
          prevSettings.filter(setting => setting.setting_key !== settingKey)
        );
        console.log('🔍 [DEBUG] NormativeDocuments.js: deleteSetting successful');
        return true;
      } else {
        console.error('🔍 [DEBUG] NormativeDocuments.js: deleteSetting failed with status:', response.status);
        return false;
      }
    } catch (err) {
      console.error('🔍 [DEBUG] NormativeDocuments.js: deleteSetting error:', err);
      return false;
    }
  };

  // Открытие модального окна настроек
  const openSettingsModal = async () => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: openSettingsModal triggered');
    setShowSettingsModal(true);
    await fetchSettings();
  };

  // Обработка выбора файла
  const handleFileChange = (e) => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: handleFileChange triggered');
    const selectedFile = e.target.files[0];
    if (!selectedFile) {
      console.log('🔍 [DEBUG] NormativeDocuments.js: handleFileChange - no file selected');
      return;
    }

    // Проверяем формат файла
    const fileExtension = selectedFile.name.split('.').pop().toLowerCase();
    const isSupported = supportedFormats.some(format => format.ext === fileExtension);

    if (isSupported) {
      setFile(selectedFile);
      setUploadError(null);
    } else {
      setUploadError('Неподдерживаемый формат файла');
      setFile(null);
    }
  };

  // Загрузка документа
  const uploadDocument = async () => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: uploadDocument started');
    if (!file) {
      console.log('🔍 [DEBUG] NormativeDocuments.js: uploadDocument - no file selected');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', selectedCategory); // Добавляем категорию

      const response = await fetch('/api/upload', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test-token'
        },
        body: formData
      });

      console.log('🔍 [DEBUG] NormativeDocuments.js: uploadDocument response status:', response.status);

      if (response.ok) {
        const result = await response.json();
        setUploadSuccess(true);
        setFile(null);
        // Очищаем input file
        const fileInput = document.getElementById('file-input');
        if (fileInput) fileInput.value = '';
        
        // Обновляем список документов
        await fetchDocuments();
        await fetchStats();
      } else {
        throw new Error(`Ошибка загрузки: ${response.status}`);
      }
    } catch (err) {
      setUploadError(`Ошибка загрузки: ${err.message}`);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // Удаление документа
  const deleteDocument = async (documentId) => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: deleteDocument started for ID:', documentId);
    if (!window.confirm('Вы уверены, что хотите удалить этот документ?')) {
      console.log('🔍 [DEBUG] NormativeDocuments.js: deleteDocument cancelled by user');
      return;
    }

    try {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer test-token'
        }
      });

      console.log('🔍 [DEBUG] NormativeDocuments.js: deleteDocument response status:', response.status);

      if (response.ok) {
        await fetchDocuments();
        await fetchStats();
      }
    } catch (err) {
      console.error('🔍 [DEBUG] NormativeDocuments.js: deleteDocument error:', err);
    }
  };

  // Получение иконки типа файла
  const getFileIcon = (fileType) => {
    const format = supportedFormats.find(f => f.ext === fileType.toLowerCase());
    return format ? format.icon : <File className="w-4 h-4" />;
  };

  // Получение названия типа файла
  const getFileTypeName = (fileType) => {
    const format = supportedFormats.find(f => f.ext === fileType.toLowerCase());
    return format ? format.name : fileType.toUpperCase();
  };

  // Получение категории документа
  const getCategoryInfo = (category) => {
    return categories.find(c => c.value === category) || categories[categories.length - 1];
  };

  // Получение статуса документа
  const getStatusInfo = (status) => {
    return statuses.find(s => s.value === status) || statuses[0];
  };

  // Фильтрация документов
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.file_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !filterCategory || doc.category === filterCategory;
    const matchesStatus = !filterStatus || doc.processing_status === filterStatus;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  // Сортировка документов
  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    switch (sortBy) {
      case 'upload_date':
        return new Date(b.upload_date) - new Date(a.upload_date);
      case 'filename':
        return a.original_filename.localeCompare(b.original_filename);
      case 'file_size':
        return b.file_size - a.file_size;
      case 'category':
        return a.category.localeCompare(b.category);
      default:
        return 0;
    }
  });

  // Загрузка данных при монтировании компонента
  useEffect(() => {
    console.log('🔍 [DEBUG] NormativeDocuments.js: Initial useEffect triggered');
    const loadData = async () => {
      await fetchDocuments();
      await fetchStats();
    };
    loadData();
  }, []);

  // Обработка обновления данных после авторизации
  useEffect(() => {
    if (refreshTrigger && isAuthenticated) {
      console.log('🔍 [DEBUG] NormativeDocuments.js: refreshTrigger triggered, fetching data');
      const loadData = async () => {
        console.log('🔍 [DEBUG] NormativeDocuments.js: Обновление данных нормативных документов после авторизации...');
        await fetchDocuments();
        await fetchStats();
        if (onRefreshComplete) {
          onRefreshComplete();
        }
      };
      loadData();
    }
  }, [refreshTrigger, isAuthenticated, onRefreshComplete]);

  useEffect(() => {
    if (showSettingsModal) {
      console.log('🔍 [DEBUG] NormativeDocuments.js: Settings modal opened, fetching settings');
      fetchSettings();
    }
  }, [showSettingsModal]);

  console.log('🔍 [DEBUG] NormativeDocuments.js: Rendering with state:', {
    documentsCount: documents.length,
    isLoading,
    error,
    showSettings: showSettingsModal,
    settingsCount: settings.length,
    stats
  });

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
            onClick={reindexDocuments}
            disabled={isReindexing}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isReindexing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Database className="w-4 h-4" />
            )}
            <span>{isReindexing ? 'Реиндексация...' : 'Реиндексация'}</span>
          </button>
          
          <button
            onClick={openSettingsModal}
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
          reindexProgress.error ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center space-x-3">
            {reindexProgress.error ? (
              <AlertCircle className="w-5 h-5 text-red-600" />
            ) : (
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            )}
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">{reindexProgress.message}</p>
              {reindexProgress.result && (
                <div className="mt-2 text-sm text-gray-600">
                  <p>Документов: {reindexProgress.result.total_documents}</p>
                  <p>Обновлено: {reindexProgress.result.updated_documents}</p>
                  <p>Токенов: {reindexProgress.result.new_total_tokens?.toLocaleString()}</p>
                </div>
              )}
            </div>
          </div>
          {!reindexProgress.error && (
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${reindexProgress.progress}%` }}
              ></div>
            </div>
          )}
        </div>
      )}

      {/* Статистика */}
      {console.log('🔍 [DEBUG] NormativeDocuments.js: Rendering stats section with:', { isLoadingStats, stats })}
      {isLoadingStats ? (
        <div className="bg-white p-8 rounded-lg border shadow-sm text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
          <p className="mt-2 text-gray-500">Загрузка статистики...</p>
        </div>
      ) : stats ? (
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
                <p className="text-2xl font-bold text-gray-900">{stats.category_distribution ? Object.keys(stats.category_distribution).length : 0}</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Детализированная статистика */}
      {stats && stats.category_distribution && (
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
          {stats.collection_name && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Коллекция:</strong> {stats.collection_name}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Фильтры и поиск */}
      <div className="bg-white p-4 rounded-lg border shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Поиск</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Поиск по названию..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Категория</label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Все категории</option>
              {categories.map(category => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Статус</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Все статусы</option>
              {statuses.map(status => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Сортировка</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="upload_date">По дате загрузки</option>
              <option value="filename">По названию</option>
              <option value="file_size">По размеру</option>
              <option value="category">По категории</option>
            </select>
          </div>
        </div>
      </div>

      {/* Список документов */}
      <div className="bg-white rounded-lg border shadow-sm">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Документы ({sortedDocuments.length})
          </h3>
        </div>
        
        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
            <p className="mt-2 text-gray-500">Загрузка документов...</p>
          </div>
        ) : sortedDocuments.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 mx-auto text-gray-400" />
            <p className="mt-2 text-gray-500">Документы не найдены</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {sortedDocuments.map((doc) => (
              <div key={doc.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center justify-center w-10 h-10 bg-gray-100 rounded-lg">
                      {getFileIcon(doc.file_type)}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-medium text-gray-900">{doc.original_filename}</h4>
                        <span className={`px-2 py-1 rounded-full text-xs ${getCategoryInfo(doc.category).color}`}>
                          {getCategoryInfo(doc.category).label}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs ${getStatusInfo(doc.processing_status).color}`}>
                          {getStatusInfo(doc.processing_status).label}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{getFileTypeName(doc.file_type)}</span>
                        <span>{(doc.file_size / 1024 / 1024).toFixed(2)} МБ</span>
                        <span className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{new Date(doc.upload_date).toLocaleDateString('ru-RU')}</span>
                        </span>
                        {doc.token_count > 0 && (
                          <span className="flex items-center space-x-1 text-purple-600">
                            <Hash className="w-3 h-3" />
                            <span>{doc.token_count.toLocaleString()} токенов</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedDocument(doc)}
                      className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                      title="Просмотр"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    
                    {doc.token_count > 0 && (
                      <button
                        onClick={() => fetchDocumentTokens(doc.id)}
                        className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
                        title="Информация о токенах"
                      >
                        <BarChart3 className="w-4 h-4" />
                      </button>
                    )}
                    
                    <button
                      onClick={() => deleteDocument(doc.id)}
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
        )}
      </div>

      {/* Модальное окно загрузки */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Загрузка документа</h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {/* Выбор файла */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Выберите файл
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <input
                    id="file-input"
                    type="file"
                    onChange={handleFileChange}
                    accept=".pdf,.docx,.dwg,.ifc,.txt"
                    className="hidden"
                  />
                  <label htmlFor="file-input" className="cursor-pointer">
                    <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                    <p className="text-sm text-gray-600">
                      {file ? file.name : 'Нажмите для выбора файла'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Поддерживаются: PDF, DOCX, DWG, IFC, TXT
                    </p>
                  </label>
                </div>
              </div>
              
              {/* Выбор категории */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Категория документа
                </label>
                <select 
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {categories.map(category => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Ошибки */}
              {uploadError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    <span className="text-sm text-red-800">{uploadError}</span>
                  </div>
                </div>
              )}
              
              {/* Успех */}
              {uploadSuccess && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-sm text-green-800">Документ успешно загружен</span>
                  </div>
                </div>
              )}
              
              {/* Прогресс */}
              {isUploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Загрузка...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}
              
              {/* Кнопки */}
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Отмена
                </button>
                <button
                  onClick={uploadDocument}
                  disabled={!file || isUploading}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isUploading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Загрузка...</span>
                    </div>
                  ) : (
                    'Загрузить'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно просмотра документа */}
      {selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Детали документа</h3>
              <button
                onClick={() => setSelectedDocument(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Название файла</label>
                  <p className="text-sm text-gray-900">{selectedDocument.original_filename}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Тип файла</label>
                  <p className="text-sm text-gray-900">{getFileTypeName(selectedDocument.file_type)}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Размер</label>
                  <p className="text-sm text-gray-900">{(selectedDocument.file_size / 1024 / 1024).toFixed(2)} МБ</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Дата загрузки</label>
                  <p className="text-sm text-gray-900">
                    {new Date(selectedDocument.upload_date).toLocaleString('ru-RU')}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Категория</label>
                  <span className={`px-2 py-1 rounded-full text-xs ${getCategoryInfo(selectedDocument.category).color}`}>
                    {getCategoryInfo(selectedDocument.category).label}
                  </span>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Статус</label>
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusInfo(selectedDocument.processing_status).color}`}>
                    {getStatusInfo(selectedDocument.processing_status).label}
                  </span>
                </div>
              </div>
              
              <div className="pt-4 border-t border-gray-200">
                <div className="flex space-x-3">
                  <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    <Download className="w-4 h-4" />
                    <span>Скачать</span>
                  </button>
                  
                  <button className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                    <Edit className="w-4 h-4" />
                    <span>Редактировать</span>
                  </button>
                  
                  <button 
                    onClick={() => deleteDocument(selectedDocument.id)}
                    className="flex items-center space-x-2 px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Удалить</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно информации о токенах */}
      {showTokenModal && selectedDocumentTokens && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Информация о токенах: {selectedDocumentTokens.document.original_filename}
              </h3>
              <button
                onClick={() => setShowTokenModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Общая информация */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Hash className="w-5 h-5 text-blue-600" />
                    <div>
                      <p className="text-sm text-gray-500">Всего токенов</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {selectedDocumentTokens.token_statistics.total_tokens.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-5 h-5 text-green-600" />
                    <div>
                      <p className="text-sm text-gray-500">Элементов</p>
                      <p className="text-2xl font-bold text-green-600">
                        {selectedDocumentTokens.token_statistics.elements_count}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="w-5 h-5 text-purple-600" />
                    <div>
                      <p className="text-sm text-gray-500">Размер файла</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {(selectedDocumentTokens.document.file_size / 1024 / 1024).toFixed(2)} МБ
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Токены по типам элементов */}
              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Токены по типам элементов</h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  {Object.entries(selectedDocumentTokens.token_statistics.by_type).map(([type, data]) => (
                    <div key={type} className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0">
                      <div className="flex items-center space-x-2">
                        <span className="capitalize font-medium text-gray-700">{type}</span>
                        <span className="text-sm text-gray-500">({data.count} элементов)</span>
                      </div>
                      <span className="font-semibold text-purple-600">
                        {data.tokens.toLocaleString()} токенов
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Токены по страницам */}
              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Токены по страницам</h4>
                <div className="bg-gray-50 p-4 rounded-lg max-h-60 overflow-y-auto">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(selectedDocumentTokens.token_statistics.by_page)
                      .sort(([a], [b]) => parseInt(a) - parseInt(b))
                      .map(([page, data]) => (
                        <div key={page} className="bg-white p-3 rounded border">
                          <div className="text-center">
                            <p className="text-sm font-medium text-gray-700">Страница {page}</p>
                            <p className="text-lg font-bold text-purple-600">{data.tokens.toLocaleString()}</p>
                            <p className="text-xs text-gray-500">{data.count} элементов</p>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно настроек */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">
                Настройки системы
              </h3>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            {isLoadingSettings ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <span className="ml-2 text-gray-600">Загрузка настроек...</span>
              </div>
            ) : settingsError ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <span className="ml-2 text-red-800">{settingsError}</span>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {settings.map((setting) => (
                  <div key={setting.setting_key} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="text-md font-medium text-gray-900 mb-1">
                          {setting.setting_description}
                        </h4>
                        <p className="text-sm text-gray-500">
                          Ключ: <code className="bg-gray-100 px-1 rounded">{setting.setting_key}</code>
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        setting.setting_type === 'text' ? 'bg-blue-100 text-blue-800' :
                        setting.setting_type === 'boolean' ? 'bg-green-100 text-green-800' :
                        setting.setting_type === 'number' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {setting.setting_type}
                      </span>
                    </div>
                    
                    <div className="space-y-3">
                      {setting.setting_type === 'text' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Значение
                          </label>
                          <textarea
                            value={setting.setting_value || ''}
                            onChange={(e) => {
                              const newSettings = settings.map(s => 
                                s.setting_key === setting.setting_key 
                                  ? { ...s, setting_value: e.target.value }
                                  : s
                              );
                              setSettings(newSettings);
                            }}
                            rows={4}
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                            placeholder="Введите значение настройки..."
                          />
                        </div>
                      )}
                      
                      {setting.setting_type === 'boolean' && (
                        <div>
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={setting.setting_value === 'true'}
                              onChange={(e) => {
                                const newSettings = settings.map(s => 
                                  s.setting_key === setting.setting_key 
                                    ? { ...s, setting_value: e.target.checked.toString() }
                                    : s
                                );
                                setSettings(newSettings);
                              }}
                              className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <span className="text-sm text-gray-700">
                              {setting.setting_value === 'true' ? 'Включено' : 'Отключено'}
                            </span>
                          </label>
                        </div>
                      )}
                      
                      {setting.setting_type === 'number' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Значение
                          </label>
                          <input
                            type="number"
                            value={setting.setting_value || ''}
                            onChange={(e) => {
                              const newSettings = settings.map(s => 
                                s.setting_key === setting.setting_key 
                                  ? { ...s, setting_value: e.target.value }
                                  : s
                              );
                              setSettings(newSettings);
                            }}
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Введите числовое значение..."
                          />
                        </div>
                      )}
                      
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={async () => {
                            const success = await deleteSetting(setting.setting_key);
                            if (success) {
                              alert('Настройка удалена успешно!');
                            } else {
                              alert('Ошибка удаления настройки');
                            }
                          }}
                          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-1"
                          title="Удалить настройку"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Удалить</span>
                        </button>
                        <button
                          onClick={async () => {
                            const success = await updateSetting(setting.setting_key, setting.setting_value);
                            if (success) {
                              // Показываем уведомление об успехе
                              alert('Настройка обновлена успешно!');
                            } else {
                              alert('Ошибка обновления настройки');
                            }
                          }}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          Сохранить
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Настройка промпта для нормоконтроля */}
                <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="text-md font-medium text-gray-900 mb-1">
                        Промпт для проверки нормоконтроля
                      </h4>
                      <p className="text-sm text-gray-500">
                        Системный промпт для LLM при проведении проверки нормоконтроля документов
                      </p>
                    </div>
                    <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                      prompt
                    </span>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Промпт для LLM
                      </label>
                      <textarea
                        value={settings.find(s => s.setting_key === 'normcontrol_prompt')?.setting_value || getDefaultNormcontrolPrompt()}
                        onChange={(e) => {
                          const newSettings = settings.map(s => 
                            s.setting_key === 'normcontrol_prompt' 
                              ? { ...s, setting_value: e.target.value }
                              : s
                          );
                          // Если настройки нет, добавляем её
                          if (!newSettings.find(s => s.setting_key === 'normcontrol_prompt')) {
                            newSettings.push({
                              setting_key: 'normcontrol_prompt',
                              setting_value: e.target.value,
                              setting_type: 'text',
                              setting_description: 'Промпт для проверки нормоконтроля'
                            });
                          }
                          setSettings(newSettings);
                        }}
                        rows={8}
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        placeholder="Введите промпт для LLM..."
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Используйте переменные: {'{document_content}'} - содержимое документа, {'{normative_docs}'} - нормативные документы
                      </p>
                    </div>
                    
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={async () => {
                          const promptValue = settings.find(s => s.setting_key === 'normcontrol_prompt')?.setting_value || getDefaultNormcontrolPrompt();
                          const success = await updateSetting('normcontrol_prompt', promptValue);
                          if (success) {
                            alert('Промпт для нормоконтроля сохранен успешно!');
                          } else {
                            alert('Ошибка сохранения промпта');
                          }
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Сохранить промпт
                      </button>
                      <button
                        onClick={() => {
                          const defaultPrompt = getDefaultNormcontrolPrompt();
                          const newSettings = settings.map(s => 
                            s.setting_key === 'normcontrol_prompt' 
                              ? { ...s, setting_value: defaultPrompt }
                              : s
                          );
                          if (!newSettings.find(s => s.setting_key === 'normcontrol_prompt')) {
                            newSettings.push({
                              setting_key: 'normcontrol_prompt',
                              setting_value: defaultPrompt,
                              setting_type: 'text',
                              setting_description: 'Промпт для проверки нормоконтроля'
                            });
                          }
                          setSettings(newSettings);
                        }}
                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                      >
                        Сбросить к умолчанию
                      </button>
                    </div>
                  </div>
                </div>

                {settings.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    Настройки не найдены
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NormativeDocuments;
