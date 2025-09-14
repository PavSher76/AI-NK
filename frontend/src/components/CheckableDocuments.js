import React, { useState, useEffect } from 'react';
import { getNormcontrolPrompt, formatNormcontrolPrompt } from '../utils/settings';
import { 
  Upload, 
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Download,
  Trash2,
  Eye,
  Calendar,
  User,
  Loader2,
  RefreshCw,
  AlertCircle,
  Play,
  Layers
} from 'lucide-react';

const CheckableDocuments = ({ isAuthenticated, authToken, refreshTrigger, onRefreshComplete }) => {
  console.log('🔍 [DEBUG] CheckableDocuments.js: Component rendered');

  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [expandedReports, setExpandedReports] = useState({});
  const [reports, setReports] = useState({});
  const [loadingReports, setLoadingReports] = useState({});
  const [settings, setSettings] = useState({});
  const [showSettings, setShowSettings] = useState(false);
  const [isLoadingSettings, setIsLoadingSettings] = useState(false);
  const [settingsError, setSettingsError] = useState(null);

  // Отладочные логи для отслеживания изменений состояния
  useEffect(() => {
    console.log('🔍 [DEBUG] CheckableDocuments.js: documents state changed:', documents.length, 'documents');
  }, [documents]);

  useEffect(() => {
    console.log('🔍 [DEBUG] CheckableDocuments.js: settings state changed:', settings);
  }, [settings]);

  const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

  // Загрузка списка проверяемых документов "как есть" без ожидания отчетов
  const fetchDocuments = async (retryCount = 0) => {
    console.log('🔍 [DEBUG] CheckableDocuments.js: fetchDocuments started - loading documents as-is');
    
    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: fetchDocuments - not authenticated');
      setError('Требуется авторизация для загрузки документов');
      return;
    }
    
    setLoading(true);
    setError(null);
    console.log('🔍 [DEBUG] CheckableDocuments.js: fetchDocuments API_BASE:', API_BASE, ', authToken:', authToken);
    try {
      const response = await fetch(`${API_BASE}/checkable-documents`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      console.log('🔍 [DEBUG] CheckableDocuments.js: fetchDocuments response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('🔍 [DEBUG] CheckableDocuments.js: fetchDocuments success, documents count:', data.documents?.length || 0);
        
        // Загружаем документы "как есть" без ожидания отчетов
        setDocuments(data.documents || []);
        
        // Отдельно запускаем загрузку отчетов для завершенных документов
        if (data.documents && data.documents.length > 0) {
          console.log('🔍 [DEBUG] CheckableDocuments.js: Starting background report loading for completed documents');
          loadReportsForCompletedDocuments(data.documents);
        }
      } else {
        console.error('🔍 [DEBUG] CheckableDocuments.js: fetchDocuments failed with status:', response.status);
        
        // Более информативные сообщения об ошибках
        if (response.status === 503) {
          if (retryCount < 3) {
            console.log(`🔍 [DEBUG] CheckableDocuments.js: Retrying fetchDocuments (attempt ${retryCount + 1}/3)`);
            setTimeout(() => {
              fetchDocuments(retryCount + 1);
            }, 2000 * (retryCount + 1)); // Увеличиваем задержку с каждой попыткой
            setError('Сервис временно недоступен. Повторная попытка...');
            return;
          } else {
            setError('Сервис временно недоступен. Попробуйте обновить страницу через несколько секунд.');
          }
        } else if (response.status === 401) {
          setError('Ошибка авторизации. Пожалуйста, войдите в систему заново.');
        } else if (response.status === 500) {
          setError('Внутренняя ошибка сервера. Попробуйте позже.');
        } else {
          setError(`Ошибка загрузки документов (код ${response.status})`);
        }
      }
    } catch (error) {
      console.error('🔍 [DEBUG] CheckableDocuments.js: fetchDocuments error:', error);
      
      // Более детальная обработка ошибок
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        setError('Ошибка сети. Проверьте подключение к интернету.');
      } else if (error.message && error.message.includes('Failed to fetch')) {
        setError('Сервис недоступен. Попробуйте обновить страницу.');
      } else {
        setError('Ошибка загрузки документов. Попробуйте позже.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Полное обновление данных (документы + отчеты)
  const refreshAllData = async () => {
    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: refreshAllData - not authenticated');
      setError('Требуется авторизация для обновления данных');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 [DEBUG] CheckableDocuments.js: refreshAllData - starting full refresh');
      
      // Загружаем список документов "как есть"
      const response = await fetch(`${API_BASE}/checkable-documents`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        const newDocuments = data.documents || [];
        console.log('🔍 [DEBUG] CheckableDocuments.js: refreshAllData - loaded', newDocuments.length, 'documents');
        
        // Сначала обновляем документы
        setDocuments(newDocuments);
        
        // Затем асинхронно загружаем отчеты для завершенных документов
        if (newDocuments.length > 0) {
          console.log('🔍 [DEBUG] CheckableDocuments.js: refreshAllData - starting background report loading');
          loadReportsForCompletedDocuments(newDocuments);
        }
        
        setSuccess('Данные успешно обновлены');
        
        // Автоматически скрываем сообщение об успехе через 3 секунды
        setTimeout(() => {
          setSuccess(null);
        }, 3000);
      } else {
        throw new Error('Ошибка загрузки документов');
      }
    } catch (error) {
      console.error('Ошибка обновления данных:', error);
      setError('Не удалось обновить данные');
    } finally {
      setLoading(false);
    }
  };

  // Скачивание PDF отчета
  const downloadReport = async (documentId) => {
    console.log('🔍 [DEBUG] CheckableDocuments.js: downloadReport started for document:', documentId);
    
    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: downloadReport - not authenticated');
      setError('Требуется авторизация для скачивания отчета');
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE}/checkable-documents/${documentId}/download-report`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        // Получаем blob из ответа
        const blob = await response.blob();
        
        // Создаем URL для blob
        const url = window.URL.createObjectURL(blob);
        
        // Создаем временную ссылку и кликаем по ней
        const link = document.createElement('a');
        link.href = url;
        link.download = `norm_control_report_${documentId}.pdf`;
        document.body.appendChild(link);
        link.click();
        
        // Очищаем
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        console.log('🔍 [DEBUG] CheckableDocuments.js: PDF report downloaded successfully');
      } else {
        console.error('🔍 [DEBUG] CheckableDocuments.js: downloadReport failed with status:', response.status);
        const errorData = await response.json();
        console.error('🔍 [DEBUG] CheckableDocuments.js: downloadReport error data:', errorData);
        setError('Ошибка скачивания отчета');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] CheckableDocuments.js: downloadReport error:', error);
      setError('Ошибка скачивания отчета');
    }
  };

  const downloadReportDocx = async (documentId) => {
    console.log('🔍 [DEBUG] CheckableDocuments.js: downloadReportDocx started for document:', documentId);
    
    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: downloadReportDocx - not authenticated');
      setError('Требуется авторизация для скачивания отчета');
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE}/checkable-documents/${documentId}/download-report-docx`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        // Получаем blob из ответа
        const blob = await response.blob();
        
        // Создаем URL для blob
        const url = window.URL.createObjectURL(blob);
        
        // Создаем временную ссылку и кликаем по ней
        const link = document.createElement('a');
        link.href = url;
        link.download = `norm_control_report_${documentId}.docx`;
        document.body.appendChild(link);
        link.click();
        
        // Очищаем
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        console.log('🔍 [DEBUG] CheckableDocuments.js: DOCX report downloaded successfully');
      } else {
        console.error('🔍 [DEBUG] CheckableDocuments.js: downloadReportDocx failed with status:', response.status);
        const errorData = await response.json();
        console.error('🔍 [DEBUG] CheckableDocuments.js: downloadReportDocx error data:', errorData);
        setError('Ошибка скачивания DOCX отчета');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] CheckableDocuments.js: downloadReportDocx error:', error);
      setError('Ошибка скачивания DOCX отчета');
    }
  };

  // Обработка выбора файла
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  // Загрузка документа
  const handleUpload = async () => {
    if (!selectedFile) return;

    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: handleUpload - not authenticated');
      setError('Требуется авторизация для загрузки документа');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      setError(null);
      setSuccess(null);

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${API_BASE}/upload/checkable`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setSuccess(`Документ "${selectedFile.name}" успешно загружен`);
        setSelectedFile(null);
        setUploadProgress(100);
        
        // Обновляем список документов
        setTimeout(() => {
          fetchDocuments();
        }, 1000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка загрузки документа');
      }
    } catch (error) {
      console.error('Ошибка загрузки:', error);
      setError(error.message);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  // Загрузка отчета о проверке
  const fetchReport = async (documentId) => {
    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: fetchReport - not authenticated');
      setError('Требуется авторизация для загрузки отчета');
      return;
    }
    
    try {
      setLoadingReports(prev => ({ ...prev, [documentId]: true }));
      const response = await fetch(`${API_BASE}/checkable-documents/${documentId}/report`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setReports(prev => ({ ...prev, [documentId]: data }));
      } else {
        throw new Error('Ошибка загрузки отчета');
      }
    } catch (error) {
      console.error('Ошибка загрузки отчета:', error);
      setError('Не удалось загрузить отчет');
    } finally {
      setLoadingReports(prev => ({ ...prev, [documentId]: false }));
    }
  };

  // Переключение отображения отчета
  const toggleReport = (documentId) => {
    if (!reports[documentId] && !loadingReports[documentId]) {
      fetchReport(documentId);
    }
    setExpandedReports(prev => ({ ...prev, [documentId]: !prev[documentId] }));
  };

  // Автоматическое обновление статуса после загрузки отчета
  useEffect(() => {
    // Обновляем список документов после загрузки отчетов
    if (Object.keys(reports).length > 0) {
      fetchDocuments();
    }
  }, [reports]);

  // Запуск проверки нормоконтроля
  const runNormcontrolCheck = async (documentId) => {
    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: runNormcontrolCheck - not authenticated');
      setError('Требуется авторизация для запуска проверки');
      return;
    }
    
    try {
      setLoadingReports(prev => ({ ...prev, [documentId]: true }));
      setError(null);
      
      // Отправляем запрос на асинхронную проверку
      const checkResponse = await fetch(`${API_BASE}/checkable-documents/${documentId}/check`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (checkResponse.ok) {
        const result = await checkResponse.json();
        
        if (result.status === 'started') {
          setSuccess(`Проверка нормоконтроля запущена асинхронно`);
          
          // Запускаем периодическую проверку статуса
          startStatusPolling(documentId);
        } else if (result.status === 'already_processing') {
          setError('Документ уже обрабатывается');
        } else {
          setSuccess(`Проверка нормоконтроля завершена`);
          // Обновляем отчет
          setTimeout(() => {
            fetchReport(documentId);
          }, 1000);
        }
      } else {
        const errorData = await checkResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Ошибка запуска проверки');
      }
    } catch (error) {
      console.error('Ошибка проверки нормоконтроля:', error);
      setError(`Ошибка проверки: ${error.message}`);
    } finally {
      setLoadingReports(prev => ({ ...prev, [documentId]: false }));
    }
  };

  // Запуск иерархической проверки
  const runHierarchicalCheck = async (documentId) => {
    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: runHierarchicalCheck - not authenticated');
      setError('Требуется авторизация для запуска проверки');
      return;
    }
    
    try {
      setLoadingReports(prev => ({ ...prev, [documentId]: true }));
      setError(null);
      
      // Отправляем запрос на асинхронную иерархическую проверку
      const checkResponse = await fetch(`${API_BASE}/checkable-documents/${documentId}/hierarchical-check`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (checkResponse.ok) {
        const result = await checkResponse.json();
        
        if (result.status === 'started') {
          setSuccess(`Иерархическая проверка запущена асинхронно`);
          
          // Запускаем периодическую проверку статуса
          startStatusPolling(documentId);
        } else if (result.status === 'already_processing') {
          setError('Документ уже обрабатывается');
        } else {
          setSuccess(`Иерархическая проверка завершена`);
          // Обновляем отчет
          setTimeout(() => {
            fetchReport(documentId);
          }, 1000);
        }
      } else {
        const errorData = await checkResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Ошибка запуска иерархической проверки');
      }
    } catch (error) {
      console.error('Ошибка иерархической проверки:', error);
      setError(`Ошибка иерархической проверки: ${error.message}`);
    } finally {
      setLoadingReports(prev => ({ ...prev, [documentId]: false }));
    }
  };

  // Периодическая проверка статуса документа
  const startStatusPolling = (documentId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/checkable-documents`, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          const document = data.documents?.find(doc => doc.id === documentId);
          
          if (document) {
            if (document.processing_status === 'completed') {
              clearInterval(pollInterval);
              setSuccess(`Проверка нормоконтроля завершена`);
              // Обновляем отчет
              fetchReport(documentId);
              // Обновляем список документов
              fetchDocuments();
            } else if (document.processing_status === 'error') {
              clearInterval(pollInterval);
              setError('Ошибка при выполнении проверки нормоконтроля');
            }
            // Если статус 'processing', продолжаем опрос
          }
        }
      } catch (error) {
        console.error('Ошибка при проверке статуса:', error);
      }
    }, 3000); // Проверяем каждые 3 секунды
    
    // Останавливаем опрос через 10 минут
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 600000);
  };

  // Удаление документа
  const deleteDocument = async (documentId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот документ?')) return;

    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: deleteDocument - not authenticated');
      setError('Требуется авторизация для удаления документа');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/checkable-documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        await fetchDocuments();
        setSuccess('Документ успешно удален');
      } else {
        throw new Error('Ошибка удаления документа');
      }
    } catch (error) {
      console.error('Ошибка удаления документа:', error);
      setError('Не удалось удалить документ');
    }
  };

  // Форматирование даты
  const formatDate = (dateString) => {
    if (!dateString) return 'Не указано';
    return new Date(dateString).toLocaleString('ru-RU');
  };

  // Получение иконки статуса
  const getStatusIcon = (status) => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'fail':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'uncertain':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  // Получение цвета статуса
  const getStatusColor = (status) => {
    switch (status) {
      case 'pass':
        return 'bg-green-100 text-green-800';
      case 'fail':
        return 'bg-red-100 text-red-800';
      case 'uncertain':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Получение статуса проверки документа
  const getDocumentStatus = (doc) => {
    // Если есть отчет о проверке (обычная или иерархическая), документ проверен
    if (reports[doc.id]?.norm_control_result || reports[doc.id]?.hierarchical_result) {
      return {
        text: 'Проверен',
        color: 'bg-green-100 text-green-800',
        icon: <CheckCircle className="w-3 h-3" />
      };
    }
    
    // Если обработка завершена, но нет отчета - ожидает проверки
    if (doc.processing_status === 'completed') {
      return {
        text: 'Ожидает',
        color: 'bg-yellow-100 text-yellow-800',
        icon: <Clock className="w-3 h-3" />
      };
    }
    
    // Если документ в процессе обработки
    if (doc.processing_status === 'processing') {
      return {
        text: 'Обрабатывается',
        color: 'bg-orange-100 text-orange-800',
        icon: <Loader2 className="w-3 h-3 animate-spin" />
      };
    }
    
    // Если обработка не завершена
    return {
      text: 'Загружен',
      color: 'bg-blue-100 text-blue-800',
      icon: <FileText className="w-3 h-3" />
    };
  };

  const getChecklistStatusColor = (status) => {
    switch (status) {
      case 'pass':
        return 'bg-green-100 text-green-800';
      case 'fail':
        return 'bg-red-100 text-red-800';
      case 'uncertain':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getChecklistStatusText = (status) => {
    switch (status) {
      case 'pass':
        return 'Соответствует';
      case 'fail':
        return 'Не соответствует';
      case 'uncertain':
        return 'Требует проверки';
      default:
        return 'Неизвестно';
    }
  };

  const getChecklistCategoryName = (category) => {
    const categories = {
      'general_requirements': 'Общие требования',
      'text_part': 'Текстовая часть',
      'graphical_part': 'Графическая часть',
      'specifications': 'Спецификации',
      'assembly_drawings': 'Сборочные чертежи',
      'detail_drawings': 'Деталировочные чертежи',
      'schemes': 'Схемы'
    };
    return categories[category] || category;
  };

  const getProcessingStatusText = (doc) => {
    if (loadingReports[doc.id]) {
      return 'Запуск проверки...';
    }
    
    switch (doc.processing_status) {
      case 'completed':
        return 'Проверка завершена';
      case 'processing':
        return 'Выполняется проверка...';
      case 'error':
        return 'Ошибка проверки';
      case 'pending':
        return 'Готов к проверке';
      default:
        return 'Статус неизвестен';
    }
  };

  // Загрузка данных при монтировании компонента
  useEffect(() => {
    // Первичная загрузка документов "как есть" без ожидания отчетов
    fetchDocuments();
    
    // Автоматическое обновление статуса документов в процессе обработки
    const interval = setInterval(() => {
      const hasProcessingDocuments = documents.some(doc => doc.processing_status === 'processing');
      if (hasProcessingDocuments) {
        console.log('🔍 [DEBUG] CheckableDocuments.js: Auto-refreshing documents with processing status');
        fetchDocuments();
      }
    }, 5000); // Увеличиваем интервал до 5 секунд
    
    return () => clearInterval(interval);
  }, [isAuthenticated, authToken]); // Убираем documents из зависимостей, чтобы избежать бесконечного цикла

  // Функция для загрузки отчетов для завершенных документов
  const loadReportsForCompletedDocuments = async (documentsToProcess = documents) => {
    // Проверка авторизации
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: loadReportsForCompletedDocuments - not authenticated');
      return;
    }
    
    if (documentsToProcess.length > 0) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: loadReportsForCompletedDocuments - processing', documentsToProcess.length, 'documents');
      
      for (const doc of documentsToProcess) {
        if (doc.processing_status === 'completed' && !reports[doc.id] && !loadingReports[doc.id]) {
          console.log('🔍 [DEBUG] CheckableDocuments.js: Loading report for document', doc.id);
          setLoadingReports(prev => ({ ...prev, [doc.id]: true }));
          
          try {
            const response = await fetch(`${API_BASE}/checkable-documents/${doc.id}/report`, {
              headers: {
                'Authorization': `Bearer ${authToken}`
              }
            });
            if (response.ok) {
              const data = await response.json();
              setReports(prev => ({ ...prev, [doc.id]: data }));
              console.log('🔍 [DEBUG] CheckableDocuments.js: Report loaded successfully for document', doc.id);
            } else {
              console.warn('🔍 [DEBUG] CheckableDocuments.js: Failed to load report for document', doc.id, 'status:', response.status);
            }
          } catch (error) {
            console.error(`Ошибка загрузки отчета для документа ${doc.id}:`, error);
          } finally {
            setLoadingReports(prev => ({ ...prev, [doc.id]: false }));
          }
        }
      }
    }
  };

  // Автоматическая загрузка отчетов при изменении документов
  useEffect(() => {
    if (documents.length > 0 && isAuthenticated && authToken) {
      loadReportsForCompletedDocuments();
    }
  }, [documents, isAuthenticated, authToken]); // Убираем reports и loadingReports из зависимостей

  // Обработка обновления данных после авторизации
  useEffect(() => {
    if (refreshTrigger && isAuthenticated && authToken) {
      console.log('🔍 [DEBUG] CheckableDocuments.js: Обновление данных проверяемых документов после авторизации...');
      fetchDocuments();
      if (onRefreshComplete) {
        onRefreshComplete();
      }
    }
  }, [refreshTrigger, isAuthenticated, authToken, onRefreshComplete]);

  console.log('🔍 [DEBUG] CheckableDocuments.js: Rendering with state:', {
    documentsCount: documents.length,
    isLoading: loading,
    error,
    showSettings,
    settingsCount: Object.keys(settings).length,
    selectedFile: selectedFile?.name,
    isUploading: uploading,
    isAuthenticated,
    hasAuthToken: !!authToken
  });

  // Проверка авторизации при рендеринге
  if (!isAuthenticated || !authToken) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Проверка Нормоконтроля
          </h1>
          <p className="text-gray-600">
            Загружайте документы для проверки на соответствие нормативным требованиям.
          </p>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-yellow-500 mr-2" />
            <span className="text-yellow-700">
              Требуется авторизация для доступа к функциям нормоконтроля. Пожалуйста, войдите в систему.
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Проверка Нормоконтроля
        </h1>
        <p className="text-gray-600">
          Загружайте документы для проверки на соответствие нормативным требованиям. 
          Документы автоматически удаляются через 2 дня после загрузки.
        </p>
      </div>

      {/* Сообщения об ошибках и успехе */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <XCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
            <span className="text-green-700">{success}</span>
          </div>
        </div>
      )}

      {/* Панель загрузки */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Загрузка нового документа
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Выберите файл для проверки
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="file"
                onChange={handleFileSelect}
                accept=".pdf,.docx,.dwg,.ifc"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                disabled={uploading}
              />
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Загрузка...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Загрузить
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Прогресс загрузки */}
          {uploading && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          )}

          {/* Информация о выбранном файле */}
          {selectedFile && (
            <div className="p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center">
                <FileText className="w-5 h-5 text-blue-500 mr-2" />
                <span className="text-sm text-blue-700">
                  Выбран файл: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} МБ)
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Панель управления */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={refreshAllData}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Загрузка...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Обновить
              </>
            )}
          </button>
        </div>
      </div>

      {/* Список документов */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Загруженные документы ({documents.length})
          </h3>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
            <p className="mt-2 text-gray-500">Загрузка документов...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 mx-auto text-gray-400" />
            <p className="mt-2 text-gray-500">Документы не найдены</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {documents.map((doc) => (
              <div key={doc.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center justify-center w-10 h-10 bg-gray-100 rounded-lg">
                      <FileText className="w-5 h-5 text-gray-600" />
                    </div>
                    
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{doc.original_filename}</h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                        <span>{doc.file_type?.toUpperCase()}</span>
                        <span>{(doc.file_size / 1024 / 1024).toFixed(2)} МБ</span>
                        <span className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(doc.upload_date)}</span>
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs flex items-center space-x-1 ${getDocumentStatus(doc).color}`}>
                          {getDocumentStatus(doc).icon}
                          <span>{getDocumentStatus(doc).text}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => runNormcontrolCheck(doc.id)}
                      disabled={loadingReports[doc.id] || doc.processing_status === 'processing'}
                      className={`p-2 transition-colors ${
                        loadingReports[doc.id] || doc.processing_status === 'processing'
                          ? 'text-gray-300 cursor-not-allowed' 
                          : 'text-gray-400 hover:text-green-600'
                      }`}
                      title="Запустить проверку нормоконтроля"
                    >
                      {loadingReports[doc.id] || doc.processing_status === 'processing' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                    </button>
                    
                    <button
                      onClick={() => runHierarchicalCheck(doc.id)}
                      disabled={loadingReports[doc.id] || doc.processing_status === 'processing'}
                      className={`p-2 transition-colors ${
                        loadingReports[doc.id] || doc.processing_status === 'processing'
                          ? 'text-gray-300 cursor-not-allowed' 
                          : 'text-gray-400 hover:text-purple-600'
                      }`}
                      title="Запустить иерархическую проверку"
                    >
                      {loadingReports[doc.id] || doc.processing_status === 'processing' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Layers className="w-4 h-4" />
                      )}
                    </button>
                    
                    <button
                      onClick={() => toggleReport(doc.id)}
                      className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                      title="Просмотр отчета"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => downloadReport(doc.id)}
                      className={`p-2 transition-colors ${
                        doc.processing_status === 'completed' 
                          ? 'text-gray-400 hover:text-blue-600' 
                          : 'text-gray-300 cursor-not-allowed'
                      }`}
                      title={doc.processing_status === 'completed' ? 'Скачать отчет PDF' : 'Отчет недоступен'}
                      disabled={doc.processing_status !== 'completed'}
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => downloadReportDocx(doc.id)}
                      className={`p-2 transition-colors ${
                        doc.processing_status === 'completed' 
                          ? 'text-gray-400 hover:text-green-600' 
                          : 'text-gray-300 cursor-not-allowed'
                      }`}
                      title={doc.processing_status === 'completed' ? 'Скачать отчет DOCX' : 'Отчет недоступен'}
                      disabled={doc.processing_status !== 'completed'}
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => deleteDocument(doc.id)}
                      className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                      title="Удалить"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {/* Отчет о проверке */}
                {expandedReports[doc.id] && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    {loadingReports[doc.id] ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="w-5 h-5 animate-spin text-blue-600 mr-2" />
                        <span className="text-gray-600">Загрузка отчета...</span>
                      </div>
                    ) : reports[doc.id] ? (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h5 className="font-medium text-gray-900">Отчет о проверке нормоконтроля</h5>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(reports[doc.id].norm_control_result?.overall_status)}`}>
                            {reports[doc.id].norm_control_result?.overall_status === 'pass' ? 'Пройден' :
                             reports[doc.id].norm_control_result?.overall_status === 'fail' ? 'Не пройден' :
                             reports[doc.id].norm_control_result?.overall_status === 'uncertain' ? 'Требует внимания' : 'Неизвестно'}
                          </span>
                        </div>
                        
                        {reports[doc.id].norm_control_result && (
                          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div className="bg-white p-3 rounded-lg border">
                              <div className="text-sm text-gray-500">Уверенность</div>
                              <div className="text-lg font-semibold">
                                {Math.round((reports[doc.id].norm_control_result.confidence || 0) * 100)}%
                              </div>
                            </div>
                            <div className="bg-white p-3 rounded-lg border">
                              <div className="text-sm text-gray-500">Соответствие</div>
                              <div className="text-lg font-semibold text-blue-600">
                                {reports[doc.id].norm_control_result.compliance_score || 0}%
                              </div>
                            </div>
                            <div className="bg-white p-3 rounded-lg border">
                              <div className="text-sm text-gray-500">Всего нарушений</div>
                              <div className="text-lg font-semibold text-red-600">
                                {reports[doc.id].norm_control_result.total_findings || 0}
                              </div>
                            </div>
                            <div className="bg-white p-3 rounded-lg border">
                              <div className="text-sm text-gray-500">Критические</div>
                              <div className="text-lg font-semibold text-red-600">
                                {reports[doc.id].norm_control_result.critical_findings || 0}
                              </div>
                            </div>
                            <div className="bg-white p-3 rounded-lg border">
                              <div className="text-sm text-gray-500">Предупреждения</div>
                              <div className="text-lg font-semibold text-yellow-600">
                                {reports[doc.id].norm_control_result.warning_findings || 0}
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* Детальный чек-лист */}
                        {reports[doc.id].norm_control_result?.checklist_results && (
                          <div className="bg-white p-4 rounded-lg border">
                            <div className="text-sm font-medium text-gray-700 mb-4">Результаты проверки по разделам:</div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {Object.entries(reports[doc.id].norm_control_result.checklist_results).map(([category, result]) => (
                                <div key={category} className="border rounded-lg p-3">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="font-medium text-gray-900">
                                      {getChecklistCategoryName(category)}
                                    </span>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getChecklistStatusColor(result.status)}`}>
                                      {getChecklistStatusText(result.status)}
                                    </span>
                                  </div>
                                  {result.findings && result.findings.length > 0 && (
                                    <div className="text-sm text-gray-600">
                                      <div className="font-medium mb-1">Нарушения:</div>
                                      <ul className="list-disc list-inside space-y-1">
                                        {result.findings.map((finding, index) => (
                                          <li key={index} className="text-xs">
                                            {finding.description}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Детальные нарушения */}
                        {reports[doc.id].norm_control_result?.findings && reports[doc.id].norm_control_result.findings.length > 0 && (
                          <div className="bg-white p-4 rounded-lg border">
                            <div className="text-sm font-medium text-gray-700 mb-4">Детальные нарушения:</div>
                            <div className="space-y-3">
                              {reports[doc.id].norm_control_result.findings.map((finding, index) => (
                                <div key={index} className="border-l-4 border-red-500 pl-4 py-2">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="font-medium text-gray-900">
                                      {finding.category && getChecklistCategoryName(finding.category)} - {finding.type === 'critical' ? 'Критическое' : finding.type === 'warning' ? 'Предупреждение' : 'Информация'}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                      Стр. {finding.page_number}
                                    </span>
                                  </div>
                                  <div className="text-sm text-gray-700 mb-1">
                                    {finding.description}
                                  </div>
                                  {finding.clause_id && (
                                    <div className="text-xs text-gray-500 mb-1">
                                      Норма: {finding.clause_id}
                                    </div>
                                  )}
                                  {finding.recommendation && (
                                    <div className="text-xs text-blue-600">
                                      Рекомендация: {finding.recommendation}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {reports[doc.id].norm_control_result?.summary && (
                          <div className="bg-white p-4 rounded-lg border">
                            <div className="text-sm font-medium text-gray-700 mb-2">Заключение:</div>
                            <div className="text-gray-900">{reports[doc.id].norm_control_result.summary}</div>
                          </div>
                        )}

                        {reports[doc.id].norm_control_result?.recommendations && (
                          <div className="bg-white p-4 rounded-lg border">
                            <div className="text-sm font-medium text-gray-700 mb-2">Общие рекомендации:</div>
                            <div className="text-gray-900">{reports[doc.id].norm_control_result.recommendations}</div>
                          </div>
                        )}
                        
                        {reports[doc.id].norm_control_result?.analysis_date && (
                          <div className="text-sm text-gray-500">
                            Дата проверки: {formatDate(reports[doc.id].norm_control_result.analysis_date)}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-4 text-gray-500">
                        Отчет о проверке не найден
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CheckableDocuments;
