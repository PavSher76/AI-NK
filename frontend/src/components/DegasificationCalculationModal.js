import React, { useState } from 'react';
import { 
  X, 
  Calculator, 
  Wind, 
  Gauge, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  Info,
  Save,
  Play
} from 'lucide-react';

const DegasificationCalculationModal = ({ 
  calculationTypes, 
  onClose, 
  onExecute, 
  onSave 
}) => {
  const [formData, setFormData] = useState({
    name: '',
    mine_depth: '',
    mine_area: '',
    coal_seam_thickness: '',
    methane_content: '',
    extraction_rate: '',
    methane_emission_rate: '',
    ventilation_air_flow: '',
    methane_concentration_limit: 1.0,
    safety_factor: 2.0,
    normative_document: 'ГОСТ Р 55154-2012',
    safety_requirements: 'ПБ 05-618-03'
  });
  
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); // 1: параметры, 2: результаты, 3: сохранение

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleExecute = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const parameters = {
        mine_depth: parseFloat(formData.mine_depth),
        mine_area: parseFloat(formData.mine_area),
        coal_seam_thickness: parseFloat(formData.coal_seam_thickness),
        methane_content: parseFloat(formData.methane_content),
        extraction_rate: parseFloat(formData.extraction_rate),
        methane_emission_rate: parseFloat(formData.methane_emission_rate),
        ventilation_air_flow: parseFloat(formData.ventilation_air_flow),
        methane_concentration_limit: parseFloat(formData.methane_concentration_limit),
        safety_factor: parseFloat(formData.safety_factor),
        normative_document: formData.normative_document,
        safety_requirements: formData.safety_requirements
      };

      const result = await onExecute({
        calculation_type: 'degasification',
        parameters
      });

      setResults(result);
      setStep(2);
    } catch (error) {
      setError('Ошибка выполнения расчета: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      
      await onSave({
        name: formData.name || 'Расчет дегазации',
        type: 'degasification',
        category: 'methane_extraction',
        parameters: formData,
        results: results
      });
      
      setStep(3);
    } catch (error) {
      setError('Ошибка сохранения расчета: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

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
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 xl:w-1/2 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Заголовок */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Wind className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  Расчет дегазации угольных шахт
                </h3>
                <p className="text-sm text-gray-500">
                  Расчет систем дегазации, вентиляции и безопасности
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Прогресс */}
          <div className="mb-6">
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                  1
                </div>
                <span className="text-sm font-medium">Параметры</span>
              </div>
              <div className={`flex-1 h-0.5 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
              <div className={`flex items-center space-x-2 ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                  2
                </div>
                <span className="text-sm font-medium">Результаты</span>
              </div>
              <div className={`flex-1 h-0.5 ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
              <div className={`flex items-center space-x-2 ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                  3
                </div>
                <span className="text-sm font-medium">Сохранение</span>
              </div>
            </div>
          </div>

          {/* Ошибки */}
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Ошибка</h3>
                  <div className="mt-2 text-sm text-red-700">{error}</div>
                </div>
              </div>
            </div>
          )}

          {/* Шаг 1: Параметры */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Название расчета
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Введите название расчета"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Глубина шахты (м) *
                  </label>
                  <input
                    type="number"
                    name="mine_depth"
                    value={formData.mine_depth}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Площадь шахты (м²) *
                  </label>
                  <input
                    type="number"
                    name="mine_area"
                    value={formData.mine_area}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="10000"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Мощность угольного пласта (м) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="coal_seam_thickness"
                    value={formData.coal_seam_thickness}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="2.5"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Содержание метана в угле (%) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="methane_content"
                    value={formData.methane_content}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="15"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Скорость отработки (м/сут) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="extraction_rate"
                    value={formData.extraction_rate}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="5"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Интенсивность выделения метана (м³/т) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="methane_emission_rate"
                    value={formData.methane_emission_rate}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="25"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Расход вентиляционного воздуха (м³/с) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="ventilation_air_flow"
                    value={formData.ventilation_air_flow}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="50"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Предельная концентрация метана (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="methane_concentration_limit"
                    value={formData.methane_concentration_limit}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="1.0"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Коэффициент безопасности
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="safety_factor"
                    value={formData.safety_factor}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="2.0"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Нормативный документ
                  </label>
                  <input
                    type="text"
                    name="normative_document"
                    value={formData.normative_document}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="ГОСТ Р 55154-2012"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Правила безопасности
                  </label>
                  <input
                    type="text"
                    name="safety_requirements"
                    value={formData.safety_requirements}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="ПБ 05-618-03"
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Отмена
                </button>
                <button
                  onClick={handleExecute}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <Play className="w-4 h-4 mr-2" />
                  )}
                  Выполнить расчет
                </button>
              </div>
            </div>
          )}

          {/* Шаг 2: Результаты */}
          {step === 2 && results && (
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-green-800">Расчет выполнен успешно</h3>
                    <div className="mt-2 text-sm text-green-700">
                      Время выполнения: {results.execution_time?.toFixed(4)} сек
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="text-lg font-medium text-gray-900">Основные параметры</h4>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Wind className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Объем угля</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {results.coal_volume?.toFixed(2)} м³
                    </p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Gauge className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-gray-700">Масса угля</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {results.coal_mass?.toFixed(2)} т
                    </p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Shield className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-medium text-gray-700">Содержание метана</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {results.total_methane_content?.toFixed(2)} м³
                    </p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Wind className="w-4 h-4 text-orange-600" />
                      <span className="text-sm font-medium text-gray-700">Выделение метана</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {results.daily_methane_emission?.toFixed(2)} м³/сут
                    </p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="text-lg font-medium text-gray-900">Вентиляция и безопасность</h4>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Gauge className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Требуемый расход воздуха</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {results.required_air_flow?.toFixed(2)} м³/с
                    </p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Wind className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-gray-700">Достаточность вентиляции</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {(results.ventilation_sufficiency * 100)?.toFixed(2)}%
                    </p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Gauge className="w-4 h-4 text-red-600" />
                      <span className="text-sm font-medium text-gray-700">Концентрация метана</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {(results.methane_concentration * 100)?.toFixed(4)}%
                    </p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Shield className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-medium text-gray-700">Эффективность дегазации</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {results.degasification_efficiency?.toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Shield className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium text-gray-700">Статус безопасности</span>
                </div>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getSafetyColor(results.safety_status)}`}>
                  {results.safety_status}
                </span>
              </div>
              
              {results.safety_recommendations && results.safety_recommendations.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start space-x-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-yellow-800 mb-2">Рекомендации по безопасности</h4>
                      <ul className="space-y-1">
                        {results.safety_recommendations.map((recommendation, index) => (
                          <li key={index} className="text-sm text-yellow-700">
                            • {recommendation}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setStep(1)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Назад
                </button>
                <button
                  onClick={handleSave}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  Сохранить расчет
                </button>
              </div>
            </div>
          )}

          {/* Шаг 3: Сохранение */}
          {step === 3 && (
            <div className="text-center space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-md p-6">
                <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-green-800 mb-2">
                  Расчет сохранен успешно
                </h3>
                <p className="text-sm text-green-700">
                  Расчет дегазации сохранен и доступен в списке расчетов
                </p>
              </div>
              
              <div className="flex justify-center space-x-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Закрыть
                </button>
                <button
                  onClick={() => {
                    setStep(1);
                    setResults(null);
                    setFormData({
                      name: '',
                      mine_depth: '',
                      mine_area: '',
                      coal_seam_thickness: '',
                      methane_content: '',
                      extraction_rate: '',
                      methane_emission_rate: '',
                      ventilation_air_flow: '',
                      methane_concentration_limit: 1.0,
                      safety_factor: 2.0,
                      normative_document: 'ГОСТ Р 55154-2012',
                      safety_requirements: 'ПБ 05-618-03'
                    });
                  }}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Calculator className="w-4 h-4 mr-2" />
                  Новый расчет
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DegasificationCalculationModal;
