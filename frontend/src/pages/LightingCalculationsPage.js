import React, { useState, useEffect } from 'react';
import './CalculationsPage.css';

const LightingCalculationsPage = ({ isAuthenticated, authToken }) => {
  const [calculations, setCalculations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [calculationTypes, setCalculationTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [parameters, setParameters] = useState({});
  const [results, setResults] = useState(null);

  useEffect(() => {
    if (isAuthenticated) {
      loadCalculationTypes();
    }
  }, [isAuthenticated]);

  const loadCalculationTypes = async () => {
    try {
      setLoading(true);
      const response = await fetch('https://localhost/api/calculations/lighting/types', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setCalculationTypes(data);
    } catch (err) {
      console.error('Error loading calculation types:', err);
      setError('Ошибка загрузки типов расчетов');
    } finally {
      setLoading(false);
    }
  };

  const handleParameterChange = (param, value) => {
    setParameters(prev => ({
      ...prev,
      [param]: value
    }));
  };

  const executeCalculation = async () => {
    if (!selectedType) {
      setError('Выберите тип расчета');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('https://localhost/api/calculations/lighting/execute', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          calculation_type: selectedType,
          parameters: parameters
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
      setShowModal(false);
    } catch (err) {
      console.error('Error executing calculation:', err);
      setError('Ошибка выполнения расчета');
    } finally {
      setLoading(false);
    }
  };

  const getParameterInput = (param, schema) => {
    const value = parameters[param] || schema.default || '';

    switch (schema.type) {
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleParameterChange(param, parseFloat(e.target.value) || 0)}
            className="parameter-input"
            step="0.01"
          />
        );
      case 'integer':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleParameterChange(param, parseInt(e.target.value) || 0)}
            className="parameter-input"
          />
        );
      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={value}
            onChange={(e) => handleParameterChange(param, e.target.checked)}
            className="parameter-checkbox"
          />
        );
      case 'string':
        if (schema.enum) {
          return (
            <select
              value={value}
              onChange={(e) => handleParameterChange(param, e.target.value)}
              className="parameter-select"
            >
              <option value="">Выберите значение</option>
              {schema.enum.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          );
        }
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParameterChange(param, e.target.value)}
            className="parameter-input"
          />
        );
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParameterChange(param, e.target.value)}
            className="parameter-input"
          />
        );
    }
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
        <h1>Освещение и инсоляция</h1>
        <p>Расчеты освещения и инсоляции согласно СП 52.13330.2016</p>
      </div>

      <div className="calculations-content">
        <div className="calculations-grid">
          {calculationTypes.map((type) => (
            <div key={type.type} className="calculation-card">
              <div className="calculation-header">
                <h3>{type.name}</h3>
                <p>{type.description}</p>
              </div>
              
              <div className="calculation-categories">
                <h4>Категории:</h4>
                <div className="category-tags">
                  {type.categories?.map((category) => (
                    <span key={category} className="category-tag">
                      {category.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>

              <div className="calculation-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setSelectedType(type.type);
                    setParameters({});
                    setShowModal(true);
                  }}
                >
                  Выполнить расчет
                </button>
              </div>
            </div>
          ))}
        </div>

        {results && renderResults()}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Параметры расчета</h3>
              <button
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="parameters-form">
                {selectedType && calculationTypes.find(t => t.type === selectedType)?.parameters_schema?.properties && 
                  Object.entries(calculationTypes.find(t => t.type === selectedType).parameters_schema.properties).map(([param, schema]) => (
                    <div key={param} className="parameter-group">
                      <label className="parameter-label">
                        {schema.title}
                        {calculationTypes.find(t => t.type === selectedType).parameters_schema.required?.includes(param) && (
                          <span className="required">*</span>
                        )}
                      </label>
                      {getParameterInput(param, schema)}
                    </div>
                  ))
                }
              </div>
            </div>
            
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowModal(false)}
              >
                Отмена
              </button>
              <button
                className="btn btn-primary"
                onClick={executeCalculation}
                disabled={loading}
              >
                {loading ? 'Выполняется...' : 'Выполнить расчет'}
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  );
};

export default LightingCalculationsPage;
