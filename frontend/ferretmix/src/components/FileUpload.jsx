import { useState } from 'react';

const FileUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [company, setCompany] = useState('');
  const [error, setError] = useState('');
  const [uploadResult, setUploadResult] = useState(null);
  

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    
    if (file) {
      // Validate file type
      const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
      
      if (validTypes.includes(file.type)) {
        setSelectedFile(file);
        setUploadStatus('');
      } else {
        setSelectedFile(null);
        setUploadStatus('❌ Please select an Excel file (.xlsx or .xls)');
      }
    }
  };

  const updateCompany = (e) => {
    setCompany(e.target.value)
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    if (!company) {
      setError('Please enter a company name');
      return;
    }

    setIsUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('company', company);

    try {
      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setUploadResult(data);
        setSelectedFile(null);
        setCompany('');
      } else {
        setError(data.error || 'Upload failed');
      }
    } catch (error) {
      setError('Upload failed: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', margin: '20px' }}>
      <h3>Upload Trial Balance</h3>
      
      <div style={{ marginBottom: '20px' }}>
        <input
          id="fileInput"
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileSelect}
          style={{ marginBottom: '10px' }}
        />
        
        {selectedFile && (
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
            Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
          </div>
        )}
      </div>

      {selectedFile && (
        <div style={{ marginBottom: '20px' }}>
          <label style={{ marginRight: '10px' }}>Input Company:</label>
          <input
            onChange={updateCompany}
            value={company}
            placeholder="Enter company name"
            style={{ padding: '8px', minWidth: '200px' }}
          />
        </div>
      )}

      <button 
        onClick={handleUpload}
        disabled={!selectedFile || !company || isUploading}
        style={{
          padding: '10px 20px',
          backgroundColor: selectedFile && company && !isUploading ? '#007bff' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: selectedFile && company && !isUploading ? 'pointer' : 'not-allowed',
          marginBottom: '20px'
        }}
      >
        {isUploading ? 'Uploading...' : 'Upload File'}
      </button>

      {uploadStatus && (
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
          {uploadStatus}
        </div>
      )}

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

      {uploadResult && (
        <div style={{ 
          color: 'green', 
          backgroundColor: '#d4edda', 
          padding: '10px', 
          borderRadius: '4px', 
          marginTop: '20px' 
        }}>
          <p>✓ Upload successful!</p>
          <p>File: {uploadResult.filename}</p>
          <p>Company: {uploadResult.company}</p>
          <p>Rows processed: {uploadResult.rows_processed}</p>
        </div>
      )}
    </div>
  );
};

export default FileUpload;