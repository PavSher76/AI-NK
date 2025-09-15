import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Upload, 
  Search, 
  BarChart3, 
  Plus,
  Filter,
  Download,
  Eye,
  Edit,
  Trash2,
  MapPin,
  Calendar,
  Tag,
  FileText,
  Image,
  ChevronRight,
  ChevronDown
} from 'lucide-react';

const AnalogObjectsPage = ({ isAuthenticated, authToken }) => {
  const [activeTab, setActiveTab] = useState('list');
  const [objects, setObjects] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    type: '',
    region: '',
    year: '',
    status: ''
  });
  const [selectedObjects, setSelectedObjects] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  // Загрузка объектов аналогов
  const loadObjects = async () => {
    setIsLoading(true);
    try {
      // Здесь будет API запрос для загрузки объектов
      // Пока используем моковые данные
      const mockObjects = [
        {
          id: 1,
          name: 'Жилой комплекс "Северный"',
          type: 'Жилой',
          region: 'Московская область',
          city: 'Химки',
          year: 2023,
          status: 'Завершен',
          area: 45000,
          floors: 25,
          apartments: 320,
          developer: 'ООО "Северстрой"',
          description: 'Многоэтажный жилой комплекс с развитой инфраструктурой',
          images: ['/images/analog1.jpg'],
          documents: ['/docs/analog1.pdf'],
          coordinates: { lat: 55.7558, lng: 37.6176 },
          characteristics: {
            'Площадь застройки': '12000 м²',
            'Общая площадь': '45000 м²',
            'Количество этажей': '25',
            'Количество квартир': '320',
            'Парковочные места': '400'
          }
        },
        {
          id: 2,
          name: 'Бизнес-центр "Деловой"',
          type: 'Коммерческий',
          region: 'Москва',
          city: 'Москва',
          year: 2022,
          status: 'В эксплуатации',
          area: 25000,
          floors: 15,
          developer: 'ООО "Деловые центры"',
          description: 'Современный бизнес-центр класса А',
          images: ['/images/analog2.jpg'],
          documents: ['/docs/analog2.pdf'],
          coordinates: { lat: 55.7558, lng: 37.6176 },
          characteristics: {
            'Площадь застройки': '8000 м²',
            'Общая площадь': '25000 м²',
            'Количество этажей': '15',
            'Офисные помещения': '20000 м²',
            'Парковочные места': '150'
          }
        }
      ];
      
      setObjects(mockObjects);
    } catch (error) {
      console.error('Ошибка загрузки объектов:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadObjects();
  }, []);

  // Фильтрация объектов
  const filteredObjects = objects.filter(obj => {
    const matchesSearch = obj.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         obj.city.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         obj.developer.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesFilters = (!filters.type || obj.type === filters.type) &&
                          (!filters.region || obj.region === filters.region) &&
                          (!filters.year || obj.year.toString() === filters.year) &&
                          (!filters.status || obj.status === filters.status);
    
    return matchesSearch && matchesFilters;
  });

  // Обработка выбора объектов
  const handleObjectSelect = (objectId) => {
    setSelectedObjects(prev => 
      prev.includes(objectId) 
        ? prev.filter(id => id !== objectId)
        : [...prev, objectId]
    );
  };

  // Обработка выбора всех объектов
  const handleSelectAll = () => {
    if (selectedObjects.length === filteredObjects.length) {
      setSelectedObjects([]);
    } else {
      setSelectedObjects(filteredObjects.map(obj => obj.id));
    }
  };

  // Удаление выбранных объектов
  const handleDeleteSelected = async () => {
    if (selectedObjects.length === 0) return;
    
    if (window.confirm(`Удалить ${selectedObjects.length} выбранных объектов?`)) {
      try {
        // API запрос для удаления
        setObjects(prev => prev.filter(obj => !selectedObjects.includes(obj.id)));
        setSelectedObjects([]);
      } catch (error) {
        console.error('Ошибка удаления объектов:', error);
      }
    }
  };

  // Экспорт данных
  const handleExport = () => {
    const dataToExport = selectedObjects.length > 0 
      ? objects.filter(obj => selectedObjects.includes(obj.id))
      : filteredObjects;
    
    const csvContent = [
      ['Название', 'Тип', 'Регион', 'Город', 'Год', 'Статус', 'Площадь', 'Этажи', 'Застройщик'],
      ...dataToExport.map(obj => [
        obj.name,
        obj.type,
        obj.region,
        obj.city,
        obj.year,
        obj.status,
        obj.area,
        obj.floors || '-',
        obj.developer
      ])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'analog_objects.csv';
    link.click();
  };

  const renderObjectCard = (obj) => (
    <div key={obj.id} className="bg-white rounded-xl shadow-soft border border-gray-100 hover:shadow-glow transition-all duration-300 overflow-hidden">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={selectedObjects.includes(obj.id)}
              onChange={() => handleObjectSelect(obj.id)}
              className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
            />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">{obj.name}</h3>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span className="flex items-center">
                  <MapPin className="w-4 h-4 mr-1" />
                  {obj.city}, {obj.region}
                </span>
                <span className="flex items-center">
                  <Calendar className="w-4 h-4 mr-1" />
                  {obj.year}
                </span>
                <span className="flex items-center">
                  <Tag className="w-4 h-4 mr-1" />
                  {obj.type}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              obj.status === 'Завершен' ? 'bg-green-100 text-green-800' :
              obj.status === 'В эксплуатации' ? 'bg-blue-100 text-blue-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              {obj.status}
            </span>
          </div>
        </div>

        <p className="text-gray-600 mb-4">{obj.description}</p>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <span className="text-sm text-gray-500">Площадь:</span>
            <p className="font-medium">{obj.area.toLocaleString()} м²</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Этажи:</span>
            <p className="font-medium">{obj.floors || '-'}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Застройщик:</span>
            <p className="font-medium">{obj.developer}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Квартиры:</span>
            <p className="font-medium">{obj.apartments || '-'}</p>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex items-center space-x-2">
            {obj.images && obj.images.length > 0 && (
              <button className="flex items-center text-sm text-gray-500 hover:text-gray-700">
                <Image className="w-4 h-4 mr-1" />
                {obj.images.length} фото
              </button>
            )}
            {obj.documents && obj.documents.length > 0 && (
              <button className="flex items-center text-sm text-gray-500 hover:text-gray-700">
                <FileText className="w-4 h-4 mr-1" />
                {obj.documents.length} документов
              </button>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <Eye className="w-4 h-4" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <Edit className="w-4 h-4" />
            </button>
            <button className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderFilters = () => (
    <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Фильтры</h3>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center text-sm text-gray-500 hover:text-gray-700"
        >
          {showFilters ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          {showFilters ? 'Скрыть' : 'Показать'} фильтры
        </button>
      </div>
      
      {showFilters && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Тип объекта</label>
            <select
              value={filters.type}
              onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все типы</option>
              <option value="Жилой">Жилой</option>
              <option value="Коммерческий">Коммерческий</option>
              <option value="Промышленный">Промышленный</option>
              <option value="Социальный">Социальный</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Регион</label>
            <select
              value={filters.region}
              onChange={(e) => setFilters(prev => ({ ...prev, region: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все регионы</option>
              <option value="Москва">Москва</option>
              <option value="Московская область">Московская область</option>
              <option value="Санкт-Петербург">Санкт-Петербург</option>
              <option value="Ленинградская область">Ленинградская область</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Год</label>
            <select
              value={filters.year}
              onChange={(e) => setFilters(prev => ({ ...prev, year: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все годы</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
              <option value="2022">2022</option>
              <option value="2021">2021</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Статус</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все статусы</option>
              <option value="Завершен">Завершен</option>
              <option value="В эксплуатации">В эксплуатации</option>
              <option value="Строится">Строится</option>
              <option value="Проектируется">Проектируется</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Заголовок и действия */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Объекты аналоги</h1>
          <p className="text-gray-600 mt-1">База данных объектов аналогов для сравнения и анализа</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleExport}
            disabled={filteredObjects.length === 0}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4 mr-2" />
            Экспорт
          </button>
          <button className="flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700">
            <Plus className="w-4 h-4 mr-2" />
            Добавить объект
          </button>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Building2 className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Всего объектов</p>
              <p className="text-2xl font-bold text-gray-900">{objects.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <BarChart3 className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Завершено</p>
              <p className="text-2xl font-bold text-gray-900">
                {objects.filter(obj => obj.status === 'Завершен').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Calendar className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">В этом году</p>
              <p className="text-2xl font-bold text-gray-900">
                {objects.filter(obj => obj.year === 2024).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-lg">
              <MapPin className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Регионов</p>
              <p className="text-2xl font-bold text-gray-900">
                {new Set(objects.map(obj => obj.region)).size}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Поиск и фильтры */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Поиск по названию, городу, застройщику..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            <Filter className="w-4 h-4 mr-2" />
            Фильтры
          </button>
        </div>
        
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Тип объекта</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Все типы</option>
                <option value="Жилой">Жилой</option>
                <option value="Коммерческий">Коммерческий</option>
                <option value="Промышленный">Промышленный</option>
                <option value="Социальный">Социальный</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Регион</label>
              <select
                value={filters.region}
                onChange={(e) => setFilters(prev => ({ ...prev, region: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Все регионы</option>
                <option value="Москва">Москва</option>
                <option value="Московская область">Московская область</option>
                <option value="Санкт-Петербург">Санкт-Петербург</option>
                <option value="Ленинградская область">Ленинградская область</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Год</label>
              <select
                value={filters.year}
                onChange={(e) => setFilters(prev => ({ ...prev, year: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Все годы</option>
                <option value="2024">2024</option>
                <option value="2023">2023</option>
                <option value="2022">2022</option>
                <option value="2021">2021</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Статус</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Все статусы</option>
                <option value="Завершен">Завершен</option>
                <option value="В эксплуатации">В эксплуатации</option>
                <option value="Строится">Строится</option>
                <option value="Проектируется">Проектируется</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Действия с выбранными объектами */}
      {selectedObjects.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-800">
              Выбрано объектов: {selectedObjects.length}
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleDeleteSelected}
                className="px-3 py-1 text-sm font-medium text-red-700 bg-red-100 rounded-lg hover:bg-red-200"
              >
                Удалить
              </button>
              <button
                onClick={handleExport}
                className="px-3 py-1 text-sm font-medium text-blue-700 bg-blue-100 rounded-lg hover:bg-blue-200"
              >
                Экспорт выбранных
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Список объектов */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Найдено объектов: {filteredObjects.length}
          </h2>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={selectedObjects.length === filteredObjects.length && filteredObjects.length > 0}
              onChange={handleSelectAll}
              className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-500">Выбрать все</span>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : filteredObjects.length === 0 ? (
          <div className="text-center py-12">
            <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Объекты не найдены</h3>
            <p className="text-gray-500">Попробуйте изменить параметры поиска или фильтры</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredObjects.map(renderObjectCard)}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalogObjectsPage;
