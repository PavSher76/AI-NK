import React from 'react';
import NormControl2PanelV2 from '../components/NormControl2PanelV2';

const NormControl2Page = ({
  isAuthenticated,
  authToken,
  refreshTrigger,
  onRefreshComplete
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <NormControl2PanelV2
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

export default NormControl2Page;
