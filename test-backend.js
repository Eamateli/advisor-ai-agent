// Simple test script to check backend health
// Using built-in fetch (Node.js 18+)

async function testBackend() {
  try {
    console.log('🔍 Testing backend health...');
    
    // Test health endpoint
    const healthResponse = await fetch('http://localhost:8000/health');
    console.log('Health status:', healthResponse.status);
    
    if (healthResponse.ok) {
      const healthData = await healthResponse.json();
      console.log('✅ Backend is healthy:', healthData);
    } else {
      console.log('❌ Backend health check failed');
    }
    
    // Test root endpoint
    const rootResponse = await fetch('http://localhost:8000/');
    console.log('Root status:', rootResponse.status);
    
    if (rootResponse.ok) {
      const rootData = await rootResponse.json();
      console.log('✅ Backend root:', rootData);
    }
    
  } catch (error) {
    console.error('❌ Backend test failed:', error.message);
  }
}

testBackend();
