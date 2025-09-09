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
  Layers,
  Wind,
  Flame,
  AlertTriangle,
  Gauge
} from 'lucide-react';
import DegasificationCalculationModal from '../components/DegasificationCalculationModal';

const DegasificationCalculationsPage = () => {
  const [calculations, setCalculations] = useState([]);
  const [calculationTypes, setCalculationTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedCalculation, setSelectedCalculation] = useState(null);
  const [showDegasificationModal, setShowDegasificationModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // API конфигурация
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://localhost/api';

  // Загрузка типов расчетов
  useEffect(() => {
    const loadCalculationTypes = async () => {
      try {
        setLoadingTypes(true);
        const response = await fetch(`${API_BASE_URL}/calculations/degasification/types`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setCalculationTypes(data);
        setLoadingTypes(false);
      } catch (error) {
        console.error('Error loading calculation types:', error);
        setError('Ошибка загрузки типов расчетов');
        setLoadingTypes(false);
      }
    };

    loadCalculationTypes();
  }, []);

  // Загрузка расчетов
  const loadCalculations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/calculations?type=degasification`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setCalculations(data);
    } catch (error) {
      console.error('Error loading calculations:', error);
      setError('Ошибка загрузки расчетов');
    } finally {
      setLoading(false);
    }
  };

  // Выполнение расчета
  const executeCalculation = async (calculationData) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/calculations/degasification/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(calculationData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSuccess('Расчет выполнен успешно');
      loadCalculations();
      return result;
    } catch (error) {
      console.error('Error executing calculation:', error);
      setError('Ошибка выполнения расчета');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Сохранение расчета
  const saveCalculation = async (calculationData) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/calculations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: calculationData.name,
          type: 'degasification',
          category: 'methane_extraction',
          parameters: calculationData.parameters,
          results: calculationData.results
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSuccess('Расчет сохранен успешно');
      loadCalculations();
      return result;
    } catch (error) {
      console.error('Error saving calculation:', error);
      setError('Ошибка сохранения расчета');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Удаление расчета
  const deleteCalculation = async (calculationId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/calculations/${calculationId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setSuccess('Расчет удален успешно');
      loadCalculations();
    } catch (error) {
      console.error('Error deleting calculation:', error);
      setError('Ошибка удаления расчета');
    } finally {
      setLoading(false);
    }
  };

  // Экспорт в DOCX
  const exportToDOCX = async (calculationId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/calculations/${calculationId}/export-docx`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `degasification_calculation_${calculationId}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setSuccess('Файл экспортирован успешно');
    } catch (error) {
      console.error('Error exporting calculation:', error);
      setError('Ошибка экспорта расчета');
    } finally {
      setLoading(false);
    }
  };

  // Фильтрация и сортировка
  const filteredCalculations = calculations
    .filter(calc => {
      const matchesSearch = calc.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           calc.type?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filterType === 'all' || calc.type === filterType;
      return matchesSearch && matchesFilter;
    })
    .sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name || '';
          bValue = b.name || '';
          break;
        case 'type':
          aValue = a.type || '';
          bValue = b.type || '';
          break;
        case 'date':
        default:
          aValue = new Date(a.created_at || 0);
          bValue = new Date(b.created_at || 0);
          break;
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  // Получение иконки для типа расчета
  const getTypeIcon = (type) => {
    switch (type) {
      case 'methane_extraction':
        return <Wind className="w-4 h-4" />;
      case 'ventilation_requirements':
        return <Gauge className="w-4 h-4" />;
      case 'safety_systems':
        return <Shield className="w-4 h-4" />;
      default:
        return <Calculator className="w-4 h-4" />;
    }
  };

  // Получение цвета статуса
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Получение цвета безопасности
  const getSafetyColor = (safetyStatus) => {
    switch (safetyStatus) {
      case 'Безопасно':
        return 'text-green-600 bg-green-100';
      case 'Опасность':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-yellow-600 bg-yellow-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Wind className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    Расчеты дегазации угольных шахт
                  </h1>
                  <p className="text-sm text-gray-500">
                    Расчеты систем дегазации, вентиляции и безопасности
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowDegasificationModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="w-4 h-4 mr-2" />
                Новый расчет
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Уведомления */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Ошибка</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
                <button
                  onClick={() => setError(null)}
                  className="mt-2 text-sm text-red-600 hover:text-red-500"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Успешно</h3>
                <div className="mt-2 text-sm text-green-700">{success}</div>
                <button
                  onClick={() => setSuccess(null)}
                  className="mt-2 text-sm text-green-600 hover:text-green-500"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Фильтры и поиск */}
        <div className="mb-6 bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Поиск расчетов..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">Все типы</option>
              <option value="methane_extraction">Извлечение метана</option>
              <option value="ventilation_requirements">Требования к вентиляции</option>
              <option value="safety_systems">Системы безопасности</option>
            </select>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="date">По дате</option>
              <option value="name">По названию</option>
              <option value="type">По типу</option>
            </select>
            
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
              <span className="ml-2">Сортировка</span>
            </button>
          </div>
        </div>

        {/* Список расчетов */}
        <div className="bg-white rounded-lg shadow">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Загрузка расчетов...</p>
            </div>
          ) : filteredCalculations.length === 0 ? (
            <div className="p-8 text-center">
              <Wind className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Нет расчетов</h3>
              <p className="text-gray-500 mb-4">Создайте первый расчет дегазации</p>
              <button
                onClick={() => setShowDegasificationModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Создать расчет
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredCalculations.map((calculation) => (
                <div key={calculation.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        {getTypeIcon(calculation.type)}
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {calculation.name || 'Расчет дегазации'}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {calculation.type === 'methane_extraction' && 'Извлечение метана'}
                            {calculation.type === 'ventilation_requirements' && 'Требования к вентиляции'}
                            {calculation.type === 'safety_systems' && 'Системы безопасности'}
                          </p>
                        </div>
                      </div>
                      
                      {calculation.results && (
                        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center space-x-2">
                              <Wind className="w-4 h-4 text-blue-600" />
                              <span className="text-sm font-medium text-gray-700">Объем угля</span>
                            </div>
                            <p className="text-lg font-semibold text-gray-900">
                              {calculation.results.coal_volume?.toFixed(2)} м³
                            </p>
                          </div>
                          
                          <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center space-x-2">
                              <Gauge className="w-4 h-4 text-green-600" />
                              <span className="text-sm font-medium text-gray-700">Концентрация метана</span>
                            </div>
                            <p className="text-lg font-semibold text-gray-900">
                              {(calculation.results.methane_concentration * 100)?.toFixed(4)}%
                            </p>
                          </div>
                          
                          <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center space-x-2">
                              <Shield className="w-4 h-4 text-purple-600" />
                              <span className="text-sm font-medium text-gray-700">Статус безопасности</span>
                            </div>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSafetyColor(calculation.results.safety_status)}`}>
                              {calculation.results.safety_status}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(calculation.status)}`}>
                        {calculation.status === 'completed' && 'Завершен'}
                        {calculation.status === 'running' && 'Выполняется'}
                        {calculation.status === 'failed' && 'Ошибка'}
                      </span>
                      
                      <button
                        onClick={() => setSelectedCalculation(calculation)}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Просмотр"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => exportToDOCX(calculation.id)}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Экспорт в DOCX"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => deleteCalculation(calculation.id)}
                        className="p-2 text-gray-400 hover:text-red-600"
                        title="Удалить"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Модальное окно для расчетов дегазации */}
      {showDegasificationModal && (
        <DegasificationCalculationModal
          calculationTypes={calculationTypes}
          onClose={() => setShowDegasificationModal(false)}
          onExecute={executeCalculation}
          onSave={saveCalculation}
        />
      )}

      {/* Модальное окно для просмотра расчета */}
      {selectedCalculation && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {selectedCalculation.name || 'Расчет дегазации'}
                </h3>
                <button
                  onClick={() => setSelectedCalculation(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              {selectedCalculation.results && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Объем угля</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {selectedCalculation.results.coal_volume?.toFixed(2)} м³
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Масса угля</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {selectedCalculation.results.coal_mass?.toFixed(2)} т
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Содержание метана</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {selectedCalculation.results.total_methane_content?.toFixed(2)} м³
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Выделение метана</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {selectedCalculation.results.daily_methane_emission?.toFixed(2)} м³/сут
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Требуемый расход воздуха</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {selectedCalculation.results.required_air_flow?.toFixed(2)} м³/с
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Достаточность вентиляции</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {(selectedCalculation.results.ventilation_sufficiency * 100)?.toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Концентрация метана</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {(selectedCalculation.results.methane_concentration * 100)?.toFixed(4)}%
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Эффективность дегазации</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {selectedCalculation.results.degasification_efficiency?.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700">Статус безопасности</label>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSafetyColor(selectedCalculation.results.safety_status)}`}>
                      {selectedCalculation.results.safety_status}
                    </span>
                  </div>
                  
                  {selectedCalculation.results.safety_recommendations && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Рекомендации по безопасности</label>
                      <ul className="mt-2 space-y-1">
                        {selectedCalculation.results.safety_recommendations.map((recommendation, index) => (
                          <li key={index} className="text-sm text-gray-600 flex items-start">
                            <AlertTriangle className="w-4 h-4 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                            {recommendation}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {selectedCalculation.results.normative_links && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Нормативные ссылки</label>
                      <div className="mt-2 space-y-1">
                        {Object.entries(selectedCalculation.results.normative_links).map(([doc, description]) => (
                          <div key={doc} className="text-sm text-gray-600">
                            <span className="font-medium">{doc}:</span> {description}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DegasificationCalculationsPage;
