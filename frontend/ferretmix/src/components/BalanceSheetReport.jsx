import { useState, useEffect } from 'react';

const BalanceSheetReport = () => {
  const [availablePeriods, setAvailablePeriods] = useState([]);
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedCompany, setSelectedCompany] = useState('');


  useEffect(() => {
    fetchAvailableCompanies();
  }, []);

  useEffect(() => {
  if (selectedCompany) {
    fetchAvailablePeriods();
  } else {
    setAvailablePeriods([]); // Clear periods if no company
    setSelectedPeriod(''); // Reset selected period
  }
}, [selectedCompany]); // ← This is the key part!
  

  const fetchAvailablePeriods = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/reports/available-periods?company=${selectedCompany}`);
      const data = await response.json();
      setAvailablePeriods(data.periods || []);
    } catch (error) {
      setError('Failed to fetch available periods');
    }
  };

  const fetchAvailableCompanies = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/reports/available-companies');
      const data = await response.json();
      setAvailableCompanies(data.companies);
    } catch (error) {
      setError('Failed to fetch available companies');
    }
  };


  const generateReport = async () => {
    console.log("🔍 generateReport called with period:", selectedPeriod);
    
    if (!selectedPeriod) {
      setError('Please select a period');
      return;
    }

    setLoading(true);
    setError('');

    try {
      console.log("🔍 About to make API call...");
      const response = await fetch(`http://localhost:5000/api/reports/balance-sheet?period_end_date=${selectedPeriod}`);
      console.log("🔍 API response:", response.status, response.ok);
      
      const data = await response.json();
      console.log("🔍 API data:", data);
      
      if (response.ok) {
        setReportData(data);
      } else {
        setError(data.error || 'Failed to generate report');
      }
    } catch (error) {
      console.log("🔍 API error:", error);
      setError('Failed to generate report: ' + error.message);
    } finally {
      setLoading(false);
    }
};

  const formatAmount = (amount) => {
    if (amount === null || amount === undefined) return '';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getRowStyle = (item) => {
    const baseStyle = {
      borderBottom: '1px solid #eee',
      padding: '8px 0'
    };

    if (item.type === 'section_header') {
      return {
        ...baseStyle,
        backgroundColor: '#f8f9fa',
        fontWeight: 'bold',
        fontSize: '16px',
        borderTop: '2px solid #333',
        padding: '12px 0'
      };
    }

    if (item.type === 'section_total') {
      return {
        ...baseStyle,
        fontWeight: 'bold',
        borderTop: '1px solid #333',
        backgroundColor: '#f5f5f5'
      };
    }

    return baseStyle;
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      
      <h2>Balance Sheet</h2>
      <div style={{ marginBottom: '30px', display: 'flex', gap: '20px', alignItems: 'end' }}>
      <div>
          <label>Which Company do you want?</label>
          <select
            value={selectedCompany}
            style={{ marginLeft: '10px', padding: '8px', minWidth: '200px' }}            
            onChange={(e) => setSelectedCompany(e.target.value)}
          >
            <option value="">Choose Company...</option>
            {availableCompanies.map((company, index) => (
              <option key={index} value={company}>
                {company}
              </option>
            ))}
          </select>
        </div>
       
      
      {/* Period Selection */}
      
      
      
        {selectedCompany && (
        <div>
          <label>Select Period:</label>
          <select 
            value={selectedPeriod} 
            onChange={(e) => setSelectedPeriod(e.target.value)}
            style={{ marginLeft: '10px', padding: '8px', minWidth: '200px' }}
          >
            <option value="">Choose Period...</option>
            {availablePeriods.map(period => (
              <option key={period} value={period}>
                {new Date(period).toLocaleDateString('en-US', { 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </option>
            ))}
          </select>
        </div>)
        }
         </div>

         
        
        <button 
          onClick={generateReport}
          disabled={!selectedPeriod || loading}
          style={{
            padding: '8px 20px',
            backgroundColor: selectedPeriod && !loading ? '#007bff' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: selectedPeriod && !loading ? 'pointer' : 'not-allowed'
          }}
        >
          {loading ? 'Generating...' : 'Generate Report'}
        </button>
      

      {/* Error Display */}
      {error && (
        <div style={{ 
          color: 'red', 
          backgroundColor: '#f8d7da', 
          padding: '10px', 
          borderRadius: '4px', 
          marginBottom: '20px' 
        }}>
          {error}
        </div>
      )}

      {/* Balance Check */}
      {reportData && (
        <div style={{ 
          marginBottom: '20px', 
          padding: '10px', 
          borderRadius: '4px',
          backgroundColor: reportData.balances ? '#d4edda' : '#f8d7da',
          color: reportData.balances ? '#155724' : '#721c24'
        }}>
          {reportData.balances ? 
            '✓ Balance Sheet is in balance' : 
            `⚠ Balance Sheet is out of balance by ${formatAmount(reportData.difference)}`
          }
        </div>
      )}

      {/* Report Display */}
      {reportData && (
        <div>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <h3>{reportData.report_title}</h3>
            <p>As at {new Date(reportData.period_end_date).toLocaleDateString()}</p>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {(reportData.data && Array.isArray(reportData.data) ? reportData.data : []).map((item, index) =>(
                <tr key={index} style={getRowStyle(item)}>
                  <td style={{ 
                    textAlign: 'left',
                    paddingLeft: `${item.indent_level * 20}px`,
                    width: '70%'
                  }}>
                    {item.name}
                  </td>
                  <td style={{ 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    width: '30%'
                  }}>
                    {formatAmount(item.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default BalanceSheetReport;