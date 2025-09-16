import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Download,
  Eye,
  Clock,
  Loader2,
  RefreshCw,
  AlertCircle,
  Settings,
  BarChart3,
  Filter,
  Search,
  ChevronDown,
  ChevronUp,
  Info,
  Warning,
  AlertOctagon,
  Trash2,
  RotateCcw
} from 'lucide-react';
import { useNormControl2 } from '../hooks/useNormControl2';

const NormControl2PanelV2 = ({ isAuthenticated, authToken }) => {
  // Используем хук для работы с API
  const {
    documents,
    loading,
    error,
    validationResults,
    statistics,
    settings,
    validateDocument,
    loadValidationResult,
    loadDocuments,
    loadStatistics,
    loadSettings,
    saveSettings,
    deleteDocument,
    revalidateDocument,
    exportResults,
    setError,
    clearError
  } = useNormControl2(authToken);

  // Локальное состояние для UI
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [success, setSuccess] = useState(null);
  const [expandedResults, setExpandedResults] = useState({});
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [localSettings, setLocalSettings] = useState({
    autoValidation: true,
    saveResults: true,
    notificationEnabled: true
  });

  // Синхронизация настроек
  useEffect(() => {
    if (settings && Object.keys(settings).length > 0) {
      setLocalSettings(prev => ({ ...prev, ...settings }));
    }
  }, [settings]);

  // Загрузка файла
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setSelectedFile(file);
    setUploading(true);
    setUploadProgress(0);
    clearError();

    try {
      const result = await validateDocument(file, localSettings);
      setSuccess(`Документ "${file.name}" успешно загружен и проверен`);
      
      // Автоматически загружаем результаты валидации
      if (result.document_id) {
        await loadValidationResult(result.document_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      setSelectedFile(null);
      setUploadProgress(0);
    }
  };

  // Загрузка результатов валидации
  const handleLoadValidationResult = async (documentId) => {
    if (!validationResults[documentId]) {
      await loadValidationResult(documentId);
    }
    setExpandedResults(prev => ({
      ...prev,
      [documentId]: !prev[documentId]
    }));
  };

  // Удаление документа
  const handleDeleteDocument = async (documentId) => {
    if (window.confirm('Вы уверены, что хотите удалить этот документ?')) {
      try {
        await deleteDocument(documentId);
        setSuccess('Документ успешно удален');
      } catch (err) {
        setError(err.message);
      }
    }
  };

  // Повторная валидация
  const handleRevalidateDocument = async (documentId) => {
    try {
      await revalidateDocument(documentId, localSettings);
      setSuccess('Документ успешно перепроверен');
    } catch (err) {
      setError(err.message);
    }
  };

  // Экспорт результатов
  const handleExportResults = async (documentId, format = 'json') => {
    try {
      const blob = await exportResults(documentId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `normcontrol2_result_${documentId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setSuccess('Результаты экспортированы');
    } catch (err) {
      setError(err.message);
    }
  };

  // Сохранение настроек
  const handleSaveSettings = async () => {
    try {
      await saveSettings(localSettings);
      setSuccess('Настройки сохранены');
    } catch (err) {
      setError(err.message);
    }
  };

  // Получение иконки статуса
  const getStatusIcon = (status) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'compliant_warnings':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'non_compliant':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'critical_issues':
        return <AlertOctagon className="w-5 h-5 text-red-600" />;
      case 'needs_review':
        return <AlertCircle className="w-5 h-5 text-orange-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  // Получение цвета статуса
  const getStatusColor = (status) => {
    switch (status) {
      case 'compliant':
        return 'text-green-600 bg-green-50';
      case 'compliant_warnings':
        return 'text-yellow-600 bg-yellow-50';
      case 'non_compliant':
        return 'text-red-600 bg-red-50';
      case 'critical_issues':
        return 'text-red-700 bg-red-100';
      case 'needs_review':
        return 'text-orange-600 bg-orange-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Получение текста статуса
  const getStatusText = (status) => {
    switch (status) {
      case 'compliant':
        return 'Соответствует';
      case 'compliant_warnings':
        return 'Соответствует с предупреждениями';
      case 'non_compliant':
        return 'Не соответствует';
      case 'critical_issues':
        return 'Критические нарушения';
      case 'needs_review':
        return 'Требует проверки';
      default:
        return 'Неизвестно';
    }
  };

  // Фильтрация документов
  const filteredDocuments = documents.filter(doc => {
    const matchesStatus = filterStatus === 'all' || doc.status === filterStatus;
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  // Рендер результатов валидации
  const renderValidationResults = (documentId) => {
    const result = validationResults[documentId];
    if (!result) return null;

    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{result.compliance_score?.toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Оценка соответствия</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{result.total_issues || 0}</div>
            <div className="text-sm text-gray-600">Всего проблем</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{result.critical_issues || 0}</div>
            <div className="text-sm text-gray-600">Критических</div>
          </div>
        </div>

        {result.issues && result.issues.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-gray-800">Проблемы:</h4>
            {result.issues.slice(0, 5).map((issue, index) => (
              <div key={index} className="flex items-start space-x-2 p-2 bg-white rounded border">
                <div className="flex-shrink-0 mt-1">
                  {issue.severity === 'critical' && <AlertOctagon className="w-4 h-4 text-red-600" />}
                  {issue.severity === 'high' && <AlertCircle className="w-4 h-4 text-red-500" />}
                  {issue.severity === 'medium' && <AlertTriangle className="w-4 h-4 text-yellow-500" />}
                  {issue.severity === 'low' && <Info className="w-4 h-4 text-blue-500" />}
                  {issue.severity === 'info' && <Info className="w-4 h-4 text-gray-500" />}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-sm">{issue.title}</div>
                  <div className="text-xs text-gray-600 mt-1">{issue.description}</div>
                  {issue.recommendation && (
                    <div className="text-xs text-blue-600 mt-1">
                      💡 {issue.recommendation}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {result.issues.length > 5 && (
              <div className="text-sm text-gray-500 text-center">
                ... и еще {result.issues.length - 5} проблем
              </div>
            )}
          </div>
        )}

        {result.recommendations && result.recommendations.length > 0 && (
          <div className="mt-4">
            <h4 className="font-semibold text-gray-800 mb-2">Рекомендации:</h4>
            <ul className="space-y-1">
              {result.recommendations.map((rec, index) => (
                <li key={index} className="text-sm text-gray-700 flex items-start">
                  <span className="mr-2">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Действия с результатами */}
        <div className="mt-4 flex space-x-2">
          <button
            onClick={() => handleRevalidateDocument(documentId)}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Перепроверить
          </button>
          <button
            onClick={() => handleExportResults(documentId, 'json')}
            className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
          >
            <Download className="w-4 h-4 mr-1" />
            Экспорт JSON
          </button>
        </div>
      </div>
    );
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Требуется авторизация</h3>
        <p className="text-gray-600">Войдите в систему для доступа к модулю Нормоконтроль - 2</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок и настройки */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Нормоконтроль - 2</h2>
          <p className="text-gray-600">Расширенная проверка формата и оформления документов</p>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Настройки */}
      {showSettings && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="font-semibold mb-3">Настройки валидации</h3>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={localSettings.autoValidation}
                onChange={(e) => setLocalSettings(prev => ({ ...prev, autoValidation: e.target.checked }))}
                className="mr-2"
              />
              Автоматическая валидация при загрузке
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={localSettings.saveResults}
                onChange={(e) => setLocalSettings(prev => ({ ...prev, saveResults: e.target.checked }))}
                className="mr-2"
              />
              Сохранять результаты
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={localSettings.notificationEnabled}
                onChange={(e) => setLocalSettings(prev => ({ ...prev, notificationEnabled: e.target.checked }))}
                className="mr-2"
              />
              Уведомления о результатах
            </label>
          </div>
          <div className="mt-4">
            <button
              onClick={handleSaveSettings}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Сохранить настройки
            </button>
          </div>
        </div>
      )}

      {/* Статистика */}
      {statistics && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="font-semibold mb-3 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Статистика
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{statistics.total_documents_validated || 0}</div>
              <div className="text-sm text-gray-600">Всего проверено</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{statistics.average_compliance_score?.toFixed(1) || 0}%</div>
              <div className="text-sm text-gray-600">Средняя оценка</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{statistics.category_issues?.title_block || 0}</div>
              <div className="text-sm text-gray-600">Проблем с надписями</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{statistics.category_issues?.fonts || 0}</div>
              <div className="text-sm text-gray-600">Проблем со шрифтами</div>
            </div>
          </div>
        </div>
      )}

      {/* Загрузка файла */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Загрузка документа</h3>
        <div className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <div className="space-y-2">
              <p className="text-lg font-medium text-gray-900">
                {selectedFile ? selectedFile.name : 'Выберите файл для проверки'}
              </p>
              <p className="text-sm text-gray-600">
                Поддерживаемые форматы: PDF, DWG, DXF, DOCX, XLSX
              </p>
            </div>
            <input
              type="file"
              onChange={handleFileUpload}
              accept=".pdf,.dwg,.dxf,.docx,.xlsx"
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <label
              htmlFor="file-upload"
              className={`mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white ${
                uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
              }`}
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Загрузка... {uploadProgress}%
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Выбрать файл
                </>
              )}
            </label>
          </div>
        </div>
      </div>

      {/* Фильтры и поиск */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Поиск документов..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">Все статусы</option>
              <option value="compliant">Соответствует</option>
              <option value="compliant_warnings">С предупреждениями</option>
              <option value="non_compliant">Не соответствует</option>
              <option value="critical_issues">Критические нарушения</option>
              <option value="needs_review">Требует проверки</option>
            </select>
            <button
              onClick={loadDocuments}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Обновить
            </button>
          </div>
        </div>
      </div>

      {/* Список документов */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">Документы ({filteredDocuments.length})</h3>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 text-gray-400 mx-auto mb-4 animate-spin" />
            <p className="text-gray-600">Загрузка документов...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Нет документов</h3>
            <p className="text-gray-600">Загрузите документ для начала проверки</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredDocuments.map((doc) => (
              <div key={doc.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-8 h-8 text-blue-600" />
                    <div>
                      <h4 className="font-medium text-gray-900">{doc.name}</h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>Формат: {doc.format?.toUpperCase()}</span>
                        <span>•</span>
                        <span>Загружен: {new Date(doc.created_at).toLocaleDateString()}</span>
                        {doc.validation_time && (
                          <>
                            <span>•</span>
                            <span>Проверен: {new Date(doc.validation_time).toLocaleDateString()}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(doc.status)}`}>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(doc.status)}
                        <span>{getStatusText(doc.status)}</span>
                      </div>
                    </div>
                    
                    {doc.compliance_score !== undefined && (
                      <div className="text-right">
                        <div className="text-lg font-bold text-blue-600">{doc.compliance_score.toFixed(1)}%</div>
                        <div className="text-xs text-gray-600">Соответствие</div>
                      </div>
                    )}
                    
                    <div className="flex space-x-1">
                      <button
                        onClick={() => handleLoadValidationResult(doc.id)}
                        className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                        title="Показать результаты"
                      >
                        {expandedResults[doc.id] ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="p-2 text-red-600 hover:text-red-900 hover:bg-red-100 rounded-lg"
                        title="Удалить документ"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
                
                {expandedResults[doc.id] && renderValidationResults(doc.id)}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Уведомления */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
              <span className="text-red-800">{error}</span>
            </div>
            <button
              onClick={clearError}
              className="text-red-600 hover:text-red-800"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              <span className="text-green-800">{success}</span>
            </div>
            <button
              onClick={() => setSuccess(null)}
              className="text-green-600 hover:text-green-800"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NormControl2PanelV2;


