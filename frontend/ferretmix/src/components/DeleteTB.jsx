import { useState, useEffect } from "react";

export default function DeleteTB() {
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [availablePeriods, setAvailablePeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [selectedCompany, setSelectedCompany] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAvailableCompanies();
  }, []);

  // Fetch periods when company is selected
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

  const deleteTB = async () => {
    if (!selectedPeriod || !selectedCompany) {
      setError('Please select both company and period');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Add your delete/report generation logic here
      const response = await fetch(`http://localhost:5000/api/tb/delete?company=${selectedCompany}&period=${selectedPeriod}`, {
        method: 'DELETE'
      });
      const data = await response.json();
      
      if (response.ok) {
        alert('Successfully deleted!');
        // Reset selections and refetch
        setSelectedCompany('');
        setSelectedPeriod('');
        fetchAvailableCompanies();
      } else {
        setError(data.error || 'Failed to delete');
      }
    } catch (error) {
      setError('Failed to delete: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Delete Trial Balance</h2>
      
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
        onClick={deleteTB}
        disabled={!selectedPeriod || !selectedCompany || loading}
        style={{
          padding: '8px 20px',
          backgroundColor: selectedPeriod && selectedCompany && !loading ? '#dc3545' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: selectedPeriod && selectedCompany && !loading ? 'pointer' : 'not-allowed',
          marginBottom: '20px'
        }}
      >
        {loading ? 'Deleting...' : 'Delete Trial Balance'}
      </button>

      {error && (
        <div style={{ color: 'red', padding: '10px', backgroundColor: '#f8d7da', borderRadius: '4px' }}>
          {error}
        </div>
      )}
    </div>
  );
}