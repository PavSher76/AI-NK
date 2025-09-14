import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  Settings, 
  Wind, 
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
  Fan,
  Droplets,
  Thermometer
} from 'lucide-react';

const VentilationCalculationsPage = ({ isAuthenticated, authToken }) => {
  const [calculations, setCalculations] = useState([]);
  const [calculationTypes, setCalculationTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedCalculation, setSelectedCalculation] = useState(null);
  const [showVentilationModal, setShowVentilationModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

  // Загрузка типов вентиляционных расчетов
  const fetchCalculationTypes = async () => {
    setLoadingTypes(true);
    try {
      const response = await fetch(`${API_BASE}/calculations/ventilation/types`, {
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
      console.log('🔍 [DEBUG] VentilationCalculationsPage.js: Not authenticated, skipping fetch');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] VentilationCalculationsPage.js: Fetching calculations');
      const response = await fetch(`${API_BASE}/calculations?type=ventilation`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('🔍 [DEBUG] VentilationCalculationsPage.js: Calculations loaded:', data);
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
          type: 'ventilation',
          category: 'air_exchange',
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
      setShowVentilationModal(false);
    } catch (error) {
      console.error('Error creating calculation:', error);
      setError('Ошибка создания расчета');
    }
  };

  // Выполнение расчета
  const executeCalculation = async (parameters) => {
    try {
      const response = await fetch(`${API_BASE}/calculations/ventilation/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          calculation_type: 'ventilation',
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
    setShowVentilationModal(true);
  };

  // Компонент модального окна создания расчета
  const VentilationCalculationModal = () => {
    const [formData, setFormData] = useState({
      name: '',
      description: '',
      room_volume: '',
      room_area: '',
      room_height: '',
      room_type: 'жилое',
      occupancy: '1',
      air_exchange_rate: '0.5',
      supply_air_temperature: '20',
      exhaust_air_temperature: '22',
      outdoor_temperature: '-25',
      co2_emission_per_person: '0.02',
      moisture_emission_per_person: '0.05',
      heat_emission_per_person: '120',
      heat_emission_from_equipment: '0',
      relative_humidity: '50',
      air_velocity: '0.2',
      ventilation_type: 'mechanical',
      heat_recovery_efficiency: '0',
      fan_efficiency: '0.7',
      smoke_ventilation_required: false,
      evacuation_route: false,
      noise_level_limit: '40',
      energy_efficiency_class: 'B'
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
          name: formData.name || 'Вентиляционный расчет',
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
      const { name, value, type, checked } = e.target;
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Wind className="w-6 h-6 mr-2 text-blue-600" />
              Вентиляционный расчет
            </h2>
            <button
              onClick={() => setShowVentilationModal(false)}
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Введите название расчета"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тип помещения
                  </label>
                  <select
                    name="room_type"
                    value={formData.room_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="жилое">Жилое</option>
                    <option value="общественное">Общественное</option>
                    <option value="производственное">Производственное</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Объем помещения (м³) *
                  </label>
                  <input
                    type="number"
                    name="room_volume"
                    value={formData.room_volume}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Площадь помещения (м²) *
                  </label>
                  <input
                    type="number"
                    name="room_area"
                    value={formData.room_area}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Высота помещения (м) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="room_height"
                    value={formData.room_height}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="2.5"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Количество людей
                  </label>
                  <input
                    type="number"
                    name="occupancy"
                    value={formData.occupancy}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="1"
                  />
                </div>
              </div>
            </div>

            {/* Параметры воздухообмена */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Fan className="w-5 h-5 mr-2" />
                Параметры воздухообмена
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Кратность воздухообмена (1/ч)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="air_exchange_rate"
                    value={formData.air_exchange_rate}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.5"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тип вентиляции
                  </label>
                  <select
                    name="ventilation_type"
                    value={formData.ventilation_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="natural">Естественная</option>
                    <option value="mechanical">Механическая</option>
                    <option value="mixed">Смешанная</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    КПД вентилятора (0-1)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    name="fan_efficiency"
                    value={formData.fan_efficiency}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.7"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    КПД рекуперации тепла (0-1)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    name="heat_recovery_efficiency"
                    value={formData.heat_recovery_efficiency}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Температурные параметры */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Thermometer className="w-5 h-5 mr-2" />
                Температурные параметры
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Температура приточного воздуха (°C)
                  </label>
                  <input
                    type="number"
                    name="supply_air_temperature"
                    value={formData.supply_air_temperature}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Температура вытяжного воздуха (°C)
                  </label>
                  <input
                    type="number"
                    name="exhaust_air_temperature"
                    value={formData.exhaust_air_temperature}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="22"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Температура наружного воздуха (°C)
                  </label>
                  <input
                    type="number"
                    name="outdoor_temperature"
                    value={formData.outdoor_temperature}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="50"
                  />
                </div>
              </div>
            </div>

            {/* Тепловыделения */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2" />
                Тепловыделения
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тепловыделения на человека (Вт)
                  </label>
                  <input
                    type="number"
                    name="heat_emission_per_person"
                    value={formData.heat_emission_per_person}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="120"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тепловыделения от оборудования (Вт)
                  </label>
                  <input
                    type="number"
                    name="heat_emission_from_equipment"
                    value={formData.heat_emission_from_equipment}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Выделение CO₂ на человека (м³/ч)
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    name="co2_emission_per_person"
                    value={formData.co2_emission_per_person}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.02"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Выделение влаги на человека (кг/ч)
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    name="moisture_emission_per_person"
                    value={formData.moisture_emission_per_person}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.05"
                  />
                </div>
              </div>
            </div>

            {/* Дополнительные параметры */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                Дополнительные параметры
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Скорость движения воздуха (м/с)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="air_velocity"
                    value={formData.air_velocity}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Предельный уровень шума (дБА)
                  </label>
                  <input
                    type="number"
                    name="noise_level_limit"
                    value={formData.noise_level_limit}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="40"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Класс энергоэффективности
                  </label>
                  <select
                    name="energy_efficiency_class"
                    value={formData.energy_efficiency_class}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                    <option value="E">E</option>
                  </select>
                </div>
              </div>
              
              <div className="mt-4 space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="smoke_ventilation_required"
                    checked={formData.smoke_ventilation_required}
                    onChange={handleInputChange}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Требуется противодымная вентиляция</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="evacuation_route"
                    checked={formData.evacuation_route}
                    onChange={handleInputChange}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Помещение является эвакуационным путем</span>
                </label>
              </div>
            </div>

            {/* Кнопки */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowVentilationModal(false)}
                className="px-4 py-2 text-gray-600 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={isExecuting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center"
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Wind className="w-8 h-8 mr-3 text-blue-600" />
            Вентиляция и кондиционирование
          </h1>
          <p className="text-gray-600 mt-1">
            Расчеты систем вентиляции согласно СП 60.13330.2016, СП 7.13130.2013, СП 54.13330.2016
          </p>
        </div>
        <button
          onClick={handleNewCalculation}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center"
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
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Все типы</option>
              <option value="air_exchange">Воздухообмен</option>
              <option value="smoke_ventilation">Противодымная вентиляция</option>
              <option value="residential_ventilation">Вентиляция жилых зданий</option>
              <option value="energy_efficiency">Энергоэффективность</option>
              <option value="acoustic_calculations">Акустические расчеты</option>
              <option value="heat_recovery">Рекуперация тепла</option>
              <option value="air_conditioning">Кондиционирование</option>
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredCalculations.length === 0 ? (
        <div className="text-center py-12">
          <Wind className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Нет расчетов</h3>
          <p className="text-gray-500 mb-4">Создайте первый вентиляционный расчет</p>
          <button
            onClick={handleNewCalculation}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Создать расчет
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCalculations.map((calculation) => (
            <div key={calculation.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="text-3xl">💨</div>
                <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                  {calculation.category}
                </span>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {calculation.name}
              </h3>
              
              <p className="text-gray-600 text-sm mb-4">
                {calculation.description || 'Вентиляционный расчет помещения'}
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
      {showVentilationModal && <VentilationCalculationModal />}

      {/* Модальное окно просмотра расчета */}
      {selectedCalculation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                <Wind className="w-6 h-6 mr-2 text-blue-600" />
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
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Воздухообмен</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Требуемый воздухообмен:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.required_air_exchange?.toFixed(2)} м³/ч
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Кратность воздухообмена:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.air_exchange_rate?.toFixed(2)} 1/ч
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Энергоэффективность</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Мощность вентилятора:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.fan_power?.toFixed(2)} Вт
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Класс энергоэффективности:</span>
                        <span className={`font-semibold px-2 py-1 rounded ${
                          selectedCalculation.results.energy_efficiency_class === 'A' ? 'bg-green-100 text-green-800' :
                          selectedCalculation.results.energy_efficiency_class === 'B' ? 'bg-blue-100 text-blue-800' :
                          selectedCalculation.results.energy_efficiency_class === 'C' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {selectedCalculation.results.energy_efficiency_class}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Акустические параметры */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Акустические параметры</h3>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Уровень шума:</span>
                    <span className="font-semibold">
                      {selectedCalculation.results.noise_level?.toFixed(1)} дБА
                    </span>
                  </div>
                </div>

                {/* Нормативные документы */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                    <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
                    Нормативные документы
                  </h3>
                  <ul className="space-y-1">
                    <li className="text-sm text-gray-700">• СП 60.13330.2016 - Отопление, вентиляция и кондиционирование воздуха</li>
                    <li className="text-sm text-gray-700">• СП 7.13130.2013 - Отопление, вентиляция и кондиционирование. Требования пожарной безопасности</li>
                    <li className="text-sm text-gray-700">• СП 54.13330.2016 - Здания жилые многоквартирные</li>
                  </ul>
                </div>
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

export default VentilationCalculationsPage;
