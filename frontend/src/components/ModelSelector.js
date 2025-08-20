import React, { useState, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

const ModelSelector = ({ selectedModel, onModelChange, models = [] }) => {
  console.log('🔍 [DEBUG] ModelSelector.js: Component rendered with props:', {
    selectedModel,
    modelsCount: models.length
  });

  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Отладочные логи для отслеживания изменений состояния
  useEffect(() => {
    console.log('🔍 [DEBUG] ModelSelector.js: selectedModel changed to:', selectedModel);
  }, [selectedModel]);

  useEffect(() => {
    console.log('🔍 [DEBUG] ModelSelector.js: models changed:', models);
  }, [models]);

  const handleModelSelect = (model) => {
    console.log('🔍 [DEBUG] ModelSelector.js: handleModelSelect called with model:', model);
    onModelChange(model);
    setIsOpen(false);
  };

  const toggleDropdown = () => {
    console.log('🔍 [DEBUG] ModelSelector.js: toggleDropdown called, current state:', isOpen);
    setIsOpen(!isOpen);
  };

  console.log('🔍 [DEBUG] ModelSelector.js: Rendering with state:', {
    isOpen,
    isLoading,
    selectedModel,
    modelsCount: models.length
  });

  return (
    <div className="relative">
      <button
        onClick={toggleDropdown}
        className="flex items-center justify-between w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <span>{selectedModel || 'Выберите модель'}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
          <div className="py-1">
            {models.length === 0 ? (
              <div className="px-4 py-2 text-sm text-gray-500">
                {isLoading ? 'Загрузка моделей...' : 'Нет доступных моделей'}
              </div>
            ) : (
              models.map((model) => (
                <button
                  key={model.id}
                  onClick={() => handleModelSelect(model.id)}
                  className={`w-full flex items-center justify-between px-4 py-2 text-sm text-left hover:bg-gray-100 ${
                    selectedModel === model.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                  }`}
                >
                  <span>{model.id}</span>
                  {selectedModel === model.id && <Check className="w-4 h-4" />}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
