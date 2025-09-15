import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Building2,
  MapPin,
  Calendar,
  Tag,
  Users,
  DollarSign,
  Ruler,
  PieChart,
  Activity,
  Download,
  RefreshCw,
  Filter,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

const AnalogObjectsAnalyticsPage = ({ isAuthenticated, authToken }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('year');
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [showFilters, setShowFilters] = useState(false);

  // Моковые данные для демонстрации
  const mockAnalyticsData = {
    summary: {
      totalObjects: 1247,
      newThisMonth: 23,
      avgPrice: 95000,
      avgArea: 28500,
      topRegion: 'Московская область',
      growthRate: 12.5
    },
    byType: [
      { type: 'Жилой', count: 856, percentage: 68.6, avgPrice: 85000 },
      { type: 'Коммерческий', count: 234, percentage: 18.8, avgPrice: 120000 },
      { type: 'Промышленный', count: 98, percentage: 7.9, avgPrice: 65000 },
      { type: 'Социальный', count: 59, percentage: 4.7, avgPrice: 78000 }
    ],
    byRegion: [
      { region: 'Московская область', count: 456, avgPrice: 98000 },
      { region: 'Москва', count: 234, avgPrice: 125000 },
      { region: 'Санкт-Петербург', count: 189, avgPrice: 89000 },
      { region: 'Ленинградская область', count: 123, avgPrice: 72000 },
      { region: 'Краснодарский край', count: 98, avgPrice: 68000 },
      { region: 'Свердловская область', count: 87, avgPrice: 55000 },
      { region: 'Другие', count: 60, avgPrice: 45000 }
    ],
    byYear: [
      { year: 2024, count: 45, avgPrice: 102000, avgArea: 31000 },
      { year: 2023, count: 234, avgPrice: 95000, avgArea: 28500 },
      { year: 2022, count: 345, avgPrice: 88000, avgArea: 27000 },
      { year: 2021, count: 298, avgPrice: 82000, avgArea: 26000 },
      { year: 2020, count: 325, avgPrice: 78000, avgArea: 25000 }
    ],
    priceTrends: [
      { month: 'Янв', price: 85000 },
      { month: 'Фев', price: 87000 },
      { month: 'Мар', price: 89000 },
      { month: 'Апр', price: 92000 },
      { month: 'Май', price: 95000 },
      { month: 'Июн', price: 98000 },
      { month: 'Июл', price: 96000 },
      { month: 'Авг', price: 94000 },
      { month: 'Сен', price: 97000 },
      { month: 'Окт', price: 99000 },
      { month: 'Ноя', price: 101000 },
      { month: 'Дек', price: 102000 }
    ],
    topDevelopers: [
      { name: 'ООО "Северстрой"', objects: 45, avgPrice: 95000, rating: 4.8 },
      { name: 'ООО "Деловые центры"', objects: 38, avgPrice: 120000, rating: 4.6 },
      { name: 'ООО "Солнечный дом"', objects: 32, avgPrice: 78000, rating: 4.7 },
      { name: 'ООО "Стройинвест"', objects: 28, avgPrice: 85000, rating: 4.5 },
      { name: 'ООО "Мегастрой"', objects: 25, avgPrice: 92000, rating: 4.4 }
    ]
  };

  // Загрузка аналитических данных
  const loadAnalyticsData = async () => {
    setIsLoading(true);
    try {
      // Имитация API запроса
      await new Promise(resolve => setTimeout(resolve, 1000));
      setAnalyticsData(mockAnalyticsData);
    } catch (error) {
      console.error('Ошибка загрузки аналитики:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod, selectedRegion]);

  // Экспорт данных
  const handleExport = (format) => {
    const data = analyticsData;
    let content, filename, mimeType;

    if (format === 'csv') {
      content = [
        ['Показатель', 'Значение'],
        ['Всего объектов', data.summary.totalObjects],
        ['Новых в этом месяце', data.summary.newThisMonth],
        ['Средняя цена за м²', data.summary.avgPrice],
        ['Средняя площадь', data.summary.avgArea],
        ['Топ регион', data.summary.topRegion],
        ['Рост (%)', data.summary.growthRate]
      ].map(row => row.join(',')).join('\n');
      filename = 'analytics_summary.csv';
      mimeType = 'text/csv';
    } else {
      content = JSON.stringify(data, null, 2);
      filename = 'analytics_data.json';
      mimeType = 'application/json';
    }

    const blob = new Blob([content], { type: mimeType });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  };

  const StatCard = ({ title, value, change, icon: Icon, color = 'blue' }) => (
    <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <div className={`flex items-center mt-2 text-sm ${
              change > 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {change > 0 ? (
                <TrendingUp className="w-4 h-4 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 mr-1" />
              )}
              {Math.abs(change)}% за период
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-${color}-100`}>
          <Icon className={`w-6 h-6 text-${color}-600`} />
        </div>
      </div>
    </div>
  );

  const BarChart = ({ data, title, xKey, yKey, color = 'blue' }) => (
    <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="text-sm text-gray-600 w-24 truncate">{item[xKey]}</span>
            <div className="flex-1 mx-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`bg-${color}-500 h-2 rounded-full transition-all duration-300`}
                  style={{ width: `${(item[yKey] / Math.max(...data.map(d => d[yKey]))) * 100}%` }}
                />
              </div>
            </div>
            <span className="text-sm font-medium text-gray-900 w-16 text-right">
              {item[yKey].toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );

  const PieChart = ({ data, title }) => (
    <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex items-center">
              <div 
                className="w-4 h-4 rounded-full mr-3"
                style={{ backgroundColor: `hsl(${index * 60}, 70%, 50%)` }}
              />
              <span className="text-sm text-gray-600">{item.type}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-900">{item.count}</span>
              <span className="text-sm text-gray-500">({item.percentage}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Данные недоступны</h3>
        <p className="text-gray-500">Не удалось загрузить аналитические данные</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок и фильтры */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Аналитика объектов аналогов</h1>
          <p className="text-gray-600 mt-1">Статистика и тренды по базе объектов аналогов</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Filter className="w-4 h-4 mr-2" />
            Фильтры
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Download className="w-4 h-4 mr-2" />
            Экспорт CSV
          </button>
          <button
            onClick={loadAnalyticsData}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Обновить
          </button>
        </div>
      </div>

      {/* Фильтры */}
      {showFilters && (
        <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Период</label>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="month">Месяц</option>
                <option value="quarter">Квартал</option>
                <option value="year">Год</option>
                <option value="all">Все время</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Регион</label>
              <select
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="all">Все регионы</option>
                <option value="moscow">Москва</option>
                <option value="moscow_region">Московская область</option>
                <option value="spb">Санкт-Петербург</option>
                <option value="spb_region">Ленинградская область</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Тип объекта</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                <option value="all">Все типы</option>
                <option value="residential">Жилой</option>
                <option value="commercial">Коммерческий</option>
                <option value="industrial">Промышленный</option>
                <option value="social">Социальный</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Основная статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Всего объектов"
          value={analyticsData.summary.totalObjects.toLocaleString()}
          change={analyticsData.summary.growthRate}
          icon={Building2}
          color="blue"
        />
        <StatCard
          title="Новых в этом месяце"
          value={analyticsData.summary.newThisMonth}
          icon={Activity}
          color="green"
        />
        <StatCard
          title="Средняя цена за м²"
          value={`${analyticsData.summary.avgPrice.toLocaleString()} ₽`}
          icon={DollarSign}
          color="yellow"
        />
        <StatCard
          title="Средняя площадь"
          value={`${analyticsData.summary.avgArea.toLocaleString()} м²`}
          icon={Ruler}
          color="purple"
        />
      </div>

      {/* Графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChart
          data={analyticsData.byRegion}
          title="Объекты по регионам"
          xKey="region"
          yKey="count"
          color="blue"
        />
        <PieChart
          data={analyticsData.byType}
          title="Распределение по типам"
        />
      </div>

      {/* Тренды цен */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Динамика цен за м²</h3>
        <div className="space-y-3">
          {analyticsData.priceTrends.map((item, index) => (
            <div key={index} className="flex items-center justify-between">
              <span className="text-sm text-gray-600 w-12">{item.month}</span>
              <div className="flex-1 mx-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(item.price / Math.max(...analyticsData.priceTrends.map(d => d.price))) * 100}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-medium text-gray-900 w-20 text-right">
                {item.price.toLocaleString()} ₽
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Топ застройщики */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Топ застройщики</h3>
        <div className="space-y-4">
          {analyticsData.topDevelopers.map((developer, index) => (
            <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-bold text-primary-600">{index + 1}</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">{developer.name}</p>
                  <p className="text-sm text-gray-500">
                    {developer.objects} объектов • Рейтинг: {developer.rating}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-medium text-gray-900">
                  {developer.avgPrice.toLocaleString()} ₽/м²
                </p>
                <p className="text-sm text-gray-500">средняя цена</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Статистика по годам */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Статистика по годам</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-700">Год</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Количество</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Средняя цена (₽/м²)</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Средняя площадь (м²)</th>
              </tr>
            </thead>
            <tbody>
              {analyticsData.byYear.map((year, index) => (
                <tr key={index} className="border-b border-gray-100">
                  <td className="py-3 px-4 font-medium text-gray-900">{year.year}</td>
                  <td className="py-3 px-4">{year.count}</td>
                  <td className="py-3 px-4">{year.avgPrice.toLocaleString()}</td>
                  <td className="py-3 px-4">{year.avgArea.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalogObjectsAnalyticsPage;
