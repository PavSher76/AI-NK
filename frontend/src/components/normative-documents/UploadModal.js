import React from 'react';
import { 
  Upload, 
  AlertCircle, 
  CheckCircle, 
  Loader2, 
  X 
} from 'lucide-react';
import { categories, supportedFormats } from './utils';

const UploadModal = ({
  isOpen,
  onClose,
  file,
  setFile,
  selectedCategory,
  setSelectedCategory,
  isUploading,
  uploadProgress,
  uploadStage,
  uploadError,
  uploadSuccess,
  onUpload,
  icons
}) => {
  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    // Проверяем формат файла
    const fileExtension = selectedFile.name.split('.').pop().toLowerCase();
    const isSupported = supportedFormats.some(format => format.ext === fileExtension);

    if (isSupported) {
      setFile(selectedFile);
    } else {
      alert('Неподдерживаемый формат файла');
      setFile(null);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Загрузка документа</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
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
          
          {/* Прогресс загрузки */}
          {isUploading && (
            <div className="space-y-3">
              <div className="flex justify-between text-sm text-gray-600">
                <span className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>
                    {uploadStage === 'upload' ? 'Загрузка файла...' : 'Обработка документа...'}
                  </span>
                </span>
                <span className="font-medium">{uploadProgress}%</span>
              </div>
              
              {/* Прогресс-бар */}
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div 
                  className={`h-3 rounded-full transition-all duration-300 ${
                    uploadStage === 'upload' ? 'bg-blue-600' : 'bg-green-600'
                  }`}
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              
              {/* Дополнительная информация */}
              <div className="text-xs text-gray-500">
                {uploadStage === 'upload' ? (
                  <span>Отправка файла на сервер...</span>
                ) : (
                  <span>Парсинг документа и индексация...</span>
                )}
              </div>
            </div>
          )}
          
          {/* Кнопки */}
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Отмена
            </button>
            <button
              onClick={onUpload}
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
  );
};

export default UploadModal;
