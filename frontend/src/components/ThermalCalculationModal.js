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
  Thermometer,
  Sun,
  Snowflake
} from 'lucide-react';

const ThermalCalculationModal = ({ 
  isOpen, 
  onClose, 
  onCreateCalculation, 
  loading = false 
}) => {
  const [selectedCategory, setSelectedCategory] = useState('heat_transfer');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parameters: {}
  });

  // Виды теплотехнических расчетов
  const thermalCategories = [
    {
      id: 'heat_transfer',
      name: 'Расчёт теплопередачи через ограждения',
      description: 'Определение коэффициента теплопередачи и тепловых потерь',
      icon: '🌡️',
      norms: ['СП 50.13330.2012', 'СП 23-101-2004', 'ГОСТ 30494-2011'],
      parameters: [
        {
          name: 'wall_thickness',
          label: 'Толщина стены',
          unit: 'м',
          type: 'number',
          required: true,
          default: 0.4,
          min: 0.1
        },
        {
          name: 'wall_area',
          label: 'Площадь стены',
          unit: 'м²',
          type: 'number',
          required: true,
          default: 20.0,
          min: 1.0
        },
        {
          name: 'thermal_conductivity',
          label: 'Коэффициент теплопроводности',
          unit: 'Вт/(м·К)',
          type: 'number',
          required: true,
          default: 0.8,
          min: 0.01
        },
        {
          name: 'indoor_temp',
          label: 'Внутренняя температура',
          unit: '°C',
          type: 'number',
          required: true,
          default: 20,
          min: -50,
          max: 50
        },
        {
          name: 'outdoor_temp',
          label: 'Наружная температура',
          unit: '°C',
          type: 'number',
          required: true,
          default: -25,
          min: -50,
          max: 50
        },
        {
          name: 'heat_transfer_coeff',
          label: 'Коэффициент теплоотдачи',
          unit: 'Вт/(м²·К)',
          type: 'number',
          required: false,
          default: 8.7,
          min: 1.0
        }
      ]
    },
    {
      id: 'insulation',
      name: 'Расчёт теплоизоляции',
      description: 'Определение толщины теплоизоляционного слоя',
      icon: '🧊',
      norms: ['СП 50.13330.2012', 'СП 23-101-2004'],
      parameters: [
        {
          name: 'required_resistance',
          label: 'Требуемое сопротивление теплопередаче',
          unit: 'м²·К/Вт',
          type: 'number',
          required: true,
          default: 3.2,
          min: 0.5
        },
        {
          name: 'insulation_conductivity',
          label: 'Теплопроводность утеплителя',
          unit: 'Вт/(м·К)',
          type: 'number',
          required: true,
          default: 0.04,
          min: 0.01
        },
        {
          name: 'base_material_conductivity',
          label: 'Теплопроводность основного материала',
          unit: 'Вт/(м·К)',
          type: 'number',
          required: true,
          default: 0.8,
          min: 0.01
        },
        {
          name: 'base_material_thickness',
          label: 'Толщина основного материала',
          unit: 'м',
          type: 'number',
          required: true,
          default: 0.25,
          min: 0.05
        },
        {
          name: 'climate_zone',
          label: 'Климатическая зона',
          unit: '',
          type: 'select',
          required: true,
          options: ['I', 'II', 'III', 'IV', 'V'],
          default: 'II'
        }
      ]
    },
    {
      id: 'energy_efficiency',
      name: 'Расчёт энергоэффективности здания',
      description: 'Определение класса энергетической эффективности',
      icon: '⚡',
      norms: ['СП 50.13330.2012', 'СП 23-101-2004', 'ГОСТ 30494-2011'],
      parameters: [
        {
          name: 'building_area',
          label: 'Общая площадь здания',
          unit: 'м²',
          type: 'number',
          required: true,
          default: 1000,
          min: 10
        },
        {
          name: 'heated_volume',
          label: 'Отапливаемый объем',
          unit: 'м³',
          type: 'number',
          required: true,
          default: 3000,
          min: 100
        },
        {
          name: 'heating_consumption',
          label: 'Расход тепловой энергии на отопление',
          unit: 'кВт·ч/год',
          type: 'number',
          required: true,
          default: 50000,
          min: 1000
        },
        {
          name: 'ventilation_consumption',
          label: 'Расход энергии на вентиляцию',
          unit: 'кВт·ч/год',
          type: 'number',
          required: false,
          default: 10000,
          min: 0
        },
        {
          name: 'hot_water_consumption',
          label: 'Расход энергии на ГВС',
          unit: 'кВт·ч/год',
          type: 'number',
          required: false,
          default: 15000,
          min: 0
        },
        {
          name: 'building_type',
          label: 'Тип здания',
          unit: '',
          type: 'select',
          required: true,
          options: ['Жилое', 'Общественное', 'Производственное', 'Складское'],
          default: 'Жилое'
        }
      ]
    },
    {
      id: 'condensation',
      name: 'Расчёт конденсации влаги',
      description: 'Проверка образования конденсата в ограждениях',
      icon: '💧',
      norms: ['СП 50.13330.2012', 'СП 23-101-2004'],
      parameters: [
        {
          name: 'wall_composition',
          label: 'Состав стены',
          unit: '',
          type: 'select',
          required: true,
          options: ['Однослойная', 'Многослойная'],
          default: 'Многослойная'
        },
        {
          name: 'indoor_humidity',
          label: 'Влажность внутреннего воздуха',
          unit: '%',
          type: 'number',
          required: true,
          default: 55,
          min: 20,
          max: 90
        },
        {
          name: 'outdoor_humidity',
          label: 'Влажность наружного воздуха',
          unit: '%',
          type: 'number',
          required: true,
          default: 80,
          min: 20,
          max: 100
        },
        {
          name: 'vapor_permeability',
          label: 'Коэффициент паропроницаемости',
          unit: 'мг/(м·ч·Па)',
          type: 'number',
          required: true,
          default: 0.1,
          min: 0.001
        },
        {
          name: 'layer_thickness',
          label: 'Толщина слоя',
          unit: 'м',
          type: 'number',
          required: true,
          default: 0.1,
          min: 0.01
        }
      ]
    },
    {
      id: 'thermal_bridge',
      name: 'Расчёт тепловых мостов',
      description: 'Определение влияния тепловых мостов на теплопотери',
      icon: '🌉',
      norms: ['СП 50.13330.2012', 'СП 23-101-2004'],
      parameters: [
        {
          name: 'bridge_length',
          label: 'Длина теплового моста',
          unit: 'м',
          type: 'number',
          required: true,
          default: 1.0,
          min: 0.1
        },
        {
          name: 'bridge_width',
          label: 'Ширина теплового моста',
          unit: 'м',
          type: 'number',
          required: true,
          default: 0.1,
          min: 0.01
        },
        {
          name: 'bridge_conductivity',
          label: 'Теплопроводность материала моста',
          unit: 'Вт/(м·К)',
          type: 'number',
          required: true,
          default: 1.5,
          min: 0.01
        },
        {
          name: 'surrounding_conductivity',
          label: 'Теплопроводность окружающего материала',
          unit: 'Вт/(м·К)',
          type: 'number',
          required: true,
          default: 0.8,
          min: 0.01
        },
        {
          name: 'bridge_type',
          label: 'Тип теплового моста',
          unit: '',
          type: 'select',
          required: true,
          options: ['Линейный', 'Точечный', 'Геометрический'],
          default: 'Линейный'
        }
      ]
    }
  ];

  const selectedCategoryData = thermalCategories.find(cat => cat.id === selectedCategory);

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
        type: 'thermal',
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
            Создание теплотехнического расчета
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
              {thermalCategories.map((category) => (
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

export default ThermalCalculationModal;
