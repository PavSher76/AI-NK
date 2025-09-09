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
  Zap,
  Building,
  Mountain,
  Droplets
} from 'lucide-react';

const FoundationCalculationModal = ({ 
  isOpen, 
  onClose, 
  onCreateCalculation, 
  loading = false 
}) => {
  const [selectedCategory, setSelectedCategory] = useState('bearing_capacity');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parameters: {}
  });

  // Виды расчетов оснований и фундаментов
  const foundationCategories = [
    {
      id: 'bearing_capacity',
      name: 'Расчёт несущей способности основания',
      description: 'Определение несущей способности грунтового основания',
      icon: '🏢',
      norms: ['СП 22.13330.2016', 'СП 24.13330.2011', 'СП 25.13330.2012'],
      parameters: [
        {
          name: 'foundation_width',
          label: 'Ширина фундамента',
          unit: 'м',
          type: 'number',
          required: true,
          default: 1.0,
          min: 0.1
        },
        {
          name: 'foundation_length',
          label: 'Длина фундамента',
          unit: 'м',
          type: 'number',
          required: true,
          default: 1.0,
          min: 0.1
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
          name: 'soil_cohesion',
          label: 'Сцепление грунта',
          unit: 'кПа',
          type: 'number',
          required: true,
          default: 10,
          min: 0
        },
        {
          name: 'soil_friction_angle',
          label: 'Угол внутреннего трения',
          unit: 'град',
          type: 'number',
          required: true,
          default: 25,
          min: 0,
          max: 45
        },
        {
          name: 'soil_density',
          label: 'Плотность грунта',
          unit: 'т/м³',
          type: 'number',
          required: true,
          default: 1.8,
          min: 1.0,
          max: 3.0
        }
      ]
    },
    {
      id: 'settlement',
      name: 'Расчёт осадок фундамента',
      description: 'Определение осадок и деформаций фундамента',
      icon: '📐',
      norms: ['СП 22.13330.2016', 'СП 24.13330.2011'],
      parameters: [
        {
          name: 'foundation_area',
          label: 'Площадь фундамента',
          unit: 'м²',
          type: 'number',
          required: true,
          default: 10,
          min: 1
        },
        {
          name: 'load_intensity',
          label: 'Интенсивность нагрузки',
          unit: 'кПа',
          type: 'number',
          required: true,
          default: 200,
          min: 10
        },
        {
          name: 'soil_modulus',
          label: 'Модуль деформации грунта',
          unit: 'МПа',
          type: 'number',
          required: true,
          default: 20,
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
          name: 'compressible_thickness',
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
      name: 'Расчёт устойчивости откосов',
      description: 'Проверка устойчивости грунтовых откосов и склонов',
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
          min: 5,
          max: 60
        },
        {
          name: 'groundwater_level',
          label: 'Уровень грунтовых вод',
          unit: 'м',
          type: 'number',
          required: false,
          default: 0,
          min: 0
        },
        {
          name: 'safety_factor',
          label: 'Коэффициент запаса',
          unit: '',
          type: 'number',
          required: true,
          default: 1.3,
          min: 1.0,
          max: 2.0
        }
      ]
    },
    {
      id: 'pile_foundation',
      name: 'Расчёт свайных фундаментов',
      description: 'Расчет несущей способности и осадок свай',
      icon: '🏗️',
      norms: ['СП 24.13330.2011', 'СП 25.13330.2012'],
      parameters: [
        {
          name: 'pile_diameter',
          label: 'Диаметр сваи',
          unit: 'м',
          type: 'number',
          required: true,
          default: 0.4,
          min: 0.2
        },
        {
          name: 'pile_length',
          label: 'Длина сваи',
          unit: 'м',
          type: 'number',
          required: true,
          default: 8.0,
          min: 3.0
        },
        {
          name: 'pile_spacing',
          label: 'Шаг свай',
          unit: 'м',
          type: 'number',
          required: true,
          default: 2.0,
          min: 1.0
        },
        {
          name: 'pile_count',
          label: 'Количество свай',
          unit: 'шт',
          type: 'number',
          required: true,
          default: 4,
          min: 1
        },
        {
          name: 'pile_material',
          label: 'Материал сваи',
          unit: '',
          type: 'select',
          required: true,
          options: ['Железобетон', 'Сталь', 'Дерево'],
          default: 'Железобетон'
        }
      ]
    },
    {
      id: 'retaining_wall',
      name: 'Расчёт подпорных стен',
      description: 'Расчет устойчивости и прочности подпорных стен',
      icon: '🧱',
      norms: ['СП 22.13330.2016', 'СП 63.13330.2018'],
      parameters: [
        {
          name: 'wall_height',
          label: 'Высота стены',
          unit: 'м',
          type: 'number',
          required: true,
          default: 3.0,
          min: 1.0
        },
        {
          name: 'wall_thickness',
          label: 'Толщина стены',
          unit: 'м',
          type: 'number',
          required: true,
          default: 0.4,
          min: 0.2
        },
        {
          name: 'backfill_angle',
          label: 'Угол засыпки',
          unit: 'град',
          type: 'number',
          required: true,
          default: 30,
          min: 0,
          max: 45
        },
        {
          name: 'backfill_density',
          label: 'Плотность засыпки',
          unit: 'т/м³',
          type: 'number',
          required: true,
          default: 1.8,
          min: 1.0,
          max: 2.5
        },
        {
          name: 'wall_material',
          label: 'Материал стены',
          unit: '',
          type: 'select',
          required: true,
          options: ['Железобетон', 'Бетон', 'Кирпич', 'Камень'],
          default: 'Железобетон'
        }
      ]
    }
  ];

  const selectedCategoryData = foundationCategories.find(cat => cat.id === selectedCategory);

  useEffect(() => {
    if (selectedCategoryData) {
      const defaultParams = {};
      selectedCategoryData.parameters.forEach(param => {
        defaultParams[param.name] = param.default;
      });
      setFormData(prev => ({
        ...prev,
        parameters: defaultParams
      }));
    }
  }, [selectedCategory]);

  const handleInputChange = (paramName, value) => {
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
    if (validateForm()) {
      onCreateCalculation({
        type: 'foundation',
        category: selectedCategory,
        ...formData
      });
    }
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      alert('Пожалуйста, введите название расчета');
      return false;
    }
    
    if (!selectedCategoryData) {
      alert('Пожалуйста, выберите тип расчета');
      return false;
    }
    
    // Проверка обязательных параметров
    for (const param of selectedCategoryData.parameters) {
      if (param.required && (!formData.parameters[param.name] || formData.parameters[param.name] === '')) {
        alert(`Пожалуйста, заполните обязательное поле: ${param.label}`);
        return false;
      }
    }
    
    return true;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">
            Создание расчета оснований и фундаментов
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
              {foundationCategories.map((category) => (
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
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <span className="text-2xl mr-2">{selectedCategoryData.icon}</span>
                <h3 className="font-semibold text-blue-900">{selectedCategoryData.name}</h3>
              </div>
              <p className="text-blue-700 mb-3">{selectedCategoryData.description}</p>
              
              <div className="mb-3">
                <h4 className="font-medium text-blue-900 mb-2">Применяемые нормы:</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedCategoryData.norms.map((norm, index) => (
                    <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                      {norm}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Основная информация */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Название расчета *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Введите название расчета"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Описание
              </label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Краткое описание расчета"
              />
            </div>
          </div>

          {/* Параметры расчета */}
          {selectedCategoryData && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Параметры расчета
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedCategoryData.parameters.map((param) => (
                  <div key={param.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {param.label} {param.required && '*'}
                      {param.unit && <span className="text-gray-500"> ({param.unit})</span>}
                    </label>
                    
                    {param.type === 'select' ? (
                      <select
                        value={formData.parameters[param.name] || param.default}
                        onChange={(e) => handleInputChange(param.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required={param.required}
                      >
                        {param.options.map((option) => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={param.type}
                        value={formData.parameters[param.name] || param.default}
                        onChange={(e) => handleInputChange(param.name, e.target.value)}
                        min={param.min}
                        max={param.max}
                        step={param.type === 'number' ? '0.01' : undefined}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required={param.required}
                      />
                    )}
                    
                    {param.min !== undefined && param.max !== undefined && (
                      <p className="text-xs text-gray-500 mt-1">
                        Диапазон: {param.min} - {param.max}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Кнопки */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
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

export default FoundationCalculationModal;
