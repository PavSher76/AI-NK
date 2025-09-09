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
  Wind,
  Fan,
  Droplets
} from 'lucide-react';

const VentilationCalculationModal = ({ 
  isOpen, 
  onClose, 
  onCreateCalculation, 
  loading = false 
}) => {
  const [selectedCategory, setSelectedCategory] = useState('air_exchange');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parameters: {}
  });

  // Виды расчетов вентиляции и кондиционирования
  const ventilationCategories = [
    {
      id: 'air_exchange',
      name: 'Расчёт воздухообмена',
      description: 'Определение необходимого воздухообмена в помещениях',
      icon: '💨',
      norms: ['СП 60.13330.2016', 'СП 7.13130.2013', 'СП 54.13330.2016'],
      parameters: [
        {
          name: 'room_volume',
          label: 'Объем помещения',
          unit: 'м³',
          type: 'number',
          required: true,
          default: 100,
          min: 1
        },
        {
          name: 'room_area',
          label: 'Площадь помещения',
          unit: 'м²',
          type: 'number',
          required: true,
          default: 25,
          min: 1
        },
        {
          name: 'occupancy',
          label: 'Количество людей',
          unit: 'чел',
          type: 'number',
          required: true,
          default: 5,
          min: 1
        },
        {
          name: 'room_type',
          label: 'Тип помещения',
          unit: '',
          type: 'select',
          required: true,
          options: ['Жилое', 'Офисное', 'Производственное', 'Складское', 'Торговое'],
          default: 'Офисное'
        },
        {
          name: 'air_quality_requirement',
          label: 'Требования к качеству воздуха',
          unit: '',
          type: 'select',
          required: true,
          options: ['Стандартные', 'Повышенные', 'Высокие'],
          default: 'Стандартные'
        }
      ]
    },
    {
      id: 'duct_sizing',
      name: 'Расчёт воздуховодов',
      description: 'Определение размеров и гидравлических характеристик воздуховодов',
      icon: '📐',
      norms: ['СП 60.13330.2016', 'СП 7.13130.2013'],
      parameters: [
        {
          name: 'air_flow_rate',
          label: 'Расход воздуха',
          unit: 'м³/ч',
          type: 'number',
          required: true,
          default: 1000,
          min: 100
        },
        {
          name: 'duct_length',
          label: 'Длина воздуховода',
          unit: 'м',
          type: 'number',
          required: true,
          default: 10,
          min: 1
        },
        {
          name: 'duct_material',
          label: 'Материал воздуховода',
          unit: '',
          type: 'select',
          required: true,
          options: ['Оцинкованная сталь', 'Нержавеющая сталь', 'Пластик', 'Гибкий'],
          default: 'Оцинкованная сталь'
        },
        {
          name: 'air_velocity',
          label: 'Скорость воздуха',
          unit: 'м/с',
          type: 'number',
          required: true,
          default: 5,
          min: 1,
          max: 15
        },
        {
          name: 'pressure_loss',
          label: 'Допустимые потери давления',
          unit: 'Па',
          type: 'number',
          required: true,
          default: 100,
          min: 10
        }
      ]
    },
    {
      id: 'fan_selection',
      name: 'Подбор вентиляторов',
      description: 'Расчет и подбор вентиляционного оборудования',
      icon: '🌀',
      norms: ['СП 60.13330.2016', 'СП 7.13130.2013'],
      parameters: [
        {
          name: 'total_air_flow',
          label: 'Общий расход воздуха',
          unit: 'м³/ч',
          type: 'number',
          required: true,
          default: 5000,
          min: 100
        },
        {
          name: 'total_pressure',
          label: 'Общее давление',
          unit: 'Па',
          type: 'number',
          required: true,
          default: 500,
          min: 50
        },
        {
          name: 'fan_type',
          label: 'Тип вентилятора',
          unit: '',
          type: 'select',
          required: true,
          options: ['Осевой', 'Центробежный', 'Диагональный', 'Тангенциальный'],
          default: 'Центробежный'
        },
        {
          name: 'installation_type',
          label: 'Тип установки',
          unit: '',
          type: 'select',
          required: true,
          options: ['Приточный', 'Вытяжной', 'Приточно-вытяжной'],
          default: 'Приточно-вытяжной'
        },
        {
          name: 'noise_requirement',
          label: 'Требования по шуму',
          unit: 'дБ',
          type: 'number',
          required: false,
          default: 45,
          min: 20,
          max: 80
        }
      ]
    },
    {
      id: 'cooling_load',
      name: 'Расчёт холодильной нагрузки',
      description: 'Определение тепловых нагрузок для кондиционирования',
      icon: '❄️',
      norms: ['СП 60.13330.2016', 'СП 7.13130.2013'],
      parameters: [
        {
          name: 'room_area',
          label: 'Площадь помещения',
          unit: 'м²',
          type: 'number',
          required: true,
          default: 50,
          min: 1
        },
        {
          name: 'room_height',
          label: 'Высота помещения',
          unit: 'м',
          type: 'number',
          required: true,
          default: 3,
          min: 2
        },
        {
          name: 'occupancy',
          label: 'Количество людей',
          unit: 'чел',
          type: 'number',
          required: true,
          default: 10,
          min: 1
        },
        {
          name: 'equipment_power',
          label: 'Мощность оборудования',
          unit: 'кВт',
          type: 'number',
          required: false,
          default: 2,
          min: 0
        },
        {
          name: 'lighting_power',
          label: 'Мощность освещения',
          unit: 'Вт/м²',
          type: 'number',
          required: false,
          default: 15,
          min: 0
        },
        {
          name: 'outdoor_temp',
          label: 'Наружная температура',
          unit: '°C',
          type: 'number',
          required: true,
          default: 35,
          min: -50,
          max: 50
        },
        {
          name: 'indoor_temp',
          label: 'Внутренняя температура',
          unit: '°C',
          type: 'number',
          required: true,
          default: 24,
          min: 15,
          max: 30
        }
      ]
    },
    {
      id: 'humidity_control',
      name: 'Расчёт влажностного режима',
      description: 'Определение параметров влажности и осушения воздуха',
      icon: '💧',
      norms: ['СП 60.13330.2016', 'СП 7.13130.2013'],
      parameters: [
        {
          name: 'room_volume',
          label: 'Объем помещения',
          unit: 'м³',
          type: 'number',
          required: true,
          default: 150,
          min: 1
        },
        {
          name: 'current_humidity',
          label: 'Текущая влажность',
          unit: '%',
          type: 'number',
          required: true,
          default: 70,
          min: 10,
          max: 100
        },
        {
          name: 'target_humidity',
          label: 'Целевая влажность',
          unit: '%',
          type: 'number',
          required: true,
          default: 50,
          min: 10,
          max: 100
        },
        {
          name: 'air_temperature',
          label: 'Температура воздуха',
          unit: '°C',
          type: 'number',
          required: true,
          default: 22,
          min: 0,
          max: 50
        },
        {
          name: 'moisture_sources',
          label: 'Источники влаги',
          unit: 'кг/ч',
          type: 'number',
          required: false,
          default: 0.5,
          min: 0
        }
      ]
    }
  ];

  const selectedCategoryData = ventilationCategories.find(cat => cat.id === selectedCategory);

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
        type: 'ventilation',
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
            Создание расчета вентиляции и кондиционирования
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
              {ventilationCategories.map((category) => (
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

export default VentilationCalculationModal;
