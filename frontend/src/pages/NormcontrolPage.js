import React from 'react';
import CheckableDocuments from '../components/CheckableDocuments';

const NormcontrolPage = ({
  isAuthenticated,
  authToken,
  refreshTrigger,
  onRefreshComplete
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
      {/* Page Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Нормоконтроль</h1>
              <p className="text-gray-600 mt-1">
                Проверка документов на соответствие нормативным требованиям с использованием AI
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <CheckableDocuments
            isAuthenticated={isAuthenticated}
            authToken={authToken}
            refreshTrigger={refreshTrigger}
            onRefreshComplete={onRefreshComplete}
          />
        </div>
      </div>
    </div>
  );
};

export default NormcontrolPage;
