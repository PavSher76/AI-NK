// Утилиты для работы с нормативными документами

// Категории документов
export const categories = [
  { value: 'gost', label: 'ГОСТ', color: 'bg-red-100 text-red-800' },
  { value: 'sp', label: 'СП', color: 'bg-blue-100 text-blue-800' },
  { value: 'snip', label: 'СНиП', color: 'bg-green-100 text-green-800' },
  { value: 'tr', label: 'ТР', color: 'bg-purple-100 text-purple-800' },
  { value: 'corporate', label: 'Корпоративные', color: 'bg-orange-100 text-orange-800' },
  { value: 'other', label: 'Прочие', color: 'bg-gray-100 text-gray-800' }
];

// Статусы документов
export const statuses = [
  { value: 'uploaded', label: 'Загружен', color: 'bg-blue-100 text-blue-800' },
  { value: 'processing', label: 'Обрабатывается', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'indexed', label: 'Проиндексирован', color: 'bg-green-100 text-green-800' },
  { value: 'error', label: 'Ошибка', color: 'bg-red-100 text-red-800' }
];

// Поддерживаемые форматы файлов
export const supportedFormats = [
  { ext: 'pdf', name: 'PDF документ', icon: 'FileText' },
  { ext: 'docx', name: 'Word документ', icon: 'FileText' },
  { ext: 'dwg', name: 'AutoCAD чертеж', icon: 'FileImage' },
  { ext: 'ifc', name: 'IFC модель', icon: 'FileCode' },
  { ext: 'txt', name: 'Текстовый файл', icon: 'FileText' }
];

// Получение иконки типа файла
export const getFileIcon = (fileType, icons) => {
  if (!fileType) return icons.File;
  const format = supportedFormats.find(f => f.ext === fileType.toLowerCase());
  return format ? icons[format.icon] : icons.File;
};

// Получение названия типа файла
export const getFileTypeName = (fileType) => {
  if (!fileType) return 'Неизвестный тип';
  const format = supportedFormats.find(f => f.ext === fileType.toLowerCase());
  return format ? format.name : fileType.toUpperCase();
};

// Получение категории документа
export const getCategoryInfo = (category) => {
  return categories.find(c => c.value === category) || categories[categories.length - 1];
};

// Получение статуса документа
export const getStatusInfo = (status) => {
  return statuses.find(s => s.value === status) || statuses[0];
};

// Фильтрация документов
export const filterDocuments = (documents, searchQuery, filterCategory, filterStatus) => {
  return documents.filter(doc => {
    // Безопасная проверка полей документа
    const filename = doc.original_filename || doc.title || doc.document_title || '';
    const fileType = doc.file_type || doc.type || '';
    
    const matchesSearch = filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         fileType.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !filterCategory || (doc.category || 'other') === filterCategory;
    const matchesStatus = !filterStatus || (doc.status || doc.processing_status || 'uploaded') === filterStatus;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });
};

// Сортировка документов
export const sortDocuments = (documents, sortBy, sortDirection = 'asc') => {
  return [...documents].sort((a, b) => {
    let result = 0;
    
    switch (sortBy) {
      case 'upload_date':
        result = new Date(b.upload_date || 0) - new Date(a.upload_date || 0);
        break;
      case 'filename':
        const filenameA = (a.original_filename || a.title || a.document_title || '').toLowerCase();
        const filenameB = (b.original_filename || b.title || b.document_title || '').toLowerCase();
        result = filenameA.localeCompare(filenameB, 'ru-RU', { numeric: true, sensitivity: 'base' });
        break;
      case 'file_size':
        result = (b.chunks_count || b.file_size || 0) - (a.chunks_count || a.file_size || 0);
        break;
      case 'category':
        result = (a.category || '').localeCompare(b.category || '', 'ru-RU');
        break;
      default:
        result = 0;
    }
    
    // Применяем направление сортировки
    return sortDirection === 'desc' ? -result : result;
  });
};
