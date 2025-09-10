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
  X
} from 'lucide-react';
// import StructuralCalculationModal from '../components/StructuralCalculationModal'; // Удалено - теперь отдельная страница

const CalculationsPage = ({ isAuthenticated, authToken, calculationType = 'all' }) => {
  const [calculations, setCalculations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedCalculation, setSelectedCalculation] = useState(null);
  const [showNewCalculationModal, setShowNewCalculationModal] = useState(false);
  const [showViewCalculationModal, setShowViewCalculationModal] = useState(false);
  const [viewingCalculation, setViewingCalculation] = useState(null);
  // const [showStructuralModal, setShowStructuralModal] = useState(false); // Удалено - теперь отдельная страница
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // API конфигурация
  const API_BASE = process.env.REACT_APP_API_BASE || '/api';

  // Виды расчетов в соответствии с нормами и методиками
  const calculationTypes = [
    {
      id: 'structural',
      name: 'Строительные конструкции',
      category: 'construction',
      description: 'Расчеты прочности, устойчивости и деформаций строительных конструкций',
      norms: ['СП 20.13330.2016', 'СП 16.13330.2017', 'СП 63.13330.2018'],
      icon: '🏗️',
      subcategories: [
        {
          id: 'strength',
          name: 'Расчёт на прочность',
          description: 'Проверка прочности элементов конструкций',
          norms: ['СП 63.13330', 'СП 16.13330', 'EN 1992', 'EN 1993'],
          parameters: ['Нагрузки, кН', 'Площадь сечения, см²', 'Прочность материала, МПа']
        },
        {
          id: 'stability',
          name: 'Расчёт на устойчивость',
          description: 'Проверка устойчивости сжатых элементов',
          norms: ['СП 16.13330', 'СП 63.13330', 'EN 1993'],
          parameters: ['Длина элемента, м', 'Момент инерции', 'Модуль упругости']
        },
        {
          id: 'stiffness',
          name: 'Расчёт на жёсткость',
          description: 'Проверка прогибов и деформаций',
          norms: ['СП 63.13330', 'СП 64.13330', 'EN 1995'],
          parameters: ['Пролет, м', 'Нагрузка, кН/м', 'Момент инерции']
        },
        {
          id: 'cracking',
          name: 'Расчёт на трещиностойкость',
          description: 'Проверка ширины раскрытия трещин',
          norms: ['СП 63.13330', 'EN 1992'],
          parameters: ['Арматура, мм²', 'Класс бетона', 'Момент, кН·м']
        },
        {
          id: 'dynamic',
          name: 'Динамический расчёт',
          description: 'Расчет на сейсмические воздействия',
          norms: ['СП 14.13330', 'EN 1998'],
          parameters: ['Сейсмический район', 'Категория грунта', 'Масса конструкции']
        }
      ]
    },
    {
      id: 'foundation',
      name: 'Основания и фундаменты',
      category: 'construction',
      description: 'Расчеты несущей способности оснований, осадок и деформаций фундаментов',
      norms: ['СП 22.13330.2016', 'СП 24.13330.2011', 'СП 25.13330.2012'],
      icon: '🏢'
    },
    {
      id: 'thermal',
      name: 'Теплотехнические расчеты',
      category: 'engineering',
      description: 'Расчеты теплопередачи, теплоизоляции и энергоэффективности',
      norms: ['СП 50.13330.2012', 'СП 23-101-2004', 'ГОСТ 30494-2011'],
      icon: '🌡️'
    },
    {
      id: 'ventilation',
      name: 'Вентиляция и кондиционирование',
      category: 'engineering',
      description: 'Расчеты воздухообмена, вентиляционных систем и микроклимата',
      norms: ['СП 60.13330.2016', 'СП 7.13130.2013', 'СП 54.13330.2016'],
      icon: '💨'
    },
    {
      id: 'electrical',
      name: 'Электротехнические расчеты',
      category: 'engineering',
      description: 'Расчеты электрических нагрузок, заземления и молниезащиты',
      norms: ['СП 31.110-2003', 'СП 437.1325800.2018', 'СП 256.1325800.2016'],
      icon: '⚡'
    },
    {
      id: 'degasification',
      name: 'Дегазация угольных шахт',
      category: 'mining',
      description: 'Расчеты систем дегазации угольных шахт и извлечения метана',
      norms: ['ГОСТ Р 55154-2012', 'ПБ 05-618-03', 'СП 31.110-2003'],
      icon: '⛏️'
    },
    {
      id: 'water',
      name: 'Водоснабжение и водоотведение',
      category: 'engineering',
      description: 'Расчеты водопотребления, гидравлики трубопроводов и очистки',
      norms: ['СП 30.13330.2016', 'СП 32.13330.2018', 'СП 31.13330.2012'],
      icon: '💧'
    },
    {
      id: 'fire',
      name: 'Пожарная безопасность',
      category: 'safety',
      description: 'Расчеты пожарных рисков, эвакуации и огнестойкости',
      norms: ['СП 1.13130.2020', 'СП 2.13130.2020', 'СП 3.13130.2009'],
      icon: '🔥'
    },
    {
      id: 'acoustic',
      name: 'Акустические расчеты',
      category: 'engineering',
      description: 'Расчеты звукоизоляции, шума и вибраций',
      norms: ['СП 51.13330.2011', 'СП 23-103-2003', 'СП 54.13330.2016'],
      icon: '🔊'
    },
    {
      id: 'lighting',
      name: 'Освещение и инсоляция',
      category: 'engineering',
      description: 'Расчеты естественного и искусственного освещения',
      norms: ['СП 52.13330.2016', 'СП 54.13330.2016', 'СП 23-102-2003'],
      icon: '💡'
    },
    {
      id: 'geotechnical',
      name: 'Инженерно-геологические расчеты',
      category: 'geology',
      description: 'Расчеты грунтовых условий, склонов и подземных вод',
      norms: ['СП 47.13330.2016', 'СП 11-105-97', 'СП 22.13330.2016'],
      icon: '🌍'
    },
    {
      id: 'uav_protection',
      name: 'Защита от БПЛА',
      category: 'safety',
      description: 'Расчеты защиты от воздействия беспилотных летательных аппаратов',
      norms: ['ГОСТ Р 58888-2020', 'СП 1.13130.2020', 'СП 2.13130.2020'],
      icon: '🛡️',
      subcategories: [
        {
          id: 'shock_wave',
          name: 'Расчёт воздействия ударной волны',
          description: 'Расчет воздействия ударной волны от взрыва БПЛА на конструкции',
          norms: ['ГОСТ Р 58888-2020', 'СП 1.13130.2020', 'СП 20.13330.2016'],
          parameters: ['Масса БПЛА, кг', 'Расстояние до объекта, м', 'Тип взрывчатого вещества', 'Высота взрыва, м', 'Материал конструкции']
        },
        {
          id: 'impact_penetration',
          name: 'Расчёт попадания БПЛА в конструкцию',
          description: 'Расчет проникающей способности БПЛА и повреждений конструкций',
          norms: ['ГОСТ Р 58888-2020', 'СП 20.13330.2016', 'СП 16.13330.2017'],
          parameters: ['Скорость БПЛА, м/с', 'Масса БПЛА, кг', 'Материал БПЛА', 'Толщина конструкции, мм', 'Прочность материала, МПа']
        }
      ]
    }
  ];

  // Категории для фильтрации
  const categories = [
    { id: 'all', name: 'Все категории' },
    { id: 'construction', name: 'Строительство' },
    { id: 'engineering', name: 'Инженерные системы' },
    { id: 'safety', name: 'Безопасность' },
    { id: 'geology', name: 'Геология' },
    { id: 'mining', name: 'Горное дело' }
  ];

  // Загрузка расчетов
  const fetchCalculations = async () => {
    if (!isAuthenticated || !authToken) {
      console.log('🔍 [DEBUG] CalculationsPage.js: Not authenticated, skipping fetch');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] CalculationsPage.js: Fetching calculations');
      const response = await fetch(`${API_BASE}/calculations`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('🔍 [DEBUG] CalculationsPage.js: Calculations loaded:', data?.length || 0);
        setCalculations(data || []);
      } else if (response.status === 401) {
        setError('Ошибка авторизации. Пожалуйста, войдите в систему.');
      } else if (response.status === 503) {
        setError('Сервис расчетов временно недоступен. Попробуйте позже.');
      } else {
        setError('Ошибка загрузки расчетов');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] CalculationsPage.js: Fetch error:', error);
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        setError('Ошибка сети. Проверьте подключение к интернету.');
      } else {
        setError('Ошибка загрузки расчетов');
      }
    } finally {
      setLoading(false);
    }
  };

  // Создание нового расчета
  const createCalculation = async (calculationData) => {
    if (!isAuthenticated || !authToken) {
      setError('Ошибка авторизации');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] CalculationsPage.js: Creating calculation:', calculationData);
      const response = await fetch(`${API_BASE}/calculations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(calculationData)
      });

      if (response.ok) {
        const newCalculation = await response.json();
        setCalculations(prev => [newCalculation, ...prev]);
        setSuccess('Расчет успешно создан');
        setShowNewCalculationModal(false);
        console.log('🔍 [DEBUG] CalculationsPage.js: Calculation created successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Ошибка создания расчета');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] CalculationsPage.js: Create error:', error);
      setError('Ошибка создания расчета');
    } finally {
      setLoading(false);
    }
  };

  // Функция createStructuralCalculation удалена - теперь структурные расчеты на отдельной странице

  // Удаление расчета
  const deleteCalculation = async (calculationId) => {
    if (!isAuthenticated || !authToken) {
      setError('Ошибка авторизации');
      return;
    }

    if (!window.confirm('Вы уверены, что хотите удалить этот расчет? Это действие нельзя отменить.')) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] CalculationsPage.js: Deleting calculation:', calculationId);
      const response = await fetch(`${API_BASE}/calculations/${calculationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        setCalculations(prev => prev.filter(calc => calc.id !== calculationId));
        setSuccess('Расчет успешно удален');
        console.log('🔍 [DEBUG] CalculationsPage.js: Calculation deleted successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Ошибка удаления расчета');
      }
    } catch (error) {
      console.error('🔍 [DEBUG] CalculationsPage.js: Delete error:', error);
      setError('Ошибка удаления расчета');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка данных при монтировании
  useEffect(() => {
    if (isAuthenticated && authToken) {
      fetchCalculations();
    }
  }, [isAuthenticated, authToken]);

  // Фильтрация и сортировка расчетов
  const filteredCalculations = calculations
    .filter(calc => {
      const matchesSearch = calc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           calc.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = filterCategory === 'all' || calc.category === filterCategory;
      const matchesType = calculationType === 'all' || calc.type === calculationType;
      return matchesSearch && matchesCategory && matchesType;
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
    setFilterCategory(e.target.value);
  };

  const handleSortChange = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const handleNewCalculation = (type) => {
    setSelectedCalculation({ type, ...calculationTypes.find(t => t.id === type) });
    setShowNewCalculationModal(true);
  };

  // Просмотр расчета
  const handleViewCalculation = async (calculation) => {
    try {
      let calculationToView = { ...calculation };
      
      // Если результат отсутствует, выполняем расчет через соответствующий API endpoint
      if (!calculation.result) {
        console.log('🔍 [DEBUG] CalculationsPage.js: No result found for viewing, executing calculation...');
        const response = await fetch(`https://localhost/api/calculations/${calculation.type}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            calculation_type: calculation.type,
            parameters: calculation.parameters
          })
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
      console.error('🔍 [DEBUG] CalculationsPage.js: View calculation error:', error);
      setError('Ошибка загрузки результатов расчета');
    }
  };

  // Скачивание результата расчета
  const handleDownloadCalculation = async (calculation) => {
    if (!isAuthenticated || !authToken) {
      setError('Ошибка авторизации');
      return;
    }

    try {
      let calculationData = { ...calculation };
      
      // Если результат отсутствует, выполняем расчет через соответствующий API endpoint
      if (!calculation.result) {
        console.log('🔍 [DEBUG] CalculationsPage.js: No result found, executing calculation...');
        const response = await fetch(`https://localhost/api/calculations/${calculation.type}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            calculation_type: calculation.type,
            parameters: calculation.parameters
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        calculationData.result = result;
      }

      // Создаем JSON файл с результатами расчета
      const finalData = {
        name: calculationData.name,
        description: calculationData.description,
        type: calculationData.type,
        category: calculationData.category,
        status: calculationData.status,
        created_at: calculationData.created_at,
        parameters: calculationData.parameters,
        result: calculationData.result
      };

      const dataStr = JSON.stringify(finalData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${calculation.name.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date(calculation.created_at).toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setSuccess('Результат расчета скачан');
    } catch (error) {
      console.error('🔍 [DEBUG] CalculationsPage.js: Download error:', error);
      setError('Ошибка скачивания расчета');
    }
  };

  // Компонент модального окна просмотра расчета
  const ViewCalculationModal = () => {
    if (!viewingCalculation) return null;

    // Функция для получения русских названий и единиц измерения
    const getFieldInfo = (key, value) => {
      const fieldMap = {
        // Динамические расчеты
        'seismic_zone': { name: 'Сейсмический район', unit: 'баллов' },
        'soil_category': { name: 'Категория грунта', unit: '' },
        'base_seismic_coefficient': { name: 'Базовый коэффициент сейсмичности', unit: '' },
        'soil_coefficient': { name: 'Коэффициент грунта', unit: '' },
        'dynamic_coefficient': { name: 'Коэффициент динамичности', unit: '' },
        'seismic_coefficient': { name: 'Итоговый коэффициент сейсмичности', unit: '' },
        'seismic_load': { name: 'Сейсмическая нагрузка', unit: 'кН' },
        'structure_weight': { name: 'Масса конструкции', unit: 'т' },
        'natural_period': { name: 'Собственный период колебаний', unit: 'с' },
        'stability_check': { name: 'Проверка сейсмической устойчивости', unit: '' },
        
        // Расчеты на прочность
        'moment_of_inertia': { name: 'Момент инерции', unit: 'см⁴' },
        'max_moment': { name: 'Максимальный момент', unit: 'кН·м' },
        'max_stress': { name: 'Максимальное напряжение', unit: 'МПа' },
        'allowable_stress': { name: 'Допускаемое напряжение', unit: 'МПа' },
        'strength_check': { name: 'Проверка прочности', unit: '' },
        'deflection': { name: 'Прогиб', unit: 'м' },
        'deflection_limit': { name: 'Предельный прогиб', unit: 'м' },
        'deflection_check': { name: 'Проверка жесткости', unit: '' },
        'safety_factor_used': { name: 'Использованный коэффициент надежности', unit: '' },
        
        // Расчеты на устойчивость
        'element_length': { name: 'Длина элемента', unit: 'м' },
        'design_length': { name: 'Расчетная длина', unit: 'м' },
        'radius_of_gyration': { name: 'Радиус инерции', unit: 'см' },
        'slenderness': { name: 'Гибкость', unit: '' },
        'critical_force': { name: 'Критическая сила', unit: 'кН' },
        'end_conditions': { name: 'Тип закрепления', unit: '' },
        
        // Расчеты на жесткость
        'span_length': { name: 'Пролет', unit: 'м' },
        'distributed_load': { name: 'Распределенная нагрузка', unit: 'кН/м' },
        'elastic_modulus': { name: 'Модуль упругости', unit: 'МПа' },
        'rotation_angle': { name: 'Угол поворота', unit: 'рад' },
        
        // Расчеты на трещиностойкость
        'reinforcement_area': { name: 'Площадь арматуры', unit: 'мм²' },
        'concrete_class': { name: 'Класс бетона', unit: '' },
        'concrete_strength': { name: 'Прочность бетона', unit: 'МПа' },
        'concrete_elastic_modulus': { name: 'Модуль упругости бетона', unit: 'МПа' },
        'bending_moment': { name: 'Изгибающий момент', unit: 'кН·м' },
        'crack_width': { name: 'Ширина раскрытия трещин', unit: 'мм' },
        'crack_width_limit': { name: 'Предельная ширина трещин', unit: 'мм' },
        'cracking_check': { name: 'Проверка трещиностойкости', unit: '' },
        'reinforcement_ratio': { name: 'Коэффициент армирования', unit: '' },
        
        // Общие поля
        'execution_time': { name: 'Время выполнения', unit: 'с' },
        'calculation_type': { name: 'Тип расчета', unit: '' },
        'timestamp': { name: 'Время выполнения', unit: '' },
        'status': { name: 'Статус', unit: '' }
      };

      const fieldInfo = fieldMap[key] || { name: key.replace(/_/g, ' '), unit: '' };
      return fieldInfo;
    };

    // Функция для форматирования значения
    const formatValue = (value, unit) => {
      if (typeof value === 'boolean') {
        return value ? 'Да' : 'Нет';
      }
      if (typeof value === 'number') {
        const formatted = value.toFixed(2);
        return unit ? `${formatted} ${unit}` : formatted;
      }
      // Специальная обработка для категории грунта
      if (typeof value === 'string' && value.length === 1 && ['A', 'B', 'C', 'D'].includes(value)) {
        const soilCategories = {
          'A': 'A - Скальные грунты',
          'B': 'B - Плотные грунты', 
          'C': 'C - Средние грунты',
          'D': 'D - Слабые грунты'
        };
        return soilCategories[value] || value;
      }
      // Специальная обработка для типа закрепления
      if (typeof value === 'string' && ['pinned', 'fixed', 'cantilever'].includes(value)) {
        const endConditions = {
          'pinned': 'Шарнирное',
          'fixed': 'Жесткое',
          'cantilever': 'Консольное'
        };
        return endConditions[value] || value;
      }
      return value;
    };

    const renderCalculationResult = (result) => {
      if (!result) return <p className="text-gray-500">Результаты расчета недоступны</p>;

      return (
        <div className="space-y-4">
          {Object.entries(result).map(([key, value]) => {
            if (key === 'normative_links' || key === 'safety_recommendations') return null;
            if (typeof value === 'object' && value !== null) {
              return (
                <div key={key} className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">
                    {getFieldInfo(key, value).name.toUpperCase()}
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(value).map(([subKey, subValue]) => {
                      const subFieldInfo = getFieldInfo(subKey, subValue);
                      return (
                        <div key={subKey} className="flex justify-between">
                          <span className="text-gray-600">{subFieldInfo.name}:</span>
                          <span className="font-medium">
                            {formatValue(subValue, subFieldInfo.unit)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            }
            const fieldInfo = getFieldInfo(key, value);
            return (
              <div key={key} className="flex justify-between py-1 border-b border-gray-200">
                <span className="text-gray-600">{fieldInfo.name}:</span>
                <span className="font-medium">
                  {formatValue(value, fieldInfo.unit)}
                </span>
              </div>
            );
          })}
          
          {result.normative_links && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Нормативные документы</h4>
              <ul className="text-sm text-blue-800">
                {Object.entries(result.normative_links).map(([doc, description]) => (
                  <li key={doc} className="mb-1">
                    <strong>{doc}:</strong> {description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.safety_recommendations && (
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h4 className="font-medium text-yellow-900 mb-2">Рекомендации по безопасности</h4>
              <ul className="text-sm text-yellow-800">
                {result.safety_recommendations.map((rec, index) => (
                  <li key={index} className="mb-1">• {rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Просмотр расчета: {viewingCalculation.name}
            </h2>
            <button
              onClick={() => setShowViewCalculationModal(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="space-y-6">
            {/* Основная информация */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-3">Основная информация</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Тип расчета:</span>
                  <span className="ml-2 font-medium">
                    {calculationTypes.find(t => t.id === viewingCalculation.type)?.name || viewingCalculation.type}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Статус:</span>
                  <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                    viewingCalculation.status === 'completed' ? 'bg-green-100 text-green-800' :
                    viewingCalculation.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {viewingCalculation.status === 'completed' ? 'Завершен' :
                     viewingCalculation.status === 'processing' ? 'В обработке' : 'Ошибка'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Дата создания:</span>
                  <span className="ml-2 font-medium">
                    {new Date(viewingCalculation.created_at).toLocaleString('ru-RU')}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Описание:</span>
                  <span className="ml-2 font-medium">{viewingCalculation.description}</span>
                </div>
              </div>
            </div>

            {/* Параметры расчета */}
            {viewingCalculation.parameters && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-3">Параметры расчета</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(viewingCalculation.parameters).map(([key, value]) => {
                    const fieldInfo = getFieldInfo(key, value);
                    return (
                      <div key={key} className="flex justify-between">
                        <span className="text-blue-700">{fieldInfo.name}:</span>
                        <span className="font-medium text-blue-900">
                          {formatValue(value, fieldInfo.unit)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Результаты расчета */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Результаты расчета</h3>
              {renderCalculationResult(viewingCalculation.result)}
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-6 border-t mt-6">
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
    );
  };

  // Компонент модального окна создания расчета
  const NewCalculationModal = () => {
    const [formData, setFormData] = useState({
      name: '',
      description: '',
      parameters: {}
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      createCalculation({
        ...formData,
        type: selectedCalculation.type,
        category: selectedCalculation.category
      });
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Новый расчет: {selectedCalculation?.name}
            </h2>
            <button
              onClick={() => setShowNewCalculationModal(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Название расчета
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Описание
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Применяемые нормы
              </label>
              <div className="space-y-2">
                {selectedCalculation?.norms?.map((norm, index) => (
                  <div key={index} className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-600">{norm}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={() => setShowNewCalculationModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Создание...' : 'Создать расчет'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Проверка авторизации для отображения
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Для доступа к расчетам необходимо авторизоваться</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Calculator className="w-8 h-8 mr-3 text-blue-600" />
            {calculationType === 'all' ? 'Инженерные расчеты' : 
             calculationType === 'structural' ? 'Строительные конструкции' :
             calculationType === 'electrical' ? 'Электротехнические расчеты' :
             calculationType === 'mechanical' ? 'Механические расчеты' :
             calculationType === 'thermal' ? 'Тепловые расчеты' :
             calculationType === 'safety' ? 'Расчеты безопасности' :
             'Инженерные расчеты'}
          </h1>
          <p className="text-gray-600 mt-1">
            {calculationType === 'all' ? 'Расчеты в соответствии с нормами и методиками' :
             calculationType === 'structural' ? 'Расчеты прочности, устойчивости и деформаций строительных конструкций' :
             calculationType === 'electrical' ? 'Расчеты электрических цепей и систем' :
             calculationType === 'mechanical' ? 'Расчеты механических систем и деталей' :
             calculationType === 'thermal' ? 'Расчеты теплообмена и теплопередачи' :
             calculationType === 'safety' ? 'Расчеты надежности и безопасности' :
             'Расчеты в соответствии с нормами и методиками'}
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
              value={filterCategory}
              onChange={handleFilterChange}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.name}
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

      {/* Виды расчетов */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {calculationTypes
          .filter(type => calculationType === 'all' || type.id === calculationType)
          .map((type) => (
          <div
            key={type.id}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow border border-gray-200"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="text-3xl">{type.icon}</div>
              <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                {categories.find(c => c.id === type.category)?.name}
              </span>
            </div>
            
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {type.name}
            </h3>
            
            <p className="text-gray-600 text-sm mb-4">
              {type.description}
            </p>
            
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-700">Применяемые нормы:</p>
              {type.norms.slice(0, 2).map((norm, index) => (
                <p key={index} className="text-xs text-gray-500">• {norm}</p>
              ))}
              {type.norms.length > 2 && (
                <p className="text-xs text-gray-400">и еще {type.norms.length - 2}...</p>
              )}
            </div>
            
            <button 
              className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center"
              onClick={() => {
                if (type.id === 'structural') {
                  // Переход на страницу структурных расчетов
                  window.location.href = '/structural-calculations';
                } else if (type.id === 'foundation') {
                  // Переход на страницу расчетов оснований и фундаментов
                  window.location.href = '/foundation-calculations';
                } else if (type.id === 'degasification') {
                  // Переход на страницу дегазации
                  window.location.href = '/degasification-calculations';
                } else if (type.id === 'thermal') {
                  // Переход на страницу теплотехнических расчетов
                  window.location.href = '/thermal-calculations';
                } else if (type.id === 'ventilation') {
                  // Переход на страницу вентиляционных расчетов
                  window.location.href = '/ventilation-calculations';
                } else if (type.id === 'electrical') {
                  // Переход на страницу электротехнических расчетов
                  window.location.href = '/electrical-calculations';
                } else if (type.id === 'water') {
                  // Переход на страницу водоснабжения
                  window.location.href = '/water-supply-calculations';
                } else if (type.id === 'fire') {
                  // Переход на страницу пожарной безопасности
                  window.location.href = '/fire-safety-calculations';
                } else if (type.id === 'acoustic') {
                  // Переход на страницу акустических расчетов
                  window.location.href = '/acoustic-calculations';
                } else if (type.id === 'lighting') {
                  // Переход на страницу освещения
                  window.location.href = '/lighting-calculations';
                } else if (type.id === 'geotechnical') {
                  // Переход на страницу геологических расчетов
                  window.location.href = '/geological-calculations';
                } else if (type.id === 'uav_protection') {
                  // Переход на страницу защиты от БПЛА
                  window.location.href = '/uav-protection-calculations';
                } else {
                  handleNewCalculation(type.id);
                }
              }}
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
              {calculationType === 'all' ? 'Мои расчеты' :
               calculationType === 'structural' ? 'Мои расчеты строительных конструкций' :
               calculationType === 'electrical' ? 'Мои электротехнические расчеты' :
               calculationType === 'mechanical' ? 'Мои механические расчеты' :
               calculationType === 'thermal' ? 'Мои тепловые расчеты' :
               calculationType === 'safety' ? 'Мои расчеты безопасности' :
               'Мои расчеты'} ({filteredCalculations.length})
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
                    Тип
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
                      <span className="text-sm text-gray-900">
                        {calculationTypes.find(t => t.id === calculation.type)?.name || calculation.type}
                      </span>
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
                          onClick={() => handleViewCalculation(calculation)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Просмотреть расчет"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDownloadCalculation(calculation)}
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

      {/* Модальное окно создания расчета */}
      {showNewCalculationModal && selectedCalculation && <NewCalculationModal />}
      
      {/* Модальное окно просмотра расчета */}
      {showViewCalculationModal && viewingCalculation && <ViewCalculationModal />}
      
      {/* Структурные расчеты теперь на отдельной странице */}
    </div>
  );
};

export default CalculationsPage;
