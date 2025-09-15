import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  MapPin, 
  Calendar, 
  Tag, 
  Building2,
  BarChart3,
  TrendingUp,
  Users,
  DollarSign,
  Ruler,
  Eye,
  Download,
  Share2,
  Star,
  ChevronDown,
  ChevronRight,
  X
} from 'lucide-react';

const AnalogObjectsSearchPage = ({ isAuthenticated, authToken }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [filters, setFilters] = useState({
    type: '',
    region: '',
    yearFrom: '',
    yearTo: '',
    areaFrom: '',
    areaTo: '',
    floorsFrom: '',
    floorsTo: '',
    priceFrom: '',
    priceTo: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('relevance');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' или 'list'
  const [selectedObjects, setSelectedObjects] = useState([]);
  const [comparisonMode, setComparisonMode] = useState(false);

  // Моковые данные для демонстрации
  const mockResults = [
    {
      id: 1,
      name: 'Жилой комплекс "Северный"',
      type: 'Жилой',
      region: 'Московская область',
      city: 'Химки',
      year: 2023,
      area: 45000,
      floors: 25,
      apartments: 320,
      price: 85000,
      developer: 'ООО "Северстрой"',
      description: 'Многоэтажный жилой комплекс с развитой инфраструктурой',
      images: ['/images/analog1.jpg'],
      coordinates: { lat: 55.7558, lng: 37.6176 },
      characteristics: {
        'Площадь застройки': '12000 м²',
        'Общая площадь': '45000 м²',
        'Количество этажей': '25',
        'Количество квартир': '320',
        'Парковочные места': '400',
        'Стоимость за м²': '85000 ₽'
      },
      similarity: 95,
      rating: 4.8
    },
    {
      id: 2,
      name: 'Бизнес-центр "Деловой"',
      type: 'Коммерческий',
      region: 'Москва',
      city: 'Москва',
      year: 2022,
      area: 25000,
      floors: 15,
      price: 120000,
      developer: 'ООО "Деловые центры"',
      description: 'Современный бизнес-центр класса А',
      images: ['/images/analog2.jpg'],
      coordinates: { lat: 55.7558, lng: 37.6176 },
      characteristics: {
        'Площадь застройки': '8000 м²',
        'Общая площадь': '25000 м²',
        'Количество этажей': '15',
        'Офисные помещения': '20000 м²',
        'Парковочные места': '150',
        'Стоимость за м²': '120000 ₽'
      },
      similarity: 87,
      rating: 4.6
    },
    {
      id: 3,
      name: 'Жилой дом "Солнечный"',
      type: 'Жилой',
      region: 'Санкт-Петербург',
      city: 'Санкт-Петербург',
      year: 2021,
      area: 32000,
      floors: 18,
      apartments: 240,
      price: 78000,
      developer: 'ООО "Солнечный дом"',
      description: 'Энергоэффективный жилой дом с современными технологиями',
      images: ['/images/analog3.jpg'],
      coordinates: { lat: 59.9311, lng: 30.3609 },
      characteristics: {
        'Площадь застройки': '9000 м²',
        'Общая площадь': '32000 м²',
        'Количество этажей': '18',
        'Количество квартир': '240',
        'Парковочные места': '300',
        'Стоимость за м²': '78000 ₽'
      },
      similarity: 82,
      rating: 4.7
    }
  ];

  // Выполнение поиска
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    
    try {
      // Имитация API запроса
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Фильтрация результатов
      let filtered = mockResults.filter(obj => {
        const matchesQuery = obj.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           obj.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           obj.developer.toLowerCase().includes(searchQuery.toLowerCase());
        
        const matchesFilters = (!filters.type || obj.type === filters.type) &&
                              (!filters.region || obj.region === filters.region) &&
                              (!filters.yearFrom || obj.year >= parseInt(filters.yearFrom)) &&
                              (!filters.yearTo || obj.year <= parseInt(filters.yearTo)) &&
                              (!filters.areaFrom || obj.area >= parseInt(filters.areaFrom)) &&
                              (!filters.areaTo || obj.area <= parseInt(filters.areaTo)) &&
                              (!filters.floorsFrom || obj.floors >= parseInt(filters.floorsFrom)) &&
                              (!filters.floorsTo || obj.floors <= parseInt(filters.floorsTo)) &&
                              (!filters.priceFrom || obj.price >= parseInt(filters.priceFrom)) &&
                              (!filters.priceTo || obj.price <= parseInt(filters.priceTo));
        
        return matchesQuery && matchesFilters;
      });

      // Сортировка
      switch (sortBy) {
        case 'year':
          filtered.sort((a, b) => b.year - a.year);
          break;
        case 'area':
          filtered.sort((a, b) => b.area - a.area);
          break;
        case 'price':
          filtered.sort((a, b) => b.price - a.price);
          break;
        case 'similarity':
          filtered.sort((a, b) => b.similarity - a.similarity);
          break;
        default:
          // По релевантности (уже отсортировано)
          break;
      }

      setSearchResults(filtered);
    } catch (error) {
      console.error('Ошибка поиска:', error);
    } finally {
      setIsSearching(false);
    }
  };

  // Обработка выбора объекта для сравнения
  const handleObjectSelect = (objectId) => {
    setSelectedObjects(prev => 
      prev.includes(objectId) 
        ? prev.filter(id => id !== objectId)
        : [...prev, objectId]
    );
  };

  // Очистка фильтров
  const clearFilters = () => {
    setFilters({
      type: '',
      region: '',
      yearFrom: '',
      yearTo: '',
      areaFrom: '',
      areaTo: '',
      floorsFrom: '',
      floorsTo: '',
      priceFrom: '',
      priceTo: ''
    });
  };

  // Экспорт результатов
  const handleExport = () => {
    const dataToExport = selectedObjects.length > 0 
      ? searchResults.filter(obj => selectedObjects.includes(obj.id))
      : searchResults;
    
    const csvContent = [
      ['Название', 'Тип', 'Регион', 'Город', 'Год', 'Площадь', 'Этажи', 'Цена за м²', 'Застройщик', 'Схожесть'],
      ...dataToExport.map(obj => [
        obj.name,
        obj.type,
        obj.region,
        obj.city,
        obj.year,
        obj.area,
        obj.floors,
        obj.price,
        obj.developer,
        obj.similarity + '%'
      ])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'analog_search_results.csv';
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
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">{obj.name}</h3>
              <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
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
              <div className="flex items-center space-x-2">
                <div className="flex items-center">
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <span className="text-sm font-medium text-gray-700 ml-1">{obj.rating}</span>
                </div>
                <div className="flex items-center">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span className="text-sm font-medium text-green-600 ml-1">{obj.similarity}% схожесть</span>
                </div>
              </div>
            </div>
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
            <p className="font-medium">{obj.floors}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Цена за м²:</span>
            <p className="font-medium">{obj.price.toLocaleString()} ₽</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Квартиры:</span>
            <p className="font-medium">{obj.apartments || '-'}</p>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="text-sm text-gray-500">
            Застройщик: <span className="font-medium text-gray-900">{obj.developer}</span>
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <Eye className="w-4 h-4" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <Share2 className="w-4 h-4" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderComparisonTable = () => {
    const objectsToCompare = searchResults.filter(obj => selectedObjects.includes(obj.id));
    
    if (objectsToCompare.length === 0) return null;

    return (
      <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Сравнение объектов</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-700">Характеристика</th>
                {objectsToCompare.map(obj => (
                  <th key={obj.id} className="text-left py-3 px-4 font-medium text-gray-700">
                    {obj.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-100">
                <td className="py-3 px-4 text-gray-600">Тип</td>
                {objectsToCompare.map(obj => (
                  <td key={obj.id} className="py-3 px-4">{obj.type}</td>
                ))}
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-3 px-4 text-gray-600">Год</td>
                {objectsToCompare.map(obj => (
                  <td key={obj.id} className="py-3 px-4">{obj.year}</td>
                ))}
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-3 px-4 text-gray-600">Площадь (м²)</td>
                {objectsToCompare.map(obj => (
                  <td key={obj.id} className="py-3 px-4">{obj.area.toLocaleString()}</td>
                ))}
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-3 px-4 text-gray-600">Этажи</td>
                {objectsToCompare.map(obj => (
                  <td key={obj.id} className="py-3 px-4">{obj.floors}</td>
                ))}
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-3 px-4 text-gray-600">Цена за м² (₽)</td>
                {objectsToCompare.map(obj => (
                  <td key={obj.id} className="py-3 px-4">{obj.price.toLocaleString()}</td>
                ))}
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-3 px-4 text-gray-600">Схожесть (%)</td>
                {objectsToCompare.map(obj => (
                  <td key={obj.id} className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      obj.similarity >= 90 ? 'bg-green-100 text-green-800' :
                      obj.similarity >= 80 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {obj.similarity}%
                    </span>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Поиск аналогов</h1>
        <p className="text-gray-600 mt-1">Найдите похожие объекты для сравнения и анализа</p>
      </div>

      {/* Поисковая строка */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Поиск по названию, описанию, застройщику..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isSearching || !searchQuery.trim()}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSearching ? 'Поиск...' : 'Найти'}
          </button>
        </div>
      </div>

      {/* Фильтры */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Фильтры</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={clearFilters}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Очистить
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center text-sm text-gray-500 hover:text-gray-700"
            >
              {showFilters ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              {showFilters ? 'Скрыть' : 'Показать'} фильтры
            </button>
          </div>
        </div>
        
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
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
              <label className="block text-sm font-medium text-gray-700 mb-2">Год от</label>
              <input
                type="number"
                value={filters.yearFrom}
                onChange={(e) => setFilters(prev => ({ ...prev, yearFrom: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="2020"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Год до</label>
              <input
                type="number"
                value={filters.yearTo}
                onChange={(e) => setFilters(prev => ({ ...prev, yearTo: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="2024"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Площадь от (м²)</label>
              <input
                type="number"
                value={filters.areaFrom}
                onChange={(e) => setFilters(prev => ({ ...prev, areaFrom: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="1000"
              />
            </div>
          </div>
        )}
      </div>

      {/* Результаты поиска */}
      {searchResults.length > 0 && (
        <div className="space-y-6">
          {/* Панель управления результатами */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Найдено объектов: {searchResults.length}
              </h2>
              {selectedObjects.length > 0 && (
                <span className="text-sm text-gray-500">
                  Выбрано: {selectedObjects.length}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="relevance">По релевантности</option>
                <option value="similarity">По схожести</option>
                <option value="year">По году</option>
                <option value="area">По площади</option>
                <option value="price">По цене</option>
              </select>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                  <Building2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                  <BarChart3 className="w-4 h-4" />
                </button>
              </div>
              
              <button
                onClick={handleExport}
                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Download className="w-4 h-4 mr-2" />
                Экспорт
              </button>
            </div>
          </div>

          {/* Список результатов */}
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 lg:grid-cols-2 gap-6' : 'space-y-4'}>
            {searchResults.map(renderObjectCard)}
          </div>

          {/* Сравнение объектов */}
          {selectedObjects.length > 1 && renderComparisonTable()}
        </div>
      )}

      {/* Пустое состояние */}
      {searchQuery && searchResults.length === 0 && !isSearching && (
        <div className="text-center py-12">
          <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Объекты не найдены</h3>
          <p className="text-gray-500">Попробуйте изменить параметры поиска или фильтры</p>
        </div>
      )}
    </div>
  );
};

export default AnalogObjectsSearchPage;
