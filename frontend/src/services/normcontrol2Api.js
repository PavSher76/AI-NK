/**
 * API сервис для модуля Нормоконтроль - 2
 */

const API_BASE = process.env.REACT_APP_API_BASE || '/api';

class NormControl2Api {
  constructor() {
    this.baseUrl = `${API_BASE}/normcontrol2`;
  }

  /**
   * Выполнение HTTP запроса
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text();
      }
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Выполнение HTTP запроса с авторизацией
   */
  async authenticatedRequest(endpoint, options = {}, authToken) {
    if (!authToken) {
      throw new Error('Требуется токен авторизации');
    }

    return this.request(endpoint, {
      ...options,
      headers: {
        'Authorization': `Bearer ${authToken}`,
        ...options.headers
      }
    });
  }

  /**
   * Валидация документа
   */
  async validateDocument(file, options = {}, authToken) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('validation_options', JSON.stringify(options));

    const url = `${this.baseUrl}/validate`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Ошибка валидации: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * Получение списка документов
   */
  async getDocuments(authToken) {
    return this.authenticatedRequest('/documents', {}, authToken);
  }

  /**
   * Получение проблем документа
   */
  async getDocumentIssues(documentId, authToken) {
    return this.authenticatedRequest(`/validate/${documentId}/issues`, {}, authToken);
  }

  /**
   * Получение статуса валидации документа
   */
  async getDocumentStatus(documentId, authToken) {
    return this.authenticatedRequest(`/validate/${documentId}/status`, {}, authToken);
  }

  /**
   * Получение отчета о валидации документа
   */
  async getDocumentReport(documentId, authToken) {
    return this.authenticatedRequest(`/validate/${documentId}/report`, {}, authToken);
  }

  /**
   * Пакетная валидация документов
   */
  async batchValidate(filePaths, options = {}, authToken) {
    const formData = new FormData();
    filePaths.forEach((path, index) => {
      formData.append(`file_paths[${index}]`, path);
    });
    formData.append('validation_options', JSON.stringify(options));

    const url = `${this.baseUrl}/batch_validate`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Ошибка пакетной валидации: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * Получение статистики валидации
   */
  async getStatistics(authToken) {
    return this.authenticatedRequest('/statistics', {}, authToken);
  }

  /**
   * Получение правил валидации
   */
  async getValidationRules(authToken) {
    return this.authenticatedRequest('/rules', {}, authToken);
  }

  /**
   * Получение настроек
   */
  async getSettings(authToken) {
    return this.authenticatedRequest('/settings', {}, authToken);
  }

  /**
   * Сохранение настроек
   */
  async saveSettings(settings, authToken) {
    return this.authenticatedRequest('/settings', {
      method: 'POST',
      body: JSON.stringify({ settings })
    }, authToken);
  }

  /**
   * Проверка состояния сервиса
   */
  async getHealthStatus() {
    return this.request('/health');
  }

  /**
   * Удаление документа
   */
  async deleteDocument(documentId, authToken) {
    return this.authenticatedRequest(`/documents/${documentId}`, {
      method: 'DELETE'
    }, authToken);
  }

  /**
   * Повторная валидация документа
   */
  async revalidateDocument(documentId, options = {}, authToken) {
    return this.authenticatedRequest(`/validate/${documentId}/revalidate`, {
      method: 'POST',
      body: JSON.stringify({ options })
    }, authToken);
  }

  /**
   * Экспорт результатов валидации
   */
  async exportResults(documentId, format = 'json', authToken) {
    const response = await fetch(`${this.baseUrl}/validate/${documentId}/export?format=${format}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (!response.ok) {
      throw new Error(`Ошибка экспорта: ${response.status}`);
    }

    return await response.blob();
  }

  /**
   * Получение истории валидаций
   */
  async getValidationHistory(documentId, authToken) {
    return this.authenticatedRequest(`/validate/${documentId}/history`, {}, authToken);
  }

  /**
   * Получение метрик производительности
   */
  async getPerformanceMetrics(authToken) {
    return this.authenticatedRequest('/metrics', {}, authToken);
  }

  /**
   * Получение логов валидации
   */
  async getValidationLogs(documentId, authToken) {
    return this.authenticatedRequest(`/validate/${documentId}/logs`, {}, authToken);
  }

  /**
   * Создание задачи валидации
   */
  async createValidationTask(filePath, options = {}, authToken) {
    return this.authenticatedRequest('/tasks', {
      method: 'POST',
      body: JSON.stringify({
        file_path: filePath,
        options
      })
    }, authToken);
  }

  /**
   * Получение статуса задачи
   */
  async getTaskStatus(taskId, authToken) {
    return this.authenticatedRequest(`/tasks/${taskId}/status`, {}, authToken);
  }

  /**
   * Отмена задачи
   */
  async cancelTask(taskId, authToken) {
    return this.authenticatedRequest(`/tasks/${taskId}/cancel`, {
      method: 'POST'
    }, authToken);
  }
}

// Создаем экземпляр API
const normControl2Api = new NormControl2Api();

export default normControl2Api;


