import { useState } from 'react';

const FileUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);

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

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus('❌ Please select a file first');
      return;
    }

    setIsUploading(true);
    setUploadStatus('📤 Uploading file...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setUploadStatus(`✅ ${result.message}`);
        // Reset the form
        setSelectedFile(null);
        // Reset file input
        document.getElementById('fileInput').value = '';
      } else {
        setUploadStatus(`❌ Error: ${result.error}`);
      }
    } catch (error) {
      setUploadStatus(`❌ Upload failed: ${error.message}`);
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
          <div style={{ fontSize: '14px', color: '#666' }}>
            Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
          </div>
        )}
      </div>

      <button 
        onClick={handleUpload}
        disabled={!selectedFile || isUploading}
        style={{
          padding: '10px 20px',
          backgroundColor: selectedFile && !isUploading ? '#007bff' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: selectedFile && !isUploading ? 'pointer' : 'not-allowed'
        }}
      >
        {isUploading ? 'Uploading...' : 'Upload File'}
      </button>

      {uploadStatus && (
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
          {uploadStatus}
        </div>
      )}
    </div>
  );
};

export default FileUpload;