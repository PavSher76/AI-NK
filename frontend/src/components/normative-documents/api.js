// API сервис для работы с нормативными документами

// Получение списка документов
export const fetchDocuments = async (authToken) => {
  try {
    const response = await fetch('/api/documents', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.documents || data;
    } else {
      console.error('Failed to fetch documents:', response.status);
      return [];
    }
  } catch (error) {
    console.error('Error fetching documents:', error);
    return [];
  }
};

// Получение статистики документов
export const fetchStats = async (authToken) => {
  try {
    // Получаем статистику напрямую от RAG сервиса
    const response = await fetch('/rag/documents/stats');
    
    if (response.ok) {
      const data = await response.json();
      
      // Возвращаем данные в том же формате, что возвращает RAG сервис
      return {
        tokens: data.tokens || 0,
        chunks: data.chunks || 0,
        vectors: data.vectors || 0,
        documents: data.documents || 0,
        timestamp: data.timestamp
      };
    } else {
      console.error('Failed to fetch stats from RAG service:', response.status);
      return null;
    }
  } catch (error) {
    console.error('Error fetching stats from RAG service:', error);
    return null;
  }
};

// Загрузка документа
export const uploadDocument = async (file, category, authToken, onProgress) => {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    const xhr = new XMLHttpRequest();
    
    // Отслеживаем прогресс загрузки
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    });

    // Обрабатываем завершение загрузки
    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        try {
          const result = JSON.parse(xhr.responseText);
          resolve(result);
        } catch (parseError) {
          reject(new Error('Ошибка обработки ответа сервера'));
        }
      } else {
        reject(new Error(`Ошибка загрузки: ${xhr.status} - ${xhr.statusText}`));
      }
    });

    // Обрабатываем ошибки
    xhr.addEventListener('error', () => {
      reject(new Error('Ошибка сети при загрузке файла'));
    });

    // Обрабатываем отмену
    xhr.addEventListener('abort', () => {
      reject(new Error('Загрузка отменена'));
    });

    // Открываем соединение и отправляем данные
    xhr.open('POST', '/api/upload');
    xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
    xhr.send(formData);
  });
};

// Удаление документа
export const deleteDocument = async (documentId, authToken) => {
  try {
    const response = await fetch(`/api/documents/${documentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    return response.ok;
  } catch (error) {
    console.error('Error deleting document:', error);
    return false;
  }
};

// Получение информации о чанках документа
export const fetchDocumentTokens = async (documentId, authToken) => {
  try {
    const response = await fetch(`/api/documents/${documentId}/chunks`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      console.error('Failed to fetch document tokens:', response.status);
      return null;
    }
  } catch (error) {
    console.error('Error fetching document tokens:', error);
    return null;
  }
};

// Реиндексация документов (синхронная)
export const reindexDocuments = async (authToken) => {
  try {
    const response = await fetch('/api/reindex-documents', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Ошибка реиндексации');
    }
  } catch (error) {
    console.error('Error reindexing documents:', error);
    throw error;
  }
};

// Запуск асинхронной реиндексации документов
export const startAsyncReindex = async (authToken) => {
  try {
    const response = await fetch('/api/reindex-documents/async', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Ошибка запуска асинхронной реиндексации');
    }
  } catch (error) {
    console.error('Error starting async reindex:', error);
    throw error;
  }
};

// Получение статуса асинхронной реиндексации
export const getReindexStatus = async (taskId, authToken) => {
  try {
    const response = await fetch(`/api/reindex-documents/status/${taskId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      }
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Ошибка получения статуса реиндексации');
    }
  } catch (error) {
    console.error('Error getting reindex status:', error);
    throw error;
  }
};

// Получение настроек
export const fetchSettings = async (authToken) => {
  try {
    const response = await fetch('/api/settings', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.settings || [];
    } else {
      console.error('Failed to fetch settings:', response.status);
      return [];
    }
  } catch (error) {
    console.error('Error fetching settings:', error);
    return [];
  }
};

// Обновление настройки
export const updateSetting = async (settingKey, newValue, authToken) => {
  try {
    // Сначала пытаемся обновить существующую настройку
    let response = await fetch(`/api/settings/${settingKey}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ setting_value: newValue })
    });
    
    // Если настройка не найдена, создаем новую
    if (response.status === 404) {
      response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          setting_key: settingKey,
          setting_value: newValue,
          setting_type: 'text',
          setting_description: settingKey === 'normcontrol_prompt' ? 'Системный промпт для LLM при проведении проверки нормоконтроля документов' : 'Системная настройка'
        })
      });
    }
    
    return response.ok;
  } catch (error) {
    console.error('Error updating setting:', error);
    return false;
  }
};

// Удаление настройки
export const deleteSetting = async (settingKey, authToken) => {
  try {
    const response = await fetch(`/api/settings/${settingKey}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      }
    });
    
    return response.ok;
  } catch (error) {
    console.error('Error deleting setting:', error);
    return false;
  }
};
