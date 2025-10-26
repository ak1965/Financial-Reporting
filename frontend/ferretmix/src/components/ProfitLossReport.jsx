import { useState, useEffect } from 'react';

const ProfitLossReport = () => {
  const [availablePeriods, setAvailablePeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedCompany, setSelectedCompany] = useState('');
  const [availableCompanies, setAvailableCompanies] = useState([]);

  useEffect(() => {
    fetchAvailableCompanies();
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      fetchAvailablePeriods();
    }
  }, [selectedCompany]);

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
    if (!selectedPeriod) {
      setError('Please select a period');
      return;
    }

    if (!selectedCompany) {
      setError('Please select a company');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`http://localhost:5000/api/reports/profit-loss?period_end_date=${selectedPeriod}&company=${selectedCompany}`);
      const data = await response.json();
      
      console.log('=== BACKEND RESPONSE DEBUG ===');
      console.log('Response status:', response.status);
      console.log('Full data:', data);
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
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h2>Profit & Loss Statement</h2>
      
      {/* Company and Period Selection */}
      <div style={{ marginBottom: '30px', display: 'flex', gap: '20px', alignItems: 'end' }}>
        <div>
          <label>Select Company: </label>
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
          </div>
        )}
      </div>

      <button 
        onClick={generateReport}
        disabled={!selectedPeriod || !selectedCompany || loading}
        style={{
          padding: '8px 20px',
          backgroundColor: selectedPeriod && selectedCompany && !loading ? '#007bff' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: selectedPeriod && selectedCompany && !loading ? 'pointer' : 'not-allowed',
          marginBottom: '20px'
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

      {/* Report Display */}
      {reportData && (
        <div>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <h3>{reportData.report_title}</h3>
            <p>For the period ending {new Date(reportData.period_end_date).toLocaleDateString()}</p>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #333', backgroundColor: '#f8f9fa' }}>
                <th style={{ textAlign: 'left', padding: '10px', width: '25%' }}>Account</th>
                <th style={{ textAlign: 'right', padding: '10px', width: '12.5%' }}>Actual</th>
                <th style={{ textAlign: 'right', padding: '10px', width: '12.5%' }}>Budget</th>
                <th style={{ textAlign: 'right', padding: '10px', width: '12.5%' }}>Prior Year</th>
                <th style={{ textAlign: 'right', padding: '10px', width: '12.5%' }}>Actual YTD</th>
                <th style={{ textAlign: 'right', padding: '10px', width: '12.5%' }}>Budget YTD</th>
                <th style={{ textAlign: 'right', padding: '10px', width: '12.5%' }}>Prior Yr YTD</th>
              </tr>
            </thead>
            <tbody>
              {(reportData.data && Array.isArray(reportData.data) ? reportData.data : []).map((item, index) => (
                <tr key={index} style={getRowStyle(item)}>
                  <td style={{ 
                    textAlign: 'left',
                    paddingLeft: `${item.indent_level * 20}px`,
                    padding: '8px'
                  }}>
                    {item.name}
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace', padding: '8px' }}>
                    {formatAmount(item.amounts?.actual || item.amount)}
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace', padding: '8px' }}>
                    {formatAmount(item.amounts?.budget)}
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace', padding: '8px' }}>
                    {formatAmount(item.amounts?.prior_year)}
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace', padding: '8px' }}>
                    {formatAmount(item.amounts?.actual_ytd)}
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace', padding: '8px' }}>
                    {formatAmount(item.amounts?.budget_ytd)}
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace', padding: '8px' }}>
                    {formatAmount(item.amounts?.prior_year_ytd)}
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
            <table style={{ width: '100%', fontSize: '14px' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '5px' }}>Metric</th>
                  <th style={{ textAlign: 'right', padding: '5px' }}>Actual</th>
                  <th style={{ textAlign: 'right', padding: '5px' }}>Budget</th>
                  <th style={{ textAlign: 'right', padding: '5px' }}>Prior Year</th>
                  <th style={{ textAlign: 'right', padding: '5px' }}>Actual YTD</th>
                  <th style={{ textAlign: 'right', padding: '5px' }}>Budget YTD</th>
                  <th style={{ textAlign: 'right', padding: '5px' }}>Prior Yr YTD</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ padding: '5px' }}>Revenue</td>
                  <td style={{ textAlign: 'right', padding: '5px' }}>{formatAmount(reportData.summary?.total_revenue?.actual)}</td>
                  <td style={{ textAlign: 'right', padding: '5px' }}>{formatAmount(reportData.summary?.total_revenue?.budget)}</td>
                  <td style={{ textAlign: 'right', padding: '5px' }}>{formatAmount(reportData.summary?.total_revenue?.prior_year)}</td>
                  <td style={{ textAlign: 'right', padding: '5px' }}>{formatAmount(reportData.summary?.total_revenue?.actual_ytd)}</td>
                  <td style={{ textAlign: 'right', padding: '5px' }}>{formatAmount(reportData.summary?.total_revenue?.budget_ytd)}</td>
                  <td style={{ textAlign: 'right', padding: '5px' }}>{formatAmount(reportData.summary?.total_revenue?.prior_year_ytd)}</td>
                </tr>
                <tr>
                  <td style={{ padding: '5px', fontWeight: 'bold' }}>Net Profit</td>
                  <td style={{ textAlign: 'right', padding: '5px', fontWeight: 'bold' }}>{formatAmount(reportData.summary?.net_profit?.actual)}</td>
                  <td style={{ textAlign: 'right', padding: '5px', fontWeight: 'bold' }}>{formatAmount(reportData.summary?.net_profit?.budget)}</td>
                  <td style={{ textAlign: 'right', padding: '5px', fontWeight: 'bold' }}>{formatAmount(reportData.summary?.net_profit?.prior_year)}</td>
                  <td style={{ textAlign: 'right', padding: '5px', fontWeight: 'bold' }}>{formatAmount(reportData.summary?.net_profit?.actual_ytd)}</td>
                  <td style={{ textAlign: 'right', padding: '5px', fontWeight: 'bold' }}>{formatAmount(reportData.summary?.net_profit?.budget_ytd)}</td>
                  <td style={{ textAlign: 'right', padding: '5px', fontWeight: 'bold' }}>{formatAmount(reportData.summary?.net_profit?.prior_year_ytd)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfitLossReport;