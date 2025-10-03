import { useState, useEffect } from 'react';

const BalanceSheetReport = () => {
  const [availablePeriods, setAvailablePeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAvailablePeriods();
  }, []);

  const fetchAvailablePeriods = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/reports/available-periods');
      const data = await response.json();
      setAvailablePeriods(data.periods || []);
    } catch (error) {
      setError('Failed to fetch available periods');
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
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Balance Sheet</h2>
      
      {/* Period Selection */}
      <div style={{ marginBottom: '30px', display: 'flex', gap: '20px', alignItems: 'end' }}>
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
      </div>

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