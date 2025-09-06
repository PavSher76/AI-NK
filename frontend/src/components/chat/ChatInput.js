import React, { useState, useRef } from 'react';
import { Send, Paperclip, X, AlertTriangle } from 'lucide-react';

const ChatInput = ({ 
  onSendMessage, 
  onSendMessageWithFile, 
  isLoading, 
  error 
}) => {
  const [inputValue, setInputValue] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileUploading, setFileUploading] = useState(false);
  const [fileUploadProgress, setFileUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (isLoading || fileUploading) return;
    
    if (selectedFile) {
      await handleFileUpload();
    } else if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    try {
      setFileUploading(true);
      setFileUploadProgress(0);
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('message', inputValue || 'Обработай этот файл');
      
      await onSendMessageWithFile(formData, selectedFile.name);
      
      setSelectedFile(null);
      setInputValue('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
    } catch (error) {
      console.error('Ошибка загрузки файла:', error);
    } finally {
      setFileUploading(false);
      setFileUploadProgress(0);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/msword',
        'application/vnd.ms-excel',
        'text/plain',
        'text/markdown'
      ];
      
      if (allowedTypes.includes(file.type)) {
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
          alert('Файл слишком большой. Максимальный размер: 100MB');
          return;
        }
        
        setSelectedFile(file);
      } else {
        alert('Поддерживаются только файлы PDF, Word, Excel, TXT и Markdown');
      }
    }
  };

  const removeSelectedFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileIcon = (fileType) => {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word') || fileType.includes('document')) return '📝';
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '📊';
    return '📎';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-6 border-t border-gray-100">
      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-error-50 border border-error-200 rounded-xl">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-error-600" />
            <p className="text-error-700 text-sm font-medium">{error}</p>
          </div>
        </div>
      )}

      {/* Выбранный файл */}
      {selectedFile && (
        <div className="mb-4 p-4 bg-primary-50 rounded-xl border border-primary-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-lg">{getFileIcon(selectedFile.type)}</span>
              <div>
                <p className="text-sm font-medium text-primary-900">{selectedFile.name}</p>
                <p className="text-xs text-primary-600">{formatFileSize(selectedFile.size)}</p>
                <p className="text-xs text-primary-500 mt-1">
                  ⚠️ Большие файлы могут быть обрезаны до 10000 символов
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={removeSelectedFile}
              className="p-1 text-primary-400 hover:text-primary-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Предупреждение о больших файлах */}
      {selectedFile && selectedFile.size > 10 * 1024 * 1024 && (
        <div className="bg-warning-50 border border-warning-200 rounded-xl p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-warning-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-warning-800">
                ⚠️ Большие файлы
              </h3>
              <div className="mt-2 text-sm text-warning-700">
                <p>
                  Файлы размером более 10МБ могут обрабатываться дольше. 
                  Система поддерживает файлы до 100МБ.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Прогресс загрузки файла */}
      {fileUploading && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>Загрузка файла...</span>
            <span>{fileUploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${fileUploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Форма ввода */}
      <form onSubmit={handleSubmit} className="flex space-x-3">
        {/* Кнопка прикрепления файла */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || fileUploading}
          className="p-3 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-xl transition-all duration-300 disabled:opacity-50 group"
          title="Прикрепить файл"
        >
          <Paperclip className="w-5 h-5 group-hover:scale-110 transition-transform" />
        </button>
        
        {/* Скрытый input для файлов */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.docx,.doc,.xlsx,.xls"
          className="hidden"
          disabled={isLoading || fileUploading}
        />

        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={selectedFile ? "Опишите, что нужно сделать с файлом..." : "Введите сообщение..."}
          className="input-field flex-1"
          disabled={isLoading || fileUploading}
        />
        <button
          type="submit"
          disabled={(!inputValue.trim() && !selectedFile) || isLoading || fileUploading}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <Send className="w-4 h-4" />
          <span>Отправить</span>
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
