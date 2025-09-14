import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Download, 
  Eye,
  Trash2,
  Search,
  Filter,
  SortAsc,
  SortDesc,
  Calendar,
  Clock,
  User,
  X,
  Send,
  SpellCheck,
  Brain,
  FileCheck,
  FileText as Report,
  RefreshCw,
} from 'lucide-react';

const OutgoingControlPage = ({ isAuthenticated, authToken }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showViewDocumentModal, setShowViewDocumentModal] = useState(false);
  const [viewingDocument, setViewingDocument] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';




  // Загрузка документов
  const fetchDocuments = async () => {
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] OutgoingControlPage.js: Not authenticated, skipping fetch');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/outgoing-control/documents`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('🔍 [DEBUG] OutgoingControlPage.js: Fetched documents:', data);
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError('Ошибка загрузки документов: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Обработка загрузки файла
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFile(file);
      setError(null);
    }
  };

  // Обработка документа
  const processDocument = async () => {
    if (!uploadedFile) {
      setError('Пожалуйста, выберите файл для обработки');
      return;
    }

    if (!isAuthenticated || !authToken) {
      setError('Необходима авторизация для обработки документов');
      return;
    }

    setIsProcessing(true);
    setProcessingStep('Загрузка документа...');

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('document_type', 'outgoing_correspondence');

      setProcessingStep('Парсинг документа...');
      const uploadResponse = await fetch(`${API_BASE}/outgoing-control/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData
      });

      if (!uploadResponse.ok) {
        throw new Error(`HTTP error! status: ${uploadResponse.status}`);
      }

      const uploadResult = await uploadResponse.json();
      console.log('🔍 [DEBUG] OutgoingControlPage.js: Document uploaded:', uploadResult);

      setProcessingStep('Проверка орфографии...');
      const spellCheckResponse = await fetch(`${API_BASE}/outgoing-control/spellcheck`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_id: uploadResult.document_id,
          text: uploadResult.text
        })
      });

      if (!spellCheckResponse.ok) {
        throw new Error(`HTTP error! status: ${spellCheckResponse.status}`);
      }

      const spellCheckResult = await spellCheckResponse.json();
      console.log('🔍 [DEBUG] OutgoingControlPage.js: Spell check completed:', spellCheckResult);

      setProcessingStep('Анализ экспертом выходного контроля...');
      const expertAnalysisResponse = await fetch(`${API_BASE}/outgoing-control/expert-analysis`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_id: uploadResult.document_id,
          text: uploadResult.text,
          spell_check_results: spellCheckResult
        })
      });

      if (!expertAnalysisResponse.ok) {
        throw new Error(`HTTP error! status: ${expertAnalysisResponse.status}`);
      }

      const expertAnalysisResult = await expertAnalysisResponse.json();
      console.log('🔍 [DEBUG] OutgoingControlPage.js: Expert analysis completed:', expertAnalysisResult);

      setProcessingStep('Консолидация результатов...');
      const consolidationResponse = await fetch(`${API_BASE}/outgoing-control/consolidate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_id: uploadResult.document_id,
          spell_check_results: spellCheckResult,
          expert_analysis: expertAnalysisResult,
          original_text: uploadResult.text
        })
      });

      if (!consolidationResponse.ok) {
        throw new Error(`HTTP error! status: ${consolidationResponse.status}`);
      }

      const finalResult = await consolidationResponse.json();
      console.log('🔍 [DEBUG] OutgoingControlPage.js: Final result:', finalResult);

      setSuccess('Документ успешно обработан');
      setUploadedFile(null);
      fetchDocuments();
    } catch (error) {
      console.error('Error processing document:', error);
      setError('Ошибка обработки документа: ' + error.message);
    } finally {
      setIsProcessing(false);
      setProcessingStep('');
    }
  };

  // Просмотр документа
  const handleViewDocument = (document) => {
    setViewingDocument(document);
    setShowViewDocumentModal(true);
  };

  // Скачивание отчета
  const handleDownloadReport = async (doc) => {
    try {
      const response = await fetch(`${API_BASE}/outgoing-control/report/${doc.id}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const htmlContent = data.html_report;
      
      // Создаем blob из HTML содержимого
      const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `outgoing_control_report_${doc.filename || doc.id}_${new Date().toISOString().split('T')[0]}.html`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setSuccess('Отчет успешно скачан');
    } catch (error) {
      console.error('Error downloading report:', error);
      setError('Ошибка скачивания отчета: ' + error.message);
    }
  };

  // Удаление документа
  const deleteDocument = async (documentId) => {
    if (!isAuthenticated || !authToken) {
      setError('Необходима авторизация для удаления документов');
      return;
    }

    if (!window.confirm('Вы уверены, что хотите удалить этот документ?')) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/outgoing-control/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setSuccess('Документ успешно удален');
      fetchDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
      setError('Ошибка удаления документа: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Фильтрация и сортировка
  const filteredDocuments = (Array.isArray(documents) ? documents : [])
    .filter(doc => {
      const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           doc.title.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filterStatus === 'all' || doc.status === filterStatus;
      return matchesSearch && matchesFilter;
    })
    .sort((a, b) => {
      let aValue, bValue;
      switch (sortBy) {
        case 'filename':
          aValue = a.filename.toLowerCase();
          bValue = b.filename.toLowerCase();
          break;
        case 'date':
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          aValue = a.filename.toLowerCase();
          bValue = b.filename.toLowerCase();
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  // Загрузка при монтировании
  useEffect(() => {
    fetchDocuments();
  }, [isAuthenticated, authToken]);

  // Очистка сообщений
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Заголовок */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <FileCheck className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-3xl font-bold text-gray-900">Выходной контроль корреспонденции</h1>
            </div>
          </div>
          <p className="text-gray-600 text-lg">
            Проверка исходящих документов на соответствие требованиям ТДО
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              Орфографическая проверка
            </span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              Экспертный анализ
            </span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              Консолидированный отчет
            </span>
          </div>
        </div>

        {/* Сообщения об ошибках и успехе */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-red-400 mr-3" />
              <div className="text-red-800">{error}</div>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <CheckCircle className="w-5 h-5 text-green-400 mr-3" />
              <div className="text-green-800">{success}</div>
            </div>
          </div>
        )}

        {/* Загрузка документа */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Upload className="w-5 h-5 mr-2 text-blue-600" />
            Загрузка документа для проверки
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Выберите файл для проверки
              </label>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleFileUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                disabled={isProcessing}
              />
            </div>

            {uploadedFile && (
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FileText className="w-5 h-5 text-gray-400 mr-2" />
                  <span className="text-sm font-medium text-gray-900">{uploadedFile.name}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    ({(uploadedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                </div>
              </div>
            )}

            {isProcessing && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center">
                  <RefreshCw className="w-5 h-5 text-blue-600 mr-2 animate-spin" />
                  <div className="text-blue-800 font-medium">{processingStep}</div>
                </div>
              </div>
            )}

            <button
              onClick={processDocument}
              disabled={!uploadedFile || isProcessing}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isProcessing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Обработка...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Начать проверку
                </>
              )}
            </button>
          </div>
        </div>

        {/* Список документов */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 sm:mb-0">
                Обработанные документы
              </h2>
              
              <div className="flex flex-col sm:flex-row gap-4">
                {/* Поиск */}
                <div className="relative">
                  <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Поиск документов..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Фильтр */}
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">Все статусы</option>
                  <option value="processing">Обработка</option>
                  <option value="completed">Завершен</option>
                  <option value="error">Ошибка</option>
                </select>

                {/* Сортировка */}
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center"
                >
                  {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {loading ? (
              <div className="p-6 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Загрузка документов...</p>
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Документы не найдены</p>
              </div>
            ) : (
              filteredDocuments.map((document) => (
                <div key={document.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <h3 className="text-lg font-medium text-gray-900">{document.filename}</h3>
                        <span className={`ml-3 px-2 py-1 rounded-full text-xs font-medium ${
                          document.status === 'completed' 
                            ? 'bg-green-100 text-green-800' 
                            : document.status === 'processing'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {document.status === 'completed' ? 'Завершен' : 
                           document.status === 'processing' ? 'Обработка' : 'Ошибка'}
                        </span>
                        {document.expert_analysis?.verdict && (
                          <span className={`ml-2 px-3 py-1 rounded-full text-xs font-medium ${
                            document.expert_analysis.verdict_color === 'success'
                              ? 'bg-green-100 text-green-800'
                              : document.expert_analysis.verdict_color === 'warning'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {document.expert_analysis.verdict}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 mb-2">{document.title}</p>
                      <div className="flex items-center text-sm text-gray-500">
                        <Calendar className="w-4 h-4 mr-1" />
                        <span className="mr-4">
                          {new Date(document.created_at).toLocaleDateString('ru-RU')}
                        </span>
                        <Clock className="w-4 h-4 mr-1" />
                        <span>
                          {new Date(document.created_at).toLocaleTimeString('ru-RU')}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleViewDocument(document)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Просмотреть документ"
                      >
                        <Eye className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDownloadReport(document)}
                        className="text-green-600 hover:text-green-900"
                        title="Скачать отчет"
                      >
                        <Download className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => deleteDocument(document.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Удалить документ"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Модальное окно просмотра документа */}
        {showViewDocumentModal && viewingDocument && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Просмотр документа: {viewingDocument.filename}
                </h3>
                <button
                  onClick={() => setShowViewDocumentModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                      <FileText className="w-5 h-5 mr-2 text-blue-600" />
                      Информация о документе
                    </h4>
                    <div className="space-y-2">
                      <div className="flex justify-between py-1 border-b border-gray-100">
                        <span className="text-sm text-gray-600">Название:</span>
                        <span className="text-sm font-medium text-gray-900">{viewingDocument.title}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100">
                        <span className="text-sm text-gray-600">Статус:</span>
                        <span className="text-sm font-medium text-gray-900">{viewingDocument.status}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100">
                        <span className="text-sm text-gray-600">Дата создания:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {new Date(viewingDocument.created_at).toLocaleString('ru-RU')}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                      <Report className="w-5 h-5 mr-2 text-green-600" />
                      Результаты проверки
                    </h4>
                    {viewingDocument.spell_check_results ? (
                      <div className="space-y-2">
                        <div className="flex justify-between py-1 border-b border-gray-100">
                          <span className="text-sm text-gray-600">Орфографические ошибки:</span>
                          <span className="text-sm font-medium text-gray-900">
                            {viewingDocument.spell_check_results.errors?.length || 0}
                          </span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-gray-100">
                          <span className="text-sm text-gray-600">Экспертная оценка:</span>
                          <span className="text-sm font-medium text-gray-900">
                            {viewingDocument.expert_analysis?.overall_score || 'Не выполнена'}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">Результаты проверки недоступны</p>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => handleDownloadReport(viewingDocument)}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Скачать отчет
                </button>
                <button
                  onClick={() => setShowViewDocumentModal(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default OutgoingControlPage;
