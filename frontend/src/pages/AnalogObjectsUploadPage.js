import React, { useState, useRef } from 'react';
import { 
  Upload, 
  FileText, 
  Image, 
  X, 
  CheckCircle, 
  AlertCircle,
  Download,
  Plus,
  Trash2,
  Eye,
  Building2,
  MapPin,
  Calendar,
  Tag,
  User,
  Phone,
  Mail
} from 'lucide-react';

const AnalogObjectsUploadPage = ({ isAuthenticated, authToken }) => {
  const [uploadMethod, setUploadMethod] = useState('files'); // 'files' или 'form'
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [showTemplate, setShowTemplate] = useState(false);
  const fileInputRef = useRef(null);

  // Форма для ручного ввода
  const [formData, setFormData] = useState({
    name: '',
    type: '',
    region: '',
    city: '',
    year: '',
    status: '',
    area: '',
    floors: '',
    apartments: '',
    developer: '',
    developerContact: '',
    developerPhone: '',
    developerEmail: '',
    description: '',
    characteristics: []
  });

  // Обработка выбора файлов
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    const validFiles = files.filter(file => {
      const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      return validTypes.includes(file.type);
    });

    setSelectedFiles(prev => [...prev, ...validFiles]);
  };

  // Удаление файла
  const handleRemoveFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Обработка загрузки файлов
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress({});
    setUploadResults([]);

    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setUploadProgress(prev => ({ ...prev, [i]: 0 }));

        // Имитация загрузки
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise(resolve => setTimeout(resolve, 100));
          setUploadProgress(prev => ({ ...prev, [i]: progress }));
        }

        // Имитация результата
        const result = {
          fileName: file.name,
          status: Math.random() > 0.1 ? 'success' : 'error',
          message: Math.random() > 0.1 ? 'Файл успешно загружен' : 'Ошибка загрузки файла',
          objectId: Math.random() > 0.1 ? Math.floor(Math.random() * 1000) : null
        };

        setUploadResults(prev => [...prev, result]);
      }
    } catch (error) {
      console.error('Ошибка загрузки:', error);
    } finally {
      setIsUploading(false);
    }
  };

  // Обработка формы
  const handleFormSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.type || !formData.region) {
      alert('Заполните обязательные поля');
      return;
    }

    setIsUploading(true);
    
    try {
      // Имитация отправки формы
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const result = {
        fileName: 'Ручной ввод',
        status: 'success',
        message: 'Объект успешно добавлен',
        objectId: Math.floor(Math.random() * 1000)
      };

      setUploadResults(prev => [...prev, result]);
      
      // Очистка формы
      setFormData({
        name: '',
        type: '',
        region: '',
        city: '',
        year: '',
        status: '',
        area: '',
        floors: '',
        apartments: '',
        developer: '',
        developerContact: '',
        developerPhone: '',
        developerEmail: '',
        description: '',
        characteristics: []
      });
    } catch (error) {
      console.error('Ошибка отправки формы:', error);
    } finally {
      setIsUploading(false);
    }
  };

  // Добавление характеристики
  const addCharacteristic = () => {
    setFormData(prev => ({
      ...prev,
      characteristics: [...prev.characteristics, { name: '', value: '' }]
    }));
  };

  // Удаление характеристики
  const removeCharacteristic = (index) => {
    setFormData(prev => ({
      ...prev,
      characteristics: prev.characteristics.filter((_, i) => i !== index)
    }));
  };

  // Обновление характеристики
  const updateCharacteristic = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      characteristics: prev.characteristics.map((char, i) => 
        i === index ? { ...char, [field]: value } : char
      )
    }));
  };

  // Скачивание шаблона
  const downloadTemplate = () => {
    const csvContent = [
      ['Название', 'Тип', 'Регион', 'Город', 'Год', 'Статус', 'Площадь', 'Этажи', 'Квартиры', 'Застройщик', 'Контактное лицо', 'Телефон', 'Email', 'Описание'],
      ['Жилой комплекс "Пример"', 'Жилой', 'Московская область', 'Химки', '2023', 'Завершен', '45000', '25', '320', 'ООО "Примерстрой"', 'Иванов И.И.', '+7(495)123-45-67', 'info@example.ru', 'Описание объекта']
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'analog_objects_template.csv';
    link.click();
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Пакетная загрузка объектов аналогов</h1>
        <p className="text-gray-600 mt-1">Загрузите файлы с данными об объектах или заполните форму вручную</p>
      </div>

      {/* Выбор метода загрузки */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Способ загрузки</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => setUploadMethod('files')}
            className={`p-4 rounded-lg border-2 transition-all ${
              uploadMethod === 'files' 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-3">
              <Upload className="w-6 h-6 text-primary-600" />
              <div className="text-left">
                <h3 className="font-medium text-gray-900">Загрузка файлов</h3>
                <p className="text-sm text-gray-500">CSV, Excel, PDF, изображения</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => setUploadMethod('form')}
            className={`p-4 rounded-lg border-2 transition-all ${
              uploadMethod === 'form' 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-3">
              <FileText className="w-6 h-6 text-primary-600" />
              <div className="text-left">
                <h3 className="font-medium text-gray-900">Ручной ввод</h3>
                <p className="text-sm text-gray-500">Заполнение формы</p>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Загрузка файлов */}
      {uploadMethod === 'files' && (
        <div className="space-y-6">
          {/* Область загрузки */}
          <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition-colors">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Перетащите файлы сюда</h3>
              <p className="text-gray-500 mb-4">или</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Выберите файлы
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".csv,.xlsx,.xls,.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif"
                onChange={handleFileSelect}
                className="hidden"
              />
              <p className="text-sm text-gray-400 mt-2">
                Поддерживаются: CSV, Excel, PDF, Word, изображения
              </p>
            </div>
          </div>

          {/* Список выбранных файлов */}
          {selectedFiles.length > 0 && (
            <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Выбранные файлы</h3>
              <div className="space-y-3">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {uploadProgress[index] !== undefined && (
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-primary-600 h-2 rounded-full transition-all"
                            style={{ width: `${uploadProgress[index]}%` }}
                          />
                        </div>
                      )}
                      <button
                        onClick={() => handleRemoveFile(index)}
                        className="p-1 text-gray-400 hover:text-red-600"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 flex items-center justify-between">
                <button
                  onClick={downloadTemplate}
                  className="flex items-center text-sm text-gray-600 hover:text-gray-800"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Скачать шаблон CSV
                </button>
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? 'Загрузка...' : 'Загрузить файлы'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Форма ручного ввода */}
      {uploadMethod === 'form' && (
        <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Информация об объекте</h3>
          
          <form onSubmit={handleFormSubmit} className="space-y-6">
            {/* Основная информация */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Название объекта *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Жилой комплекс 'Северный'"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Тип объекта *
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  required
                >
                  <option value="">Выберите тип</option>
                  <option value="Жилой">Жилой</option>
                  <option value="Коммерческий">Коммерческий</option>
                  <option value="Промышленный">Промышленный</option>
                  <option value="Социальный">Социальный</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Регион *
                </label>
                <input
                  type="text"
                  value={formData.region}
                  onChange={(e) => setFormData(prev => ({ ...prev, region: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Московская область"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Город
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Химки"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Год постройки
                </label>
                <input
                  type="number"
                  value={formData.year}
                  onChange={(e) => setFormData(prev => ({ ...prev, year: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="2023"
                  min="1900"
                  max="2030"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Статус
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Выберите статус</option>
                  <option value="Проектируется">Проектируется</option>
                  <option value="Строится">Строится</option>
                  <option value="Завершен">Завершен</option>
                  <option value="В эксплуатации">В эксплуатации</option>
                </select>
              </div>
            </div>

            {/* Технические характеристики */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-4">Технические характеристики</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Площадь (м²)
                  </label>
                  <input
                    type="number"
                    value={formData.area}
                    onChange={(e) => setFormData(prev => ({ ...prev, area: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="45000"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Количество этажей
                  </label>
                  <input
                    type="number"
                    value={formData.floors}
                    onChange={(e) => setFormData(prev => ({ ...prev, floors: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="25"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Количество квартир
                  </label>
                  <input
                    type="number"
                    value={formData.apartments}
                    onChange={(e) => setFormData(prev => ({ ...prev, apartments: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="320"
                  />
                </div>
              </div>
            </div>

            {/* Информация о застройщике */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-4">Информация о застройщике</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Название компании
                  </label>
                  <input
                    type="text"
                    value={formData.developer}
                    onChange={(e) => setFormData(prev => ({ ...prev, developer: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="ООО 'Северстрой'"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Контактное лицо
                  </label>
                  <input
                    type="text"
                    value={formData.developerContact}
                    onChange={(e) => setFormData(prev => ({ ...prev, developerContact: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Иванов И.И."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Телефон
                  </label>
                  <input
                    type="tel"
                    value={formData.developerPhone}
                    onChange={(e) => setFormData(prev => ({ ...prev, developerPhone: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="+7(495)123-45-67"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.developerEmail}
                    onChange={(e) => setFormData(prev => ({ ...prev, developerEmail: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="info@example.ru"
                  />
                </div>
              </div>
            </div>

            {/* Дополнительные характеристики */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-medium text-gray-900">Дополнительные характеристики</h4>
                <button
                  type="button"
                  onClick={addCharacteristic}
                  className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Добавить характеристику
                </button>
              </div>
              
              <div className="space-y-3">
                {formData.characteristics.map((char, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <input
                      type="text"
                      value={char.name}
                      onChange={(e) => updateCharacteristic(index, 'name', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Название характеристики"
                    />
                    <input
                      type="text"
                      value={char.value}
                      onChange={(e) => updateCharacteristic(index, 'value', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Значение"
                    />
                    <button
                      type="button"
                      onClick={() => removeCharacteristic(index)}
                      className="p-2 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Описание */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Описание объекта
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Подробное описание объекта..."
              />
            </div>

            {/* Кнопки */}
            <div className="flex items-center justify-end space-x-4">
              <button
                type="button"
                onClick={() => setFormData({
                  name: '', type: '', region: '', city: '', year: '', status: '',
                  area: '', floors: '', apartments: '', developer: '', developerContact: '',
                  developerPhone: '', developerEmail: '', description: '', characteristics: []
                })}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Очистить
              </button>
              <button
                type="submit"
                disabled={isUploading}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? 'Сохранение...' : 'Сохранить объект'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Результаты загрузки */}
      {uploadResults.length > 0 && (
        <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Результаты загрузки</h3>
          <div className="space-y-3">
            {uploadResults.map((result, index) => (
              <div key={index} className={`flex items-center justify-between p-3 rounded-lg ${
                result.status === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-center space-x-3">
                  {result.status === 'success' ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-600" />
                  )}
                  <div>
                    <p className="font-medium text-gray-900">{result.fileName}</p>
                    <p className={`text-sm ${
                      result.status === 'success' ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {result.message}
                    </p>
                  </div>
                </div>
                {result.objectId && (
                  <span className="text-sm text-gray-500">ID: {result.objectId}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalogObjectsUploadPage;
