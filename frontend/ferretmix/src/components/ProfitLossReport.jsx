import { useState, useEffect } from 'react';

const ProfitLossReport = () => {
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
  if (!selectedPeriod) {
    setError('Please select a period');
    return;
  }

  setLoading(true);
  setError('');

  try {
    const response = await fetch(`http://localhost:5000/api/reports/profit-loss?period_end_date=${selectedPeriod}`);
    const data = await response.json();
    
    // ADD THIS DEBUGGING
    console.log('=== BACKEND RESPONSE DEBUG ===');
    console.log('Response status:', response.status);
    console.log('Full data:', data);
    console.log('Has data property:', 'data' in data);
    console.log('Has summary property:', 'summary' in data);
    console.log('Has error property:', 'error' in data);
    if (data.error) {
      console.log('Backend error message:', data.error);
    }
    console.log('===============================');
    
    if (response.ok) {
      setReportData(data);
    } else {
      setError(data.error || 'Failed to generate report');
    }
  } catch (error) {
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

    if (item.type === 'section_total' || item.type === 'calculated_total') {
      return {
        ...baseStyle,
        fontWeight: 'bold',
        borderTop: '1px solid #333',
        backgroundColor: '#f5f5f5'
      };
    }

    if (item.type === 'final_total') {
      return {
        ...baseStyle,
        fontWeight: 'bold',
        fontSize: '18px',
        borderTop: '3px double #333',
        borderBottom: '3px double #333',
        backgroundColor: '#e9ecef',
        padding: '12px 0'
      };
    }

    return baseStyle;
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Profit & Loss Statement</h2>
      
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

      {/* Report Display */}
      {reportData && (
        <div>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <h3>{reportData.report_title}</h3>
            <p>For the period ending {new Date(reportData.period_end_date).toLocaleDateString()}</p>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {(reportData.data && Array.isArray(reportData.data) ? reportData.data : []).map((item, index) => (
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

          {/* Summary Box */}
          <div style={{ 
            marginTop: '30px', 
            padding: '20px', 
            backgroundColor: '#f8f9fa', 
            borderRadius: '8px' 
          }}>
            <h4>Key Metrics</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>Revenue: {formatAmount(reportData.summary.total_revenue)}</div>
              <div>Gross Profit: {formatAmount(reportData.summary.gross_profit)}</div>
              <div>EBITDA: {formatAmount(reportData.summary.ebitda)}</div>
              <div style={{ fontWeight: 'bold' }}>
                Net Profit: {formatAmount(reportData.summary.net_profit)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfitLossReport;