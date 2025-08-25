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
      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
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
