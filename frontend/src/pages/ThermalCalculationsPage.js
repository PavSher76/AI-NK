import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  Settings, 
  Thermometer, 
  Activity, 
  Shield, 
  Zap,
  Play, 
  Download, 
  Save,
  Trash2,
  Eye,
  Edit,
  Plus,
  Search,
  Filter,
  SortAsc,
  SortDesc,
  Calendar,
  User,
  Clock,
  CheckCircle,
  AlertCircle,
  Info,
  X,
  BookOpen,
  FileText,
  Target,
  TrendingUp,
  BarChart3,
  Layers,
  Building,
  Home,
  Sun,
  Wind
} from 'lucide-react';

const ThermalCalculationsPage = ({ isAuthenticated, authToken }) => {
  const [calculations, setCalculations] = useState([]);
  const [calculationTypes, setCalculationTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedCalculation, setSelectedCalculation] = useState(null);
  const [showThermalModal, setShowThermalModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

  // Загрузка типов теплотехнических расчетов
  const fetchCalculationTypes = async () => {
    setLoadingTypes(true);
    try {
      const response = await fetch(`${API_BASE}/calculations/thermal/types`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const types = await response.json();
      setCalculationTypes(types);
    } catch (error) {
      console.error('Error fetching calculation types:', error);
      setError('Ошибка загрузки типов расчетов');
    } finally {
      setLoadingTypes(false);
    }
  };

  // Загрузка расчетов
  const fetchCalculations = async () => {
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] ThermalCalculationsPage.js: Not authenticated, skipping fetch');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] ThermalCalculationsPage.js: Fetching calculations');
      const response = await fetch(`${API_BASE}/calculations?type=thermal`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('🔍 [DEBUG] ThermalCalculationsPage.js: Calculations loaded:', data);
      setCalculations(data);
    } catch (error) {
      console.error('Error fetching calculations:', error);
      setError('Ошибка загрузки расчетов');
    } finally {
      setLoading(false);
    }
  };

  // Создание нового расчета
  const createCalculation = async (calculationData) => {
    try {
      const response = await fetch(`${API_BASE}/calculations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: calculationData.name,
          type: 'thermal',
          category: 'heat_loss',
          parameters: calculationData.parameters,
          results: calculationData.results
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const newCalculation = await response.json();
      setCalculations(prev => [newCalculation, ...prev]);
      setSuccess('Расчет успешно создан');
      setShowThermalModal(false);
    } catch (error) {
      console.error('Error creating calculation:', error);
      setError('Ошибка создания расчета');
    }
  };

  // Выполнение расчета
  const executeCalculation = async (parameters) => {
    try {
      const response = await fetch(`${API_BASE}/calculations/thermal/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          calculation_type: 'thermal',
          parameters: parameters
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing calculation:', error);
      throw error;
    }
  };

  // Удаление расчета
  const deleteCalculation = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/calculations/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setCalculations(prev => prev.filter(calc => calc.id !== id));
      setSuccess('Расчет успешно удален');
    } catch (error) {
      console.error('Error deleting calculation:', error);
      setError('Ошибка удаления расчета');
    }
  };

  // Загрузка данных при монтировании
  useEffect(() => {
    fetchCalculationTypes();
    fetchCalculations();
  }, [isAuthenticated, authToken]);

  // Фильтрация и сортировка
  const filteredCalculations = calculations
    .filter(calc => {
      const matchesSearch = calc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           calc.description?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = filterType === 'all' || calc.category === filterType;
      return matchesSearch && matchesType;
    })
    .sort((a, b) => {
      let aValue, bValue;
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'date':
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
        default:
          aValue = a[sortBy];
          bValue = b[sortBy];
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const handleSortChange = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const handleNewCalculation = () => {
    setShowThermalModal(true);
  };

  // Компонент модального окна создания расчета
  const ThermalCalculationModal = () => {
    const [formData, setFormData] = useState({
      name: '',
      description: '',
      building_type: 'жилое',
      building_area: '',
      building_volume: '',
      number_of_floors: '',
      wall_thickness: '',
      wall_material: '',
      thermal_conductivity: '',
      wall_area: '',
      floor_area: '',
      ceiling_area: '',
      window_area: '0',
      indoor_temperature: '20',
      outdoor_temperature: '-25',
      relative_humidity: '55',
      wind_speed: '5.0',
      air_exchange_rate: '0.5',
      heat_emission_people: '0',
      heat_emission_equipment: '0',
      heat_emission_lighting: '0',
      normative_heat_transfer_resistance: '3.2'
    });

    const [isExecuting, setIsExecuting] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      setIsExecuting(true);

      try {
        // Выполнение расчета
        const results = await executeCalculation(formData);
        
        // Создание расчета
        await createCalculation({
          name: formData.name || 'Теплотехнический расчет',
          parameters: formData,
          results: results
        });
      } catch (error) {
        setError('Ошибка выполнения расчета: ' + error.message);
      } finally {
        setIsExecuting(false);
      }
    };

    const handleInputChange = (e) => {
      const { name, value } = e.target;
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Thermometer className="w-6 h-6 mr-2 text-orange-600" />
              Теплотехнический расчет
            </h2>
            <button
              onClick={() => setShowThermalModal(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Основная информация */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Building className="w-5 h-5 mr-2" />
                Основная информация
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Название расчета
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="Введите название расчета"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тип здания
                  </label>
                  <select
                    name="building_type"
                    value={formData.building_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="жилое">Жилое</option>
                    <option value="общественное">Общественное</option>
                    <option value="производственное">Производственное</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Площадь здания (м²) *
                  </label>
                  <input
                    type="number"
                    name="building_area"
                    value={formData.building_area}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Объем здания (м³) *
                  </label>
                  <input
                    type="number"
                    name="building_volume"
                    value={formData.building_volume}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="300"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Количество этажей *
                  </label>
                  <input
                    type="number"
                    name="number_of_floors"
                    value={formData.number_of_floors}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="1"
                  />
                </div>
              </div>
            </div>

            {/* Параметры ограждающих конструкций */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Layers className="w-5 h-5 mr-2" />
                Ограждающие конструкции
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Толщина стены (м) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    name="wall_thickness"
                    value={formData.wall_thickness}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="0.5"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Материал стены *
                  </label>
                  <input
                    type="text"
                    name="wall_material"
                    value={formData.wall_material}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="кирпич"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Теплопроводность (Вт/(м·К)) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    name="thermal_conductivity"
                    value={formData.thermal_conductivity}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="0.7"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Площадь стен (м²) *
                  </label>
                  <input
                    type="number"
                    name="wall_area"
                    value={formData.wall_area}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Площадь пола (м²) *
                  </label>
                  <input
                    type="number"
                    name="floor_area"
                    value={formData.floor_area}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Площадь потолка (м²) *
                  </label>
                  <input
                    type="number"
                    name="ceiling_area"
                    value={formData.ceiling_area}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Площадь окон (м²)
                  </label>
                  <input
                    type="number"
                    name="window_area"
                    value={formData.window_area}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Климатические параметры */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Sun className="w-5 h-5 mr-2" />
                Климатические параметры
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Внутренняя температура (°C)
                  </label>
                  <input
                    type="number"
                    name="indoor_temperature"
                    value={formData.indoor_temperature}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Наружная температура (°C)
                  </label>
                  <input
                    type="number"
                    name="outdoor_temperature"
                    value={formData.outdoor_temperature}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="-25"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Относительная влажность (%)
                  </label>
                  <input
                    type="number"
                    name="relative_humidity"
                    value={formData.relative_humidity}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="55"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Скорость ветра (м/с)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="wind_speed"
                    value={formData.wind_speed}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="5.0"
                  />
                </div>
              </div>
            </div>

            {/* Кнопки */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowThermalModal(false)}
                className="px-4 py-2 text-gray-600 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={isExecuting}
                className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors disabled:opacity-50 flex items-center"
              >
                {isExecuting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Выполняется...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Выполнить расчет
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  if (loadingTypes) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Thermometer className="w-8 h-8 mr-3 text-orange-600" />
            Теплотехнические расчеты
          </h1>
          <p className="text-gray-600 mt-1">
            Расчеты теплопередачи, теплоизоляции и энергоэффективности согласно СП 50.13330.2012
          </p>
        </div>
        <button
          onClick={handleNewCalculation}
          className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Новый расчет
        </button>
      </div>

      {/* Уведомления */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
          <span className="text-red-700">{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-400 hover:text-red-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4 flex items-center">
          <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
          <span className="text-green-700">{success}</span>
          <button
            onClick={() => setSuccess(null)}
            className="ml-auto text-green-400 hover:text-green-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Фильтры и поиск */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Поиск расчетов..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="all">Все типы</option>
              <option value="heat_loss">Теплопотери</option>
              <option value="thermal_insulation">Теплоизоляция</option>
              <option value="condensation">Конденсация</option>
            </select>
            <button
              onClick={() => handleSortChange('date')}
              className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center"
            >
              {sortBy === 'date' && sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Список расчетов */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
        </div>
      ) : filteredCalculations.length === 0 ? (
        <div className="text-center py-12">
          <Thermometer className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Нет расчетов</h3>
          <p className="text-gray-500 mb-4">Создайте первый теплотехнический расчет</p>
          <button
            onClick={handleNewCalculation}
            className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
          >
            Создать расчет
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCalculations.map((calculation) => (
            <div key={calculation.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="text-3xl">🌡️</div>
                <span className="text-xs px-2 py-1 bg-orange-100 text-orange-800 rounded-full">
                  {calculation.category}
                </span>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {calculation.name}
              </h3>
              
              <p className="text-gray-600 text-sm mb-4">
                {calculation.description || 'Теплотехнический расчет здания'}
              </p>
              
              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-gray-500">
                  <Calendar className="w-4 h-4 mr-2" />
                  {new Date(calculation.created_at).toLocaleDateString()}
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <User className="w-4 h-4 mr-2" />
                  {calculation.created_by || 'Система'}
                </div>
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={() => setSelectedCalculation(calculation)}
                  className="flex-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors flex items-center justify-center"
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Просмотр
                </button>
                <button
                  onClick={() => deleteCalculation(calculation.id)}
                  className="px-3 py-2 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Модальное окно создания расчета */}
      {showThermalModal && <ThermalCalculationModal />}

      {/* Модальное окно просмотра расчета */}
      {selectedCalculation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                <Thermometer className="w-6 h-6 mr-2 text-orange-600" />
                {selectedCalculation.name}
              </h2>
              <button
                onClick={() => setSelectedCalculation(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {selectedCalculation.results && (
              <div className="space-y-6">
                {/* Результаты расчетов */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Теплопотери</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Общие теплопотери:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.heat_losses?.total_heat_loss?.toFixed(2)} Вт
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Удельные теплопотери:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.heat_losses?.specific_heat_loss?.toFixed(2)} Вт/м²
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Энергоэффективность</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Класс энергоэффективности:</span>
                        <span className={`font-semibold px-2 py-1 rounded ${
                          selectedCalculation.results.energy_efficiency?.efficiency_class === 'A+' ? 'bg-green-100 text-green-800' :
                          selectedCalculation.results.energy_efficiency?.efficiency_class === 'A' ? 'bg-green-100 text-green-800' :
                          selectedCalculation.results.energy_efficiency?.efficiency_class === 'B' ? 'bg-blue-100 text-blue-800' :
                          selectedCalculation.results.energy_efficiency?.efficiency_class === 'C' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {selectedCalculation.results.energy_efficiency?.efficiency_class}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Удельное потребление:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.energy_efficiency?.specific_consumption?.toFixed(2)} Вт/м²
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Нормативное соответствие */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Нормативное соответствие</h3>
                  <div className="flex items-center">
                    {selectedCalculation.results.normative_compliance?.meets_requirements ? (
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                    )}
                    <span className={selectedCalculation.results.normative_compliance?.meets_requirements ? 'text-green-700' : 'text-red-700'}>
                      {selectedCalculation.results.normative_compliance?.meets_requirements ? 
                        'Соответствует нормативным требованиям' : 
                        'Не соответствует нормативным требованиям'
                      }
                    </span>
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    Соответствие: {selectedCalculation.results.normative_compliance?.compliance_percentage?.toFixed(1)}%
                  </div>
                </div>

                {/* Рекомендации по безопасности */}
                {selectedCalculation.results.safety_recommendations && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                      <Shield className="w-5 h-5 mr-2 text-yellow-600" />
                      Рекомендации по безопасности
                    </h3>
                    <ul className="space-y-1">
                      {selectedCalculation.results.safety_recommendations.map((rec, index) => (
                        <li key={index} className="text-sm text-gray-700 flex items-start">
                          <span className="text-yellow-600 mr-2">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedCalculation(null)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThermalCalculationsPage;