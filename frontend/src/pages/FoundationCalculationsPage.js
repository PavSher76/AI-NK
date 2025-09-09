import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  FileText, 
  Settings, 
  CheckCircle, 
  AlertCircle,
  Info,
  BookOpen,
  Ruler,
  Zap,
  ArrowLeft,
  Save,
  Download
} from 'lucide-react';
import './CalculationsPage.css';

const FoundationCalculationsPage = ({ isAuthenticated, authToken }) => {
  const [selectedCategory, setSelectedCategory] = useState('bearing_capacity');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parameters: {}
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [results, setResults] = useState(null);

  // Виды расчетов оснований и фундаментов
  const foundationCategories = [
    {
      id: 'bearing_capacity',
      name: 'Расчёт несущей способности',
      description: 'Определение несущей способности основания',
      icon: '🏗️',
      norms: ['СП 22.13330.2016', 'СП 24.13330.2011'],
      parameters: [
        {
          name: 'foundation_width',
          label: 'Ширина фундамента',
          unit: 'м',
          type: 'number',
          required: true,
          default: 1.0,
          min: 0.3
        },
        {
          name: 'foundation_depth',
          label: 'Глубина заложения',
          unit: 'м',
          type: 'number',
          required: true,
          default: 1.5,
          min: 0.5
        },
        {
          name: 'soil_type',
          label: 'Тип грунта',
          unit: '',
          type: 'select',
          required: true,
          default: 'clay',
          options: [
            { value: 'clay', label: 'Глина' },
            { value: 'sand', label: 'Песок' },
            { value: 'loam', label: 'Суглинок' },
            { value: 'sandy_loam', label: 'Супесь' }
          ]
        },
        {
          name: 'soil_density',
          label: 'Плотность грунта',
          unit: 'кг/м³',
          type: 'number',
          required: true,
          default: 1800,
          min: 1000
        },
        {
          name: 'angle_of_friction',
          label: 'Угол внутреннего трения',
          unit: 'град',
          type: 'number',
          required: true,
          default: 25,
          min: 10,
          max: 45
        },
        {
          name: 'cohesion',
          label: 'Сцепление',
          unit: 'кПа',
          type: 'number',
          required: true,
          default: 20,
          min: 0
        }
      ]
    },
    {
      id: 'settlement',
      name: 'Расчёт осадок',
      description: 'Определение осадок фундамента',
      icon: '📏',
      norms: ['СП 22.13330.2016', 'СП 24.13330.2011'],
      parameters: [
        {
          name: 'foundation_area',
          label: 'Площадь фундамента',
          unit: 'м²',
          type: 'number',
          required: true,
          default: 10.0,
          min: 1.0
        },
        {
          name: 'foundation_pressure',
          label: 'Давление под подошвой',
          unit: 'кПа',
          type: 'number',
          required: true,
          default: 200,
          min: 50
        },
        {
          name: 'compression_modulus',
          label: 'Модуль деформации',
          unit: 'МПа',
          type: 'number',
          required: true,
          default: 10,
          min: 1
        },
        {
          name: 'poisson_ratio',
          label: 'Коэффициент Пуассона',
          unit: '',
          type: 'number',
          required: true,
          default: 0.3,
          min: 0.1,
          max: 0.5
        },
        {
          name: 'layer_thickness',
          label: 'Толщина сжимаемого слоя',
          unit: 'м',
          type: 'number',
          required: true,
          default: 5.0,
          min: 1.0
        }
      ]
    },
    {
      id: 'slope_stability',
      name: 'Расчёт устойчивости склонов',
      description: 'Проверка устойчивости откосов и склонов',
      icon: '⛰️',
      norms: ['СП 22.13330.2016', 'СП 47.13330.2016'],
      parameters: [
        {
          name: 'slope_height',
          label: 'Высота откоса',
          unit: 'м',
          type: 'number',
          required: true,
          default: 5.0,
          min: 1.0
        },
        {
          name: 'slope_angle',
          label: 'Угол откоса',
          unit: 'град',
          type: 'number',
          required: true,
          default: 30,
          min: 10,
          max: 60
        },
        {
          name: 'soil_density',
          label: 'Плотность грунта',
          unit: 'кг/м³',
          type: 'number',
          required: true,
          default: 1800,
          min: 1000
        },
        {
          name: 'angle_of_friction',
          label: 'Угол внутреннего трения',
          unit: 'град',
          type: 'number',
          required: true,
          default: 25,
          min: 10,
          max: 45
        },
        {
          name: 'cohesion',
          label: 'Сцепление',
          unit: 'кПа',
          type: 'number',
          required: true,
          default: 20,
          min: 0
        },
        {
          name: 'water_pressure',
          label: 'Напор грунтовых вод',
          unit: 'кПа',
          type: 'number',
          required: false,
          default: 0,
          min: 0
        }
      ]
    },
    {
      id: 'seismic_analysis',
      name: 'Сейсмический анализ',
      description: 'Расчет на сейсмические воздействия',
      icon: '🌊',
      norms: ['СП 14.13330.2014', 'СП 22.13330.2016'],
      parameters: [
        {
          name: 'seismic_intensity',
          label: 'Сейсмическая интенсивность',
          unit: 'баллы',
          type: 'select',
          required: true,
          default: '6',
          options: [
            { value: '6', label: '6 баллов' },
            { value: '7', label: '7 баллов' },
            { value: '8', label: '8 баллов' },
            { value: '9', label: '9 баллов' }
          ]
        },
        {
          name: 'soil_category',
          label: 'Категория грунта',
          unit: '',
          type: 'select',
          required: true,
          default: 'B',
          options: [
            { value: 'A', label: 'A - Скальные грунты' },
            { value: 'B', label: 'B - Плотные грунты' },
            { value: 'C', label: 'C - Средние грунты' },
            { value: 'D', label: 'D - Слабые грунты' }
          ]
        },
        {
          name: 'structure_weight',
          label: 'Вес сооружения',
          unit: 'кН',
          type: 'number',
          required: true,
          default: 1000,
          min: 100
        },
        {
          name: 'natural_period',
          label: 'Собственный период',
          unit: 'с',
          type: 'number',
          required: true,
          default: 0.5,
          min: 0.1
        },
        {
          name: 'damping_ratio',
          label: 'Коэффициент демпфирования',
          unit: '',
          type: 'number',
          required: true,
          default: 0.05,
          min: 0.01,
          max: 0.1
        }
      ]
    },
    {
      id: 'groundwater',
      name: 'Расчёт подземных вод',
      description: 'Анализ влияния подземных вод',
      icon: '💧',
      norms: ['СП 22.13330.2016', 'СП 47.13330.2016'],
      parameters: [
        {
          name: 'water_level',
          label: 'Уровень грунтовых вод',
          unit: 'м',
          type: 'number',
          required: true,
          default: 2.0,
          min: 0.5
        },
        {
          name: 'water_pressure',
          label: 'Напор воды',
          unit: 'кПа',
          type: 'number',
          required: true,
          default: 20,
          min: 0
        },
        {
          name: 'permeability',
          label: 'Коэффициент фильтрации',
          unit: 'м/сут',
          type: 'number',
          required: true,
          default: 1.0,
          min: 0.001
        },
        {
          name: 'drainage_area',
          label: 'Площадь дренажа',
          unit: 'м²',
          type: 'number',
          required: true,
          default: 100,
          min: 1
        },
        {
          name: 'drainage_depth',
          label: 'Глубина дренажа',
          unit: 'м',
          type: 'number',
          required: true,
          default: 1.0,
          min: 0.5
        }
      ]
    }
  ];

  const selectedCategoryData = foundationCategories.find(cat => cat.id === selectedCategory);

  useEffect(() => {
    if (selectedCategoryData) {
      // Инициализируем параметры для выбранной категории
      const initialParameters = {};
      selectedCategoryData.parameters.forEach(param => {
        initialParameters[param.name] = param.default;
      });
      
      setFormData(prev => ({
        ...prev,
        parameters: initialParameters
      }));
    }
  }, [selectedCategory]);

  const handleParameterChange = (paramName, value) => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [paramName]: value
      }
    }));
  };

  const createCalculation = async (calculationData) => {
    if (!isAuthenticated || !authToken) {
      setError('Ошибка авторизации');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] FoundationCalculationsPage.js: Creating foundation calculation:', calculationData);
      
      // Сначала выполняем расчет
      const executeResponse = await fetch('https://localhost/api/calculations/geological/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          calculation_type: 'geological',
          parameters: {
            ...calculationData.parameters,
            calculation_subtype: selectedCategory
          }
        })
      });

      if (!executeResponse.ok) {
        const errorData = await executeResponse.json();
        throw new Error(errorData.detail || 'Ошибка выполнения расчета');
      }

      const calculationResult = await executeResponse.json();
      setResults(calculationResult);
      
      // Создаем запись в базе данных
      const createResponse = await fetch('https://localhost/api/calculations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          ...calculationData,
          result: calculationResult
        })
      });

      if (createResponse.ok) {
        setSuccess('Расчет основания и фундамента успешно создан и выполнен');
        console.log('🔍 [DEBUG] FoundationCalculationsPage.js: Foundation calculation created successfully');
      } else {
        const errorData = await createResponse.json();
        setError(errorData.message || 'Ошибка создания расчета');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] FoundationCalculationsPage.js: Foundation calculation error:', error);
      setError(error.message || 'Ошибка создания расчета основания');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const calculationData = {
      name: formData.name || `${selectedCategoryData.name} - ${new Date().toLocaleDateString()}`,
      description: formData.description || selectedCategoryData.description,
      type: 'foundation',
      category: 'construction',
      subcategory: selectedCategory,
      parameters: formData.parameters
    };

    createCalculation(calculationData);
  };

  const validateForm = () => {
    if (!formData.name.trim()) return false;
    
    // Проверяем обязательные параметры
    const requiredParams = selectedCategoryData.parameters.filter(p => p.required);
    for (const param of requiredParams) {
      const value = formData.parameters[param.name];
      if (value === undefined || value === null || value === '') return false;
      if (param.type === 'number' && (isNaN(value) || value < (param.min || 0))) return false;
    }
    
    return true;
  };

  const renderResults = () => {
    if (!results) return null;

    return (
      <div className="results-container">
        <h3>Результаты расчета</h3>
        <div className="results-grid">
          {Object.entries(results).map(([key, value]) => {
            if (key === 'normative_links' || key === 'safety_recommendations') return null;
            if (typeof value === 'object' && value !== null) {
              return (
                <div key={key} className="result-section">
                  <h4>{key.replace(/_/g, ' ').toUpperCase()}</h4>
                  <div className="result-details">
                    {Object.entries(value).map(([subKey, subValue]) => (
                      <div key={subKey} className="result-item">
                        <span className="result-label">{subKey.replace(/_/g, ' ')}:</span>
                        <span className="result-value">{typeof subValue === 'number' ? subValue.toFixed(2) : subValue}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }
            return null;
          })}
        </div>
        
        {results.normative_links && (
          <div className="normative-links">
            <h4>Нормативные документы</h4>
            <ul>
              {Object.entries(results.normative_links).map(([doc, description]) => (
                <li key={doc}><strong>{doc}:</strong> {description}</li>
              ))}
            </ul>
          </div>
        )}

        {results.safety_recommendations && (
          <div className="safety-recommendations">
            <h4>Рекомендации по безопасности</h4>
            <ul>
              {results.safety_recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  if (!isAuthenticated) {
    return (
      <div className="calculations-page">
        <div className="auth-required">
          <h2>Требуется авторизация</h2>
          <p>Для доступа к расчетам необходимо войти в систему</p>
        </div>
      </div>
    );
  }

  return (
    <div className="calculations-page">
      <div className="page-header">
        <div className="flex items-center mb-4">
          <button
            onClick={() => window.location.href = '/calculations'}
            className="flex items-center text-blue-600 hover:text-blue-800 mr-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Назад к расчетам
          </button>
        </div>
        <h1>Основания и фундаменты</h1>
        <p>Расчеты несущей способности оснований, осадок и деформаций фундаментов</p>
      </div>

      <div className="calculations-content">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Левая колонка - выбор типа расчета */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Виды расчетов</h3>
              <div className="space-y-3">
                {foundationCategories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`w-full p-4 border rounded-lg text-left transition-colors ${
                      selectedCategory === category.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <div className="flex items-center mb-2">
                      <span className="text-2xl mr-2">{category.icon}</span>
                      <h4 className="font-medium text-gray-900">{category.name}</h4>
                    </div>
                    <p className="text-sm text-gray-600">{category.description}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Правая колонка - форма расчета */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              {selectedCategoryData && (
                <>
                  <div className="flex items-center mb-6">
                    <span className="text-3xl mr-3">{selectedCategoryData.icon}</span>
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">{selectedCategoryData.name}</h2>
                      <p className="text-gray-600">{selectedCategoryData.description}</p>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg mb-6">
                    <h4 className="font-medium text-gray-700 mb-2">Применяемые нормы:</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedCategoryData.norms.map((norm, index) => (
                        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                          {norm}
                        </span>
                      ))}
                    </div>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Основные поля */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Название расчета
                        </label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => setFormData({...formData, name: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder={`${selectedCategoryData.name} - ${new Date().toLocaleDateString()}`}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Описание
                        </label>
                        <input
                          type="text"
                          value={formData.description}
                          onChange={(e) => setFormData({...formData, description: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder={selectedCategoryData.description}
                        />
                      </div>
                    </div>

                    {/* Параметры расчета */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Параметры расчета</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {selectedCategoryData.parameters.map((param) => (
                          <div key={param.name}>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              {param.label} {param.required && <span className="text-red-500">*</span>}
                            </label>
                            
                            {param.type === 'select' ? (
                              <select
                                value={formData.parameters[param.name] || param.default}
                                onChange={(e) => handleParameterChange(param.name, e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                required={param.required}
                              >
                                {param.options.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <div className="relative">
                                <input
                                  type={param.type}
                                  value={formData.parameters[param.name] || param.default}
                                  onChange={(e) => handleParameterChange(param.name, parseFloat(e.target.value) || e.target.value)}
                                  min={param.min}
                                  max={param.max}
                                  step={param.type === 'number' ? 'any' : undefined}
                                  className="w-full px-3 py-2 pr-12 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  required={param.required}
                                />
                                <span className="absolute right-3 top-2 text-gray-500 text-sm">
                                  {param.unit}
                                </span>
                              </div>
                            )}
                            
                            {param.min !== undefined && param.max !== undefined && (
                              <p className="text-xs text-gray-500 mt-1">
                                Диапазон: {param.min} - {param.max} {param.unit}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Кнопки */}
                    <div className="flex justify-end space-x-3 pt-6 border-t">
                      <button
                        type="button"
                        onClick={() => window.location.href = '/calculations'}
                        className="px-6 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                      >
                        Отмена
                      </button>
                      <button
                        type="submit"
                        disabled={loading || !validateForm()}
                        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                      >
                        {loading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Выполнение...
                          </>
                        ) : (
                          <>
                            <Calculator className="w-4 h-4 mr-2" />
                            Выполнить расчет
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Результаты */}
        {results && renderResults()}
      </div>

      {/* Сообщения об ошибках и успехе */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mt-6">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4 mt-6">
          <div className="flex">
            <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
            <p className="text-green-800">{success}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FoundationCalculationsPage;