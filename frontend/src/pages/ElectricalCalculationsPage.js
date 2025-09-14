import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  Settings, 
  Zap, 
  Activity, 
  Shield, 
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
  Wind,
  Battery,
  Cpu,
  Wifi
} from 'lucide-react';

const ElectricalCalculationsPage = ({ isAuthenticated, authToken }) => {
  const [calculations, setCalculations] = useState([]);
  const [calculationTypes, setCalculationTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedCalculation, setSelectedCalculation] = useState(null);
  const [showElectricalModal, setShowElectricalModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

  // Загрузка типов электротехнических расчетов
  const fetchCalculationTypes = async () => {
    setLoadingTypes(true);
    try {
      const response = await fetch(`${API_BASE}/calculations/electrical/types`, {
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
      console.log('🔍 [DEBUG] ElectricalCalculationsPage.js: Not authenticated, skipping fetch');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] ElectricalCalculationsPage.js: Fetching calculations');
      const response = await fetch(`${API_BASE}/calculations?type=electrical`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('🔍 [DEBUG] ElectricalCalculationsPage.js: Calculations loaded:', data);
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
          type: 'electrical',
          category: 'electrical_loads',
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
      setShowElectricalModal(false);
    } catch (error) {
      console.error('Error creating calculation:', error);
      setError('Ошибка создания расчета');
    }
  };

  // Выполнение расчета
  const executeCalculation = async (parameters) => {
    try {
      const response = await fetch(`${API_BASE}/calculations/electrical/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          calculation_type: 'electrical',
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
    setShowElectricalModal(true);
  };

  // Компонент модального окна создания расчета
  const ElectricalCalculationModal = () => {
    const [formData, setFormData] = useState({
      name: '',
      description: '',
      building_type: 'жилое',
      total_area: '',
      number_of_floors: '',
      number_of_apartments: '0',
      lighting_load: '',
      power_load: '',
      heating_load: '0',
      ventilation_load: '0',
      demand_factor: '0.7',
      diversity_factor: '0.8',
      power_factor: '0.9',
      voltage: '380',
      load_current: '0',
      power: '0',
      cable_length: '0',
      soil_resistivity: '100',
      building_height: '0',
      building_length: '0',
      building_width: '0',
      annual_electricity_consumption: '0'
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
          name: formData.name || 'Электротехнический расчет',
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
              <Zap className="w-6 h-6 mr-2 text-yellow-600" />
              Электротехнический расчет
            </h2>
            <button
              onClick={() => setShowElectricalModal(false)}
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  >
                    <option value="жилое">Жилое</option>
                    <option value="общественное">Общественное</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Общая площадь здания (м²) *
                  </label>
                  <input
                    type="number"
                    name="total_area"
                    value={formData.total_area}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="1000"
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="5"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Количество квартир
                  </label>
                  <input
                    type="number"
                    name="number_of_apartments"
                    value={formData.number_of_apartments}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Электрические нагрузки */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Battery className="w-5 h-5 mr-2" />
                Электрические нагрузки
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Нагрузка освещения (Вт/м²) *
                  </label>
                  <input
                    type="number"
                    name="lighting_load"
                    value={formData.lighting_load}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="10"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Силовая нагрузка (Вт/м²) *
                  </label>
                  <input
                    type="number"
                    name="power_load"
                    value={formData.power_load}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="15"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Нагрузка отопления (Вт/м²)
                  </label>
                  <input
                    type="number"
                    name="heating_load"
                    value={formData.heating_load}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Нагрузка вентиляции (Вт/м²)
                  </label>
                  <input
                    type="number"
                    name="ventilation_load"
                    value={formData.ventilation_load}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Коэффициенты */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                Коэффициенты
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Коэффициент спроса
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    name="demand_factor"
                    value={formData.demand_factor}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0.7"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Коэффициент разновременности
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    name="diversity_factor"
                    value={formData.diversity_factor}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0.8"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Коэффициент мощности
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    name="power_factor"
                    value={formData.power_factor}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0.9"
                  />
                </div>
              </div>
            </div>

            {/* Параметры кабелей */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Cpu className="w-5 h-5 mr-2" />
                Параметры кабелей
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Номинальное напряжение (В)
                  </label>
                  <input
                    type="number"
                    name="voltage"
                    value={formData.voltage}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="380"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Расчетный ток нагрузки (А)
                  </label>
                  <input
                    type="number"
                    name="load_current"
                    value={formData.load_current}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Мощность нагрузки (кВт)
                  </label>
                  <input
                    type="number"
                    name="power"
                    value={formData.power}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Длина кабеля (м)
                  </label>
                  <input
                    type="number"
                    name="cable_length"
                    value={formData.cable_length}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Параметры заземления */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Параметры заземления
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Удельное сопротивление грунта (Ом·м)
                  </label>
                  <input
                    type="number"
                    name="soil_resistivity"
                    value={formData.soil_resistivity}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Высота здания (м)
                  </label>
                  <input
                    type="number"
                    name="building_height"
                    value={formData.building_height}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Длина здания (м)
                  </label>
                  <input
                    type="number"
                    name="building_length"
                    value={formData.building_length}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ширина здания (м)
                  </label>
                  <input
                    type="number"
                    name="building_width"
                    value={formData.building_width}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Кнопки */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowElectricalModal(false)}
                className="px-4 py-2 text-gray-600 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={isExecuting}
                className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors disabled:opacity-50 flex items-center"
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Zap className="w-8 h-8 mr-3 text-yellow-600" />
            Электротехнические расчеты
          </h1>
          <p className="text-gray-600 mt-1">
            Расчеты электрических нагрузок, заземления и молниезащиты согласно СП 31.110-2003, СП 437.1325800.2018, СП 256.1325800.2016
          </p>
        </div>
        <button
          onClick={handleNewCalculation}
          className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors flex items-center"
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
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
            >
              <option value="all">Все типы</option>
              <option value="electrical_loads">Электрические нагрузки</option>
              <option value="cable_calculation">Расчет кабелей</option>
              <option value="grounding">Заземление</option>
              <option value="lightning_protection">Молниезащита</option>
              <option value="energy_efficiency">Энергоэффективность</option>
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-600"></div>
        </div>
      ) : filteredCalculations.length === 0 ? (
        <div className="text-center py-12">
          <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Нет расчетов</h3>
          <p className="text-gray-500 mb-4">Создайте первый электротехнический расчет</p>
          <button
            onClick={handleNewCalculation}
            className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
          >
            Создать расчет
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCalculations.map((calculation) => (
            <div key={calculation.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="text-3xl">⚡</div>
                <span className="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full">
                  {calculation.category}
                </span>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {calculation.name}
              </h3>
              
              <p className="text-gray-600 text-sm mb-4">
                {calculation.description || 'Электротехнический расчет здания'}
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
      {showElectricalModal && <ElectricalCalculationModal />}

      {/* Модальное окно просмотра расчета */}
      {selectedCalculation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                <Zap className="w-6 h-6 mr-2 text-yellow-600" />
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
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Электрические нагрузки</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Общая установленная мощность:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.electrical_loads?.total_installed_power?.toFixed(0)} Вт
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Расчетная мощность:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.electrical_loads?.calculated_power?.toFixed(0)} Вт
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Расчетный ток:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.electrical_loads?.calculated_current?.toFixed(1)} А
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Кабели</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Рекомендуемое сечение:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.cable_calculation?.selected_section?.toFixed(1)} мм²
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Максимальный ток:</span>
                        <span className="font-semibold">
                          {selectedCalculation.results.cable_calculation?.max_current?.toFixed(1)} А
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Заземление */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Заземление</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Сопротивление заземления:</span>
                      <span className="font-semibold">
                        {selectedCalculation.results.grounding_calculation?.total_resistance?.toFixed(2)} Ом
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Количество электродов:</span>
                      <span className="font-semibold">
                        {selectedCalculation.results.grounding_calculation?.number_of_electrodes}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Соответствие требованиям:</span>
                      <span className={`font-semibold ${selectedCalculation.results.grounding_calculation?.meets_requirements ? 'text-green-600' : 'text-red-600'}`}>
                        {selectedCalculation.results.grounding_calculation?.meets_requirements ? 'Да' : 'Нет'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Молниезащита */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Молниезащита</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Уровень защиты:</span>
                      <span className="font-semibold">
                        {selectedCalculation.results.lightning_protection?.protection_level}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Количество молниеотводов:</span>
                      <span className="font-semibold">
                        {selectedCalculation.results.lightning_protection?.number_of_rods}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Высота молниеотвода:</span>
                      <span className="font-semibold">
                        {selectedCalculation.results.lightning_protection?.lightning_rod_height?.toFixed(1)} м
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Соответствие требованиям:</span>
                      <span className={`font-semibold ${selectedCalculation.results.lightning_protection?.meets_requirements ? 'text-green-600' : 'text-red-600'}`}>
                        {selectedCalculation.results.lightning_protection?.meets_requirements ? 'Да' : 'Нет'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Энергоэффективность */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Энергоэффективность</h3>
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
                </div>

                {/* Нормативные документы */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                    <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
                    Нормативные документы
                  </h3>
                  <ul className="space-y-1">
                    <li className="text-sm text-gray-700">• СП 31.110-2003 - Электроустановки жилых и общественных зданий</li>
                    <li className="text-sm text-gray-700">• СП 437.1325800.2018 - Инженерные системы зданий и сооружений</li>
                    <li className="text-sm text-gray-700">• СП 256.1325800.2016 - Энергоэффективность зданий</li>
                  </ul>
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

export default ElectricalCalculationsPage;
