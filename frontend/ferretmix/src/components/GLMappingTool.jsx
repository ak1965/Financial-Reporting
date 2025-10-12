import { useState, useEffect } from 'react';

const GLMappingTool = () => {
  const [trialBalances, setTrialBalances] = useState([]);
  const [selectedTB, setSelectedTB] = useState('');
  const [glCodes, setGLCodes] = useState([]);
  const [reportType, setReportType] = useState('profit_loss');
  const [reportLines, setReportLines] = useState({});
  const [existingMappings, setExistingMappings] = useState({});
  const [loading, setLoading] = useState(false);

  // Load available trial balances on component mount
  useEffect(() => {
    fetchTrialBalances();
  }, []);

  // Load report lines when report type changes
  useEffect(() => {
    if (reportType) {
      fetchReportLines();
      fetchExistingMappings();
    }
  }, [reportType]);

  // Load GL codes when trial balance is selected
  useEffect(() => {
    if (selectedTB) {
      fetchGLCodes();
    }
  }, [selectedTB]);

  const fetchTrialBalances = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/mappings/trial-balances');
      const data = await response.json();
      setTrialBalances(data.trial_balances || []);
    } catch (error) {
      console.error('Error fetching trial balances:', error);
    }
  };

  const fetchGLCodes = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:5000/api/mappings/gl-codes/${selectedTB}`);
      const data = await response.json();
      setGLCodes(data.gl_codes || []);
    } catch (error) {
      console.error('Error fetching GL codes:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReportLines = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/mappings/report-lines/${reportType}`);
      const data = await response.json();
      setReportLines(data.report_lines || {});
    } catch (error) {
      console.error('Error fetching report lines:', error);
    }
  };

  const fetchExistingMappings = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/mappings/mappings/${reportType}`);
      const data = await response.json();
      const mappingsObj = {};
      data.mappings?.forEach(mapping => {
        mappingsObj[mapping.gl_code] = {
          line_id: mapping.line_id,
          sign_multiplier: mapping.sign_multiplier
        };
      });
      setExistingMappings(mappingsObj);
    } catch (error) {
      console.error('Error fetching existing mappings:', error);
    }
  };

  const [savingStates, setSavingStates] = useState({}); // Add this state

const handleMappingChange = async (glCode, lineId, signMultiplier) => {
  try {
    // Show saving state
    setSavingStates(prev => ({ ...prev, [glCode]: 'saving' }));
    
    const response = await fetch('http://localhost:5000/api/mappings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        gl_code: glCode,
        report_type: reportType,
        line_id: lineId,
        sign_multiplier: signMultiplier
      }),
    });

    if (response.ok) {
      // Update local state
      setExistingMappings(prev => ({
        ...prev,
        [glCode]: { line_id: lineId, sign_multiplier: signMultiplier }
      }));
      
      // Show saved state (remove the setTimeout - keep it permanently)
      setSavingStates(prev => ({ ...prev, [glCode]: 'saved' }));
      
    } else {
      setSavingStates(prev => ({ ...prev, [glCode]: 'error' }));
    }
  } catch (error) {
    console.error('Error saving mapping:', error);
    setSavingStates(prev => ({ ...prev, [glCode]: 'error' }));
  }
};
  const handleDeleteMapping = async (glCode) => {
    try {
      const response = await fetch(`http://localhost:5000/api/mappings/${glCode}/${reportType}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setExistingMappings(prev => {
          const updated = { ...prev };
          delete updated[glCode];
          return updated;
        });
        console.log('Mapping deleted successfully');
      }
    } catch (error) {
      console.error('Error deleting mapping:', error);
    }
  };

  const renderReportLineOptions = () => {
    const options = [];
    Object.entries(reportLines).forEach(([sectionName, lines]) => {
      options.push(
        <optgroup key={sectionName} label={sectionName.toUpperCase()}>
          {lines.map(line => (
            <option key={line.id} value={`${line.id}|${line.sign_multiplier}`}>
              {line.name}
            </option>
          ))}
        </optgroup>
      );
    });
    return options;
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>GL Code Mapping Tool</h2>
      
      {/* Controls */}
      <div style={{ marginBottom: '30px', display: 'flex', gap: '20px', alignItems: 'end' }}>
        <div>
          <label>Select Trial Balance:</label>
          <select 
            value={selectedTB} 
            onChange={(e) => setSelectedTB(e.target.value)}
            style={{ marginLeft: '10px', padding: '5px', minWidth: '200px' }}
          >
            <option value="">Choose Trial Balance...</option>
            {trialBalances.map(tb => (
              <option key={tb.upload_id} value={tb.upload_id}>
                {tb.filename} - {tb.period_end_date}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Report Type:</label>
          <select 
            value={reportType} 
            onChange={(e) => setReportType(e.target.value)}
            style={{ marginLeft: '10px', padding: '5px' }}
          >
            <option value="profit_loss">Profit & Loss</option>
            <option value="balance_sheet">Balance Sheet</option>
          </select>
        </div>
      </div>

      {/* Mapping Table */}
      {selectedTB && glCodes.length > 0 && (
        <div>
          <h3>Map GL Codes to Report Lines</h3>
          {loading ? (
            <p>Loading GL codes...</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '10px', border: '1px solid #ddd' }}>GL Code</th>
                  <th style={{ padding: '10px', border: '1px solid #ddd' }}>Account Name</th>
                  <th style={{ padding: '10px', border: '1px solid #ddd' }}>Amount</th>
                  <th style={{ padding: '10px', border: '1px solid #ddd' }}>Report Line</th>
                  <th style={{ padding: '10px', border: '1px solid #ddd' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {glCodes.map(glCode => (
                  <tr key={glCode.gl_code}>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                      {glCode.gl_code}
                    </td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                      {glCode.account_name}
                    </td>
                    <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'right' }}>
                      {glCode.amount?.toLocaleString()}
                    </td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                      <select
                        value={existingMappings[glCode.gl_code] ? 
                          `${existingMappings[glCode.gl_code].line_id}|${existingMappings[glCode.gl_code].sign_multiplier}` : ''}
                        onChange={(e) => {
                          if (e.target.value) {
                            const [lineId, signMultiplier] = e.target.value.split('|');
                            handleMappingChange(glCode.gl_code, lineId, parseInt(signMultiplier));
                          }
                        }}
                        style={{ width: '100%', padding: '5px' }}
                      >
                        <option value="">Select report line...</option>
                        {renderReportLineOptions()}
                      </select>
                    </td>
                    <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center' }}>
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
    {/* Saving/Saved/Error status */}
    {savingStates[glCode.gl_code] === 'saving' && (
      <span style={{ color: 'orange', fontSize: '14px' }}>Saving...</span>
    )}
    {savingStates[glCode.gl_code] === 'saved' && (
      <span style={{ color: 'green', fontSize: '14px' }}>✓ Saved</span>
    )}
    {savingStates[glCode.gl_code] === 'error' && (
      <span style={{ color: 'red', fontSize: '14px' }}>❌ Error</span>
    )}
    
    {/* Remove button - show when mapping exists */}
    {existingMappings[glCode.gl_code] && (
      <button
        onClick={() => handleDeleteMapping(glCode.gl_code)}
        style={{ 
          backgroundColor: '#dc3545', 
          color: 'white', 
          border: 'none', 
          padding: '5px 10px', 
          borderRadius: '3px',
          cursor: 'pointer',
          fontSize: '12px'
        }}
      >
        Remove
      </button>
    )}
  </div>
</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};

export default GLMappingTool;