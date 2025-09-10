import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  FileText, 
  BookOpen, 
  Settings, 
  Play, 
  Download, 
  Upload,
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
  Shield,
  Zap,
  Target
} from 'lucide-react';

const UAVProtectionCalculationsPage = ({ isAuthenticated, authToken }) => {
  const [calculations, setCalculations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedCalculation, setSelectedCalculation] = useState(null);
  const [showNewCalculationModal, setShowNewCalculationModal] = useState(false);
  const [showViewCalculationModal, setShowViewCalculationModal] = useState(false);
  const [viewingCalculation, setViewingCalculation] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api';

  // Типы расчетов защиты от БПЛА
  const calculationTypes = [
    {
      id: 'shock_wave',
      name: 'Расчёт воздействия ударной волны',
      description: 'Расчет воздействия ударной волны от взрыва БПЛА на конструкции',
      norms: ['СП 542.1325800.2024', 'СП 1.13130.2020', 'СП 20.13330.2016'],
      icon: '💥',
      parameters: [
        { name: 'uav_mass', label: 'Масса БПЛА', unit: 'кг', type: 'number', required: true },
        { name: 'distance', label: 'Расстояние до объекта', unit: 'м', type: 'number', required: true },
        { name: 'explosive_type', label: 'Тип взрывчатого вещества', unit: '', type: 'select', required: true, options: [
          { value: 'TNT', label: 'ТНТ' },
          { value: 'RDX', label: 'РДХ' },
          { value: 'PETN', label: 'ПЭТН' },
          { value: 'HMX', label: 'ГМХ' }
        ]},
        { name: 'explosion_height', label: 'Высота взрыва', unit: 'м', type: 'number', required: true },
        { name: 'structure_material', label: 'Материал конструкции', unit: '', type: 'select', required: true, options: [
          { value: 'concrete', label: 'Бетон' },
          { value: 'steel', label: 'Сталь' },
          { value: 'brick', label: 'Кирпич' },
          { value: 'wood', label: 'Дерево' }
        ]},
        { name: 'structure_thickness', label: 'Толщина конструкции', unit: 'мм', type: 'number', required: true }
      ]
    },
    {
      id: 'impact_penetration',
      name: 'Расчёт попадания БПЛА в конструкцию',
      description: 'Расчет проникающей способности БПЛА и повреждений конструкций',
      norms: ['СП 542.1325800.2024', 'СП 20.13330.2016', 'СП 16.13330.2017'],
      icon: '🎯',
      parameters: [
        { name: 'uav_velocity', label: 'Скорость БПЛА', unit: 'м/с', type: 'number', required: true },
        { name: 'uav_mass', label: 'Масса БПЛА', unit: 'кг', type: 'number', required: true },
        { name: 'uav_material', label: 'Материал БПЛА', unit: '', type: 'select', required: true, options: [
          { value: 'aluminum', label: 'Алюминий' },
          { value: 'carbon_fiber', label: 'Углеродное волокно' },
          { value: 'steel', label: 'Сталь' },
          { value: 'plastic', label: 'Пластик' }
        ]},
        { name: 'structure_thickness', label: 'Толщина конструкции', unit: 'мм', type: 'number', required: true },
        { name: 'structure_strength', label: 'Прочность материала', unit: 'МПа', type: 'number', required: true },
        { name: 'impact_angle', label: 'Угол удара', unit: 'град', type: 'number', required: true, min: 0, max: 90 }
      ]
    }
  ];

  // Загрузка расчетов
  const fetchCalculations = async () => {
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] UAVProtectionCalculationsPage.js: Not authenticated, skipping fetch');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/calculations?type=uav_protection`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('🔍 [DEBUG] UAVProtectionCalculationsPage.js: Fetched calculations:', data);
      setCalculations(data);
    } catch (error) {
      console.error('Error fetching calculations:', error);
      setError('Ошибка загрузки расчетов: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Создание нового расчета
  const handleNewCalculation = async (calculationType) => {
    if (!isAuthenticated || !authToken) {
      setError('Необходима авторизация для создания расчетов');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/calculations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: calculationType,
          name: `Расчет защиты от БПЛА - ${new Date().toLocaleString()}`,
          description: `Новый расчет ${calculationType}`,
          parameters: {}
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const newCalculation = await response.json();
      console.log('🔍 [DEBUG] UAVProtectionCalculationsPage.js: Created calculation:', newCalculation);
      
      setSuccess('Расчет успешно создан');
      setShowNewCalculationModal(false);
      fetchCalculations();
    } catch (error) {
      console.error('Error creating calculation:', error);
      setError('Ошибка создания расчета: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Выполнение расчета
  const executeCalculation = async (calculationId, parameters) => {
    if (!isAuthenticated || !authToken) {
      setError('Необходима авторизация для выполнения расчетов');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/calculations/${calculationId}/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ parameters })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('🔍 [DEBUG] UAVProtectionCalculationsPage.js: Calculation result:', result);
      
      setSuccess('Расчет успешно выполнен');
      fetchCalculations();
    } catch (error) {
      console.error('Error executing calculation:', error);
      setError('Ошибка выполнения расчета: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Просмотр расчета
  const handleViewCalculation = async (calculation) => {
    try {
      let calculationToView = { ...calculation };
      if (!calculation.result) {
        console.log('🔍 [DEBUG] UAVProtectionCalculationsPage.js: No result found for viewing, executing calculation...');
        const response = await fetch(`${API_BASE}/calculations/${calculation.type}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({ calculation_type: calculation.type, parameters: calculation.parameters })
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        calculationToView.result = result;
      }
      setViewingCalculation(calculationToView);
      setShowViewCalculationModal(true);
    } catch (error) {
      console.error('Error viewing calculation:', error);
      setError('Ошибка просмотра расчета: ' + error.message);
    }
  };

  // Скачивание расчета
  const handleDownloadCalculation = async (calculation) => {
    try {
      let calculationData = { ...calculation };
      if (!calculation.result) {
        console.log('🔍 [DEBUG] UAVProtectionCalculationsPage.js: No result found, executing calculation...');
        const response = await fetch(`${API_BASE}/calculations/${calculation.type}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({ calculation_type: calculation.type, parameters: calculation.parameters })
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        calculationData.result = result;
      }

      const dataStr = JSON.stringify(calculationData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `uav_protection_calculation_${calculation.id}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading calculation:', error);
      setError('Ошибка скачивания расчета: ' + error.message);
    }
  };

  // Удаление расчета
  const deleteCalculation = async (calculationId) => {
    if (!isAuthenticated || !authToken) {
      setError('Необходима авторизация для удаления расчетов');
      return;
    }

    if (!window.confirm('Вы уверены, что хотите удалить этот расчет?')) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/calculations/${calculationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setSuccess('Расчет успешно удален');
      fetchCalculations();
    } catch (error) {
      console.error('Error deleting calculation:', error);
      setError('Ошибка удаления расчета: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Фильтрация и сортировка
  const filteredCalculations = calculations
    .filter(calc => {
      const matchesSearch = calc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           calc.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filterType === 'all' || calc.type === filterType;
      return matchesSearch && matchesFilter;
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
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  // Загрузка при монтировании
  useEffect(() => {
    fetchCalculations();
  }, [isAuthenticated, authToken]);

  // Очистка сообщений
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Заголовок */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <Shield className="w-8 h-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Защита от БПЛА</h1>
          </div>
          <p className="text-gray-600 text-lg">
            Расчеты защиты от воздействия беспилотных летательных аппаратов
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              СП 542.1325800.2024
            </span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              СП 1.13130.2020
            </span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              СП 2.13130.2020
            </span>
          </div>
        </div>

        {/* Сообщения об ошибках и успехе */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-red-400 mr-3" />
              <div className="text-red-800">{error}</div>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <CheckCircle className="w-5 h-5 text-green-400 mr-3" />
              <div className="text-green-800">{success}</div>
            </div>
          </div>
        )}

        {/* Типы расчетов */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {calculationTypes.map((type) => (
            <div key={type.id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <div className="flex items-center mb-4">
                <span className="text-3xl mr-3">{type.icon}</span>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{type.name}</h3>
                  <p className="text-gray-600">{type.description}</p>
                </div>
              </div>
              
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Применяемые нормы:</h4>
                <div className="flex flex-wrap gap-1">
                  {type.norms.map((norm, index) => (
                    <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                      {norm}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Параметры расчета:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {type.parameters.slice(0, 3).map((param, index) => (
                    <li key={index} className="flex items-center">
                      <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                      {param.label} ({param.unit})
                    </li>
                  ))}
                  {type.parameters.length > 3 && (
                    <li className="text-gray-500">и еще {type.parameters.length - 3} параметров...</li>
                  )}
                </ul>
              </div>
              
              <button 
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center"
                onClick={() => handleNewCalculation(type.id)}
                disabled={loading}
              >
                <Plus className="w-4 h-4 mr-2" />
                Создать расчет
              </button>
            </div>
          ))}
        </div>

        {/* Список расчетов */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 sm:mb-0">
                Выполненные расчеты
              </h2>
              
              <div className="flex flex-col sm:flex-row gap-4">
                {/* Поиск */}
                <div className="relative">
                  <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Поиск расчетов..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Фильтр */}
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">Все типы</option>
                  <option value="shock_wave">Ударная волна</option>
                  <option value="impact_penetration">Попадание в конструкцию</option>
                </select>

                {/* Сортировка */}
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center"
                >
                  {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {loading ? (
              <div className="p-6 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Загрузка расчетов...</p>
              </div>
            ) : filteredCalculations.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <Calculator className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Расчеты не найдены</p>
              </div>
            ) : (
              filteredCalculations.map((calculation) => (
                <div key={calculation.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <h3 className="text-lg font-medium text-gray-900">{calculation.name}</h3>
                        <span className={`ml-3 px-2 py-1 rounded-full text-xs font-medium ${
                          calculation.status === 'completed' 
                            ? 'bg-green-100 text-green-800' 
                            : calculation.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {calculation.status === 'completed' ? 'Завершен' : 
                           calculation.status === 'pending' ? 'В ожидании' : 'Ошибка'}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-2">{calculation.description}</p>
                      <div className="flex items-center text-sm text-gray-500">
                        <Calendar className="w-4 h-4 mr-1" />
                        <span className="mr-4">
                          {new Date(calculation.created_at).toLocaleDateString('ru-RU')}
                        </span>
                        <Clock className="w-4 h-4 mr-1" />
                        <span>
                          {new Date(calculation.created_at).toLocaleTimeString('ru-RU')}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleViewCalculation(calculation)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Просмотреть расчет"
                      >
                        <Eye className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDownloadCalculation(calculation)}
                        className="text-green-600 hover:text-green-900"
                        title="Скачать результат"
                      >
                        <Download className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => deleteCalculation(calculation.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Удалить расчет"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Модальное окно просмотра расчета */}
        {showViewCalculationModal && viewingCalculation && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Просмотр расчета: {viewingCalculation.name}
                </h3>
                <button
                  onClick={() => setShowViewCalculationModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-3">Параметры расчета</h4>
                    <div className="space-y-2">
                      {Object.entries(viewingCalculation.parameters || {}).map(([key, value]) => (
                        <div key={key} className="flex justify-between py-1 border-b border-gray-100">
                          <span className="text-sm text-gray-600">{key}:</span>
                          <span className="text-sm font-medium text-gray-900">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-3">Результаты расчета</h4>
                    {viewingCalculation.result ? (
                      <div className="space-y-2">
                        {Object.entries(viewingCalculation.result).map(([key, value]) => (
                          <div key={key} className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-sm text-gray-600">{key}:</span>
                            <span className="text-sm font-medium text-gray-900">{value}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">Результаты расчета недоступны</p>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => handleDownloadCalculation(viewingCalculation)}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Скачать результат
                </button>
                <button
                  onClick={() => setShowViewCalculationModal(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UAVProtectionCalculationsPage;
