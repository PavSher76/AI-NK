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
      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
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
