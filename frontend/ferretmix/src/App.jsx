import { useState } from 'react';
import { testConnection } from './services/api';
import FileUpload from './components/FileUpload';
import GLMappingTool from './components/GLMappingTool';
import ProfitLossReport from './components/ProfitLossReport';
import BalanceSheetReport from './components/BalanceSheetReport';
import './App.css';
import DeleteTB from './components/DeleteTB';

function App() {
  const [currentView, setCurrentView] = useState('upload');
  const [apiStatus, setApiStatus] = useState('Not tested');

  const handleTestConnection = async () => {
    try {
      setApiStatus('Testing...');
      const result = await testConnection();
      setApiStatus(`✅ Success: ${result.status}`);
    } catch (error) {
      setApiStatus(`❌ Failed: ${error.message}`);
    }
  };

  const navButtonStyle = (isActive) => ({
    marginRight: '10px', 
    padding: '10px 15px',
    backgroundColor: isActive ? '#007bff' : '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer'
  });

  return (
    <div className="App">
      <header className="App-header">
        <h1>Financial Reporting System</h1>
        
        {/* Navigation */}
        <div style={{ margin: '20px 0' }}>
          <button 
            onClick={() => setCurrentView('upload')}
            style={navButtonStyle(currentView === 'upload')}
          >
            Upload TB
          </button>
          <button 
            onClick={() => setCurrentView('delete')}
            style={navButtonStyle(currentView === 'delete')}
          >
            Delete TB
          </button>
          <button 
            onClick={() => setCurrentView('mapping')}
            style={navButtonStyle(currentView === 'mapping')}
          >
            Setup Mappings
          </button>
          <button 
            onClick={() => setCurrentView('profit-loss')}
            style={navButtonStyle(currentView === 'profit-loss')}
          >
            P&L Report
          </button>
          <button 
            onClick={() => setCurrentView('balance-sheet')}
            style={navButtonStyle(currentView === 'balance-sheet')}
          >
            Balance Sheet
          </button>
          <button onClick={handleTestConnection} style={{ padding: '10px 15px' }}>
            Test API
          </button>
        </div>

        <p>API Status: {apiStatus}</p>

        {/* Content */}
        {currentView === 'upload' && <FileUpload />}
        {currentView === 'mapping' && <GLMappingTool />}
        {currentView === 'profit-loss' && <ProfitLossReport />}
        {currentView === 'balance-sheet' && <BalanceSheetReport />}
        {currentView === 'delete' && <DeleteTB />}
      </header>
    </div>
  );
}

export default App;