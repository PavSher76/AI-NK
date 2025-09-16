import { useState, useEffect, useCallback } from 'react';
import normControl2Api from '../services/normcontrol2Api';

/**
 * Хук для работы с модулем Нормоконтроль - 2
 */
export const useNormControl2 = (authToken) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationResults, setValidationResults] = useState({});
  const [statistics, setStatistics] = useState(null);
  const [settings, setSettings] = useState({});

  // Загрузка документов
  const loadDocuments = useCallback(async () => {
    if (!authToken) return;

    setLoading(true);
    setError(null);

    try {
      const data = await normControl2Api.getDocuments(authToken);
      setDocuments(data.documents || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  // Валидация документа
  const validateDocument = useCallback(async (file, options = {}) => {
    if (!authToken) {
      throw new Error('Требуется авторизация');
    }

    setLoading(true);
    setError(null);

    try {
      const result = await normControl2Api.validateDocument(file, options, authToken);
      
      // Обновляем список документов
      const newDocument = {
        id: result.document_id,
        name: result.document_name,
        format: result.document_format,
        status: result.overall_status,
        compliance_score: result.compliance_score,
        total_issues: result.total_issues,
        validation_time: result.validation_time,
        created_at: new Date().toISOString()
      };
      
      setDocuments(prev => [newDocument, ...prev]);
      setValidationResults(prev => ({
        ...prev,
        [result.document_id]: result
      }));

      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  // Загрузка результатов валидации
  const loadValidationResult = useCallback(async (documentId) => {
    if (!authToken || validationResults[documentId]) return;

    try {
      const result = await normControl2Api.getDocumentIssues(documentId, authToken);
      setValidationResults(prev => ({
        ...prev,
        [documentId]: result
      }));
    } catch (err) {
      console.error('Ошибка загрузки результатов:', err);
    }
  }, [authToken, validationResults]);

  // Загрузка статистики
  const loadStatistics = useCallback(async () => {
    if (!authToken) return;

    try {
      const data = await normControl2Api.getStatistics(authToken);
      setStatistics(data);
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err);
    }
  }, [authToken]);

  // Загрузка настроек
  const loadSettings = useCallback(async () => {
    if (!authToken) return;

    try {
      const data = await normControl2Api.getSettings(authToken);
      setSettings(data.settings || {});
    } catch (err) {
      console.error('Ошибка загрузки настроек:', err);
    }
  }, [authToken]);

  // Сохранение настроек
  const saveSettings = useCallback(async (newSettings) => {
    if (!authToken) {
      throw new Error('Требуется авторизация');
    }

    try {
      await normControl2Api.saveSettings(newSettings, authToken);
      setSettings(newSettings);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [authToken]);

  // Удаление документа
  const deleteDocument = useCallback(async (documentId) => {
    if (!authToken) {
      throw new Error('Требуется авторизация');
    }

    try {
      await normControl2Api.deleteDocument(documentId, authToken);
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      setValidationResults(prev => {
        const newResults = { ...prev };
        delete newResults[documentId];
        return newResults;
      });
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [authToken]);

  // Повторная валидация
  const revalidateDocument = useCallback(async (documentId, options = {}) => {
    if (!authToken) {
      throw new Error('Требуется авторизация');
    }

    setLoading(true);
    setError(null);

    try {
      const result = await normControl2Api.revalidateDocument(documentId, options, authToken);
      
      // Обновляем документ в списке
      setDocuments(prev => prev.map(doc => 
        doc.id === documentId 
          ? {
              ...doc,
              status: result.overall_status,
              compliance_score: result.compliance_score,
              total_issues: result.total_issues,
              validation_time: result.validation_time
            }
          : doc
      ));

      // Обновляем результаты валидации
      setValidationResults(prev => ({
        ...prev,
        [documentId]: result
      }));

      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  // Пакетная валидация
  const batchValidate = useCallback(async (filePaths, options = {}) => {
    if (!authToken) {
      throw new Error('Требуется авторизация');
    }

    setLoading(true);
    setError(null);

    try {
      const result = await normControl2Api.batchValidate(filePaths, options, authToken);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  // Экспорт результатов
  const exportResults = useCallback(async (documentId, format = 'json') => {
    if (!authToken) {
      throw new Error('Требуется авторизация');
    }

    try {
      const blob = await normControl2Api.exportResults(documentId, format, authToken);
      return blob;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [authToken]);

  // Загрузка данных при инициализации
  useEffect(() => {
    if (authToken) {
      loadDocuments();
      loadStatistics();
      loadSettings();
    }
  }, [authToken, loadDocuments, loadStatistics, loadSettings]);

  return {
    // Состояние
    documents,
    loading,
    error,
    validationResults,
    statistics,
    settings,

    // Действия
    loadDocuments,
    validateDocument,
    loadValidationResult,
    loadStatistics,
    loadSettings,
    saveSettings,
    deleteDocument,
    revalidateDocument,
    batchValidate,
    exportResults,

    // Утилиты
    setError,
    clearError: () => setError(null)
  };
};

export default useNormControl2;


