import React, { useState, useEffect } from 'react';
import { 
  X, 
  Calculator, 
  FileText, 
  Settings, 
  CheckCircle, 
  AlertCircle,
  Info,
  BookOpen,
  Ruler,
  Zap
} from 'lucide-react';

const StructuralCalculationModal = ({ 
  isOpen, 
  onClose, 
  onCreateCalculation, 
  loading = false 
}) => {
  const [selectedCategory, setSelectedCategory] = useState('strength');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parameters: {}
  });

  // Виды расчетов строительных конструкций
  const structuralCategories = [
    {
      id: 'strength',
      name: 'Расчёт на прочность',
      description: 'Проверка прочности элементов конструкций',
      icon: '🏗️',
      norms: ['СП 63.13330', 'СП 16.13330', 'EN 1992', 'EN 1993'],
      parameters: [
        {
          name: 'load_value',
          label: 'Расчетная нагрузка',
          unit: 'кН',
          type: 'number',
          required: true,
          default: 100,
          min: 0
        },
        {
          name: 'section_area',
          label: 'Площадь сечения',
          unit: 'см²',
          type: 'number',
          required: true,
          default: 100,
          min: 1
        },
        {
          name: 'material_strength',
          label: 'Расчетное сопротивление материала',
          unit: 'МПа',
          type: 'number',
          required: true,
          default: 235,
          min: 100
        },
        {
          name: 'safety_factor',
          label: 'Коэффициент надежности',
          unit: '',
          type: 'number',
          required: false,
          default: 1.1,
          min: 1.0,
          max: 2.0
        }
      ]
    },
    {
      id: 'stability',
      name: 'Расчёт на устойчивость',
      description: 'Проверка устойчивости сжатых элементов',
      icon: '📏',
      norms: ['СП 16.13330', 'СП 63.13330', 'EN 1993'],
      parameters: [
        {
          name: 'element_length',
          label: 'Длина элемента',
          unit: 'м',
          type: 'number',
          required: true,
          default: 3.0,
          min: 0.1
        },
        {
          name: 'moment_of_inertia',
          label: 'Момент инерции',
          unit: 'см⁴',
          type: 'number',
          required: true,
          default: 1000,
          min: 1
        },
        {
          name: 'elastic_modulus',
          label: 'Модуль упругости',
          unit: 'МПа',
          type: 'number',
          required: true,
          default: 210000,
          min: 10000
        },
        {
          name: 'end_conditions',
          label: 'Тип закрепления',
          unit: '',
          type: 'select',
          required: true,
          default: 'pinned',
          options: [
            { value: 'pinned', label: 'Шарнирное' },
            { value: 'fixed', label: 'Жесткое' },
            { value: 'cantilever', label: 'Консольное' }
          ]
        }
      ]
    },
    {
      id: 'stiffness',
      name: 'Расчёт на жёсткость',
      description: 'Проверка прогибов и деформаций',
      icon: '📐',
      norms: ['СП 63.13330', 'СП 64.13330', 'EN 1995'],
      parameters: [
        {
          name: 'span_length',
          label: 'Пролет',
          unit: 'м',
          type: 'number',
          required: true,
          default: 6.0,
          min: 0.5
        },
        {
          name: 'distributed_load',
          label: 'Распределенная нагрузка',
          unit: 'кН/м',
          type: 'number',
          required: true,
          default: 10.0,
          min: 0
        },
        {
          name: 'moment_of_inertia',
          label: 'Момент инерции',
          unit: 'см⁴',
          type: 'number',
          required: true,
          default: 5000,
          min: 1
        },
        {
          name: 'elastic_modulus',
          label: 'Модуль упругости',
          unit: 'МПа',
          type: 'number',
          required: true,
          default: 210000,
          min: 10000
        }
      ]
    },
    {
      id: 'cracking',
      name: 'Расчёт на трещиностойкость',
      description: 'Проверка ширины раскрытия трещин',
      icon: '🔍',
      norms: ['СП 63.13330', 'EN 1992'],
      parameters: [
        {
          name: 'reinforcement_area',
          label: 'Площадь арматуры',
          unit: 'мм²',
          type: 'number',
          required: true,
          default: 1000,
          min: 1
        },
        {
          name: 'concrete_class',
          label: 'Класс бетона',
          unit: '',
          type: 'select',
          required: true,
          default: 'B25',
          options: [
            { value: 'B15', label: 'B15' },
            { value: 'B20', label: 'B20' },
            { value: 'B25', label: 'B25' },
            { value: 'B30', label: 'B30' },
            { value: 'B35', label: 'B35' }
          ]
        },
        {
          name: 'bending_moment',
          label: 'Изгибающий момент',
          unit: 'кН·м',
          type: 'number',
          required: true,
          default: 50.0,
          min: 0
        },
        {
          name: 'crack_width_limit',
          label: 'Предельная ширина трещин',
          unit: 'мм',
          type: 'number',
          required: true,
          default: 0.3,
          min: 0.1,
          max: 1.0
        }
      ]
    },
    {
      id: 'dynamic',
      name: 'Динамический расчёт',
      description: 'Расчет на сейсмические воздействия',
      icon: '🌊',
      norms: ['СП 14.13330', 'EN 1998'],
      parameters: [
        {
          name: 'seismic_zone',
          label: 'Сейсмический район',
          unit: '',
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
          label: 'Масса конструкции',
          unit: 'т',
          type: 'number',
          required: true,
          default: 100.0,
          min: 1
        },
        {
          name: 'natural_period',
          label: 'Собственный период колебаний',
          unit: 'с',
          type: 'number',
          required: true,
          default: 0.5,
          min: 0.1
        }
      ]
    }
  ];

  const selectedCategoryData = structuralCategories.find(cat => cat.id === selectedCategory);

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

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const calculationData = {
      name: formData.name || `${selectedCategoryData.name} - ${new Date().toLocaleDateString()}`,
      description: formData.description || selectedCategoryData.description,
      type: 'structural',
      category: 'construction',
      subcategory: selectedCategory,
      parameters: formData.parameters
    };

    onCreateCalculation(calculationData);
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">
            Создание расчета строительных конструкций
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Выбор категории расчета */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Вид расчета
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {structuralCategories.map((category) => (
                <button
                  key={category.id}
                  type="button"
                  onClick={() => setSelectedCategory(category.id)}
                  className={`p-4 border rounded-lg text-left transition-colors ${
                    selectedCategory === category.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-2">{category.icon}</span>
                    <h3 className="font-medium text-gray-900">{category.name}</h3>
                  </div>
                  <p className="text-sm text-gray-600">{category.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Информация о выбранной категории */}
          {selectedCategoryData && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <span className="text-2xl mr-2">{selectedCategoryData.icon}</span>
                <h3 className="text-lg font-medium text-gray-900">{selectedCategoryData.name}</h3>
              </div>
              <p className="text-gray-600 mb-3">{selectedCategoryData.description}</p>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Применяемые нормы:</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedCategoryData.norms.map((norm, index) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                      {norm}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

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
                placeholder={`${selectedCategoryData?.name || 'Расчет'} - ${new Date().toLocaleDateString()}`}
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
                placeholder={selectedCategoryData?.description}
              />
            </div>
          </div>

          {/* Параметры расчета */}
          {selectedCategoryData && (
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
          )}

          {/* Кнопки */}
          <div className="flex justify-end space-x-3 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
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
                  Создание...
                </>
              ) : (
                <>
                  <Calculator className="w-4 h-4 mr-2" />
                  Создать расчет
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StructuralCalculationModal;
