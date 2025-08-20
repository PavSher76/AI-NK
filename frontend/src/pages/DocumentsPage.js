import React from 'react';
import NormativeDocuments from '../components/NormativeDocuments';

const DocumentsPage = ({
  isAuthenticated,
  authToken,
  refreshTrigger,
  onRefreshComplete
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100">
      {/* Page Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Нормативные документы</h1>
              <p className="text-gray-600 mt-1">
                Управление базой нормативных документов для системы нормоконтроля
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <NormativeDocuments
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

export default DocumentsPage;
