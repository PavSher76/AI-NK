import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  Settings, 
  Ruler, 
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
  Layers
} from 'lucide-react';
import StructuralCalculationModal from '../components/StructuralCalculationModal';

const StructuralCalculationsPage = ({ isAuthenticated, authToken }) => {
  const [calculations, setCalculations] = useState([]);
  const [calculationTypes, setCalculationTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedCalculation, setSelectedCalculation] = useState(null);
  const [showStructuralModal, setShowStructuralModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api';

  // Загрузка типов расчетов строительных конструкций
  const fetchCalculationTypes = async () => {
    if (!isAuthenticated || !authToken) {
      setError('Ошибка авторизации');
      return;
    }

    setLoadingTypes(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] StructuralCalculationsPage.js: Fetching calculation types');
      const response = await fetch(`${API_BASE}/calculations/structural/types`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        const types = await response.json();
        setCalculationTypes(types);
        console.log('🔍 [DEBUG] StructuralCalculationsPage.js: Calculation types loaded:', types);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Ошибка загрузки типов расчетов');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] StructuralCalculationsPage.js: Fetch types error:', error);
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        setError('Ошибка сети. Проверьте подключение к интернету.');
      } else {
        setError('Ошибка загрузки типов расчетов');
      }
    } finally {
      setLoadingTypes(false);
    }
  };

  // Загрузка существующих расчетов
  const fetchCalculations = async () => {
    if (!isAuthenticated || !authToken) {
      setError('Ошибка авторизации');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] StructuralCalculationsPage.js: Fetching calculations');
      const response = await fetch(`${API_BASE}/calculations?type=structural`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCalculations(data);
        console.log('🔍 [DEBUG] StructuralCalculationsPage.js: Calculations loaded:', data);
      } else if (response.status === 404) {
        setCalculations([]);
        console.log('🔍 [DEBUG] StructuralCalculationsPage.js: No calculations found');
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Ошибка загрузки расчетов');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] StructuralCalculationsPage.js: Fetch error:', error);
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        setError('Ошибка сети. Проверьте подключение к интернету.');
      } else {
        setError('Ошибка загрузки расчетов');
      }
    } finally {
      setLoading(false);
    }
  };

  // Удаление расчета
  const deleteCalculation = async (calculationId) => {
    if (!isAuthenticated || !authToken) {
      setError('Ошибка авторизации');
      return;
    }

    if (!window.confirm('Вы уверены, что хотите удалить этот расчет?')) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] StructuralCalculationsPage.js: Deleting calculation:', calculationId);
      const response = await fetch(`${API_BASE}/calculations/${calculationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        setCalculations(prev => prev.filter(calc => calc.id !== calculationId));
        setSuccess('Расчет успешно удален');
        console.log('🔍 [DEBUG] StructuralCalculationsPage.js: Calculation deleted successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Ошибка удаления расчета');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] StructuralCalculationsPage.js: Delete error:', error);
      setError('Ошибка удаления расчета');
    } finally {
      setLoading(false);
    }
  };

  // Создание структурного расчета
  const createStructuralCalculation = async (calculationData) => {
    if (!isAuthenticated || !authToken) {
      setError('Ошибка авторизации');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] StructuralCalculationsPage.js: Creating structural calculation:', calculationData);
      
      // Сначала выполняем расчет
      const executeResponse = await fetch(`${API_BASE}/calculations/structural/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          calculation_type: calculationData.subcategory,
          parameters: calculationData.parameters
        })
      });

      if (!executeResponse.ok) {
        const errorData = await executeResponse.json();
        throw new Error(errorData.detail || 'Ошибка выполнения расчета');
      }

      const calculationResult = await executeResponse.json();
      
      // Создаем запись в базе данных
      const createResponse = await fetch(`${API_BASE}/calculations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          ...calculationData,
          type: 'structural',
          result: calculationResult
        })
      });

      if (createResponse.ok) {
        const newCalculation = await createResponse.json();
        setCalculations(prev => [newCalculation, ...prev]);
        setSuccess('Расчет успешно создан и выполнен');
        setShowStructuralModal(false);
        console.log('🔍 [DEBUG] StructuralCalculationsPage.js: Structural calculation created successfully');
      } else {
        const errorData = await createResponse.json();
        setError(errorData.message || 'Ошибка создания расчета');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] StructuralCalculationsPage.js: Create error:', error);
      setError(error.message || 'Ошибка создания расчета');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка данных при монтировании
  useEffect(() => {
    if (isAuthenticated && authToken) {
      fetchCalculationTypes();
      fetchCalculations();
    }
  }, [isAuthenticated, authToken]);

  // Фильтрация и сортировка расчетов
  const filteredCalculations = calculations
    .filter(calc => {
      const matchesSearch = calc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           calc.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = filterType === 'all' || calc.subcategory === filterType;
      return matchesSearch && matchesType;
    })
    .sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'date':
          comparison = new Date(a.created_at) - new Date(b.created_at);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        default:
          comparison = 0;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // Обработчики событий
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleFilterChange = (e) => {
    setFilterType(e.target.value);
  };

  const handleSortChange = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const handleNewCalculation = (typeId) => {
    const selectedType = calculationTypes.find(t => t.id === typeId);
    if (selectedType) {
      setSelectedCalculation(selectedType);
      setShowStructuralModal(true);
    }
  };

  // Получение иконки для типа расчета
  const getCalculationIcon = (typeId) => {
    switch (typeId) {
      case 'strength':
        return <Target className="w-6 h-6" />;
      case 'stability':
        return <TrendingUp className="w-6 h-6" />;
      case 'stiffness':
        return <BarChart3 className="w-6 h-6" />;
      case 'cracking':
        return <Layers className="w-6 h-6" />;
      case 'dynamic':
        return <Activity className="w-6 h-6" />;
      default:
        return <Calculator className="w-6 h-6" />;
    }
  };

  // Получение цвета для типа расчета
  const getCalculationColor = (typeId) => {
    switch (typeId) {
      case 'strength':
        return 'bg-red-100 text-red-800';
      case 'stability':
        return 'bg-blue-100 text-blue-800';
      case 'stiffness':
        return 'bg-green-100 text-green-800';
      case 'cracking':
        return 'bg-yellow-100 text-yellow-800';
      case 'dynamic':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loadingTypes) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Загрузка типов расчетов...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Settings className="w-8 h-8 mr-3 text-blue-600" />
            Строительные конструкции
          </h1>
          <p className="text-gray-600 mt-1">
            Расчеты прочности, устойчивости и деформаций строительных конструкций
          </p>
        </div>
      </div>

      {/* Фильтры и поиск */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Поиск расчетов..."
                value={searchTerm}
                onChange={handleSearchChange}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={handleFilterChange}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Все типы</option>
              {calculationTypes.map(type => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
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

      {/* Виды расчетов строительных конструкций */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {calculationTypes.map((type) => (
          <div
            key={type.id}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow border border-gray-200"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="text-blue-600">
                {getCalculationIcon(type.id)}
              </div>
              <span className={`text-xs px-2 py-1 rounded-full ${getCalculationColor(type.id)}`}>
                {type.name.split(' ')[0]}
              </span>
            </div>
            
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {type.name}
            </h3>
            
            <p className="text-gray-600 text-sm mb-4">
              {type.description}
            </p>
            
            <div className="space-y-2 mb-4">
              <p className="text-xs font-medium text-gray-700">Применяемые нормы:</p>
              {type.norms.slice(0, 2).map((norm, index) => (
                <p key={index} className="text-xs text-gray-500 flex items-center">
                  <FileText className="w-3 h-3 mr-1" />
                  {norm}
                </p>
              ))}
              {type.norms.length > 2 && (
                <p className="text-xs text-gray-400">и еще {type.norms.length - 2}...</p>
              )}
            </div>

            <div className="space-y-1 mb-4">
              <p className="text-xs font-medium text-gray-700">Параметры:</p>
              {type.parameters.slice(0, 3).map((param, index) => (
                <p key={index} className="text-xs text-gray-500">
                  • {param.label} ({param.unit})
                </p>
              ))}
              {type.parameters.length > 3 && (
                <p className="text-xs text-gray-400">и еще {type.parameters.length - 3}...</p>
              )}
            </div>
            
            <button 
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center"
              onClick={() => handleNewCalculation(type.id)}
            >
              <Plus className="w-4 h-4 mr-2" />
              Создать расчет
            </button>
          </div>
        ))}
      </div>

      {/* Список существующих расчетов */}
      {calculations.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Мои расчеты строительных конструкций ({filteredCalculations.length})
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Название
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Тип расчета
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Статус
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Дата создания
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCalculations.map((calculation) => (
                  <tr key={calculation.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {calculation.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {calculation.description}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getCalculationIcon(calculation.subcategory || calculation.type)}
                        <span className="ml-2 text-sm text-gray-900">
                          {calculationTypes.find(t => t.id === (calculation.subcategory || calculation.type))?.name || calculation.type}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        calculation.status === 'completed' ? 'bg-green-100 text-green-800' :
                        calculation.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {calculation.status === 'completed' ? 'Завершен' :
                         calculation.status === 'processing' ? 'В обработке' : 'Ошибка'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(calculation.created_at).toLocaleDateString('ru-RU')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button 
                          className="text-blue-600 hover:text-blue-900"
                          title="Просмотреть расчет"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button 
                          className="text-green-600 hover:text-green-900"
                          title="Скачать результат"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => deleteCalculation(calculation.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Удалить расчет"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Сообщения об ошибках и успехе */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
            <p className="text-green-800">{success}</p>
          </div>
        </div>
      )}

      {/* Модальное окно создания структурного расчета */}
      {showStructuralModal && selectedCalculation && (
        <StructuralCalculationModal
          isOpen={showStructuralModal}
          onClose={() => setShowStructuralModal(false)}
          onCreateCalculation={createStructuralCalculation}
          loading={loading}
          selectedCategoryData={selectedCalculation}
        />
      )}
    </div>
  );
};

export default StructuralCalculationsPage;
