const API_URL = 'http://localhost:5000';

export const testConnection = async () => {
  try {
    const response = await fetch(`${API_URL}/`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API connection failed:', error);
    throw error;
  }
};

export const testUploadEndpoint = async () => {
  try {
    const response = await fetch(`${API_URL}/api/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ test: 'data' })
    });
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Upload endpoint test failed:', error);
    throw error;
  }
};