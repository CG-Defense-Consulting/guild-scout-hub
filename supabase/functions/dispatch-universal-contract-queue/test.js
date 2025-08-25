// Test script for the dispatch-universal-contract-queue Edge Function
// This can be run locally or used as a reference for testing

const testEdgeFunction = async () => {
  const supabaseUrl = 'YOUR_SUPABASE_URL'
  const supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY'
  
  // Test payload - no contract IDs needed!
  const testPayload = {
    force_refresh: false,
    headless: true,
    timeout: 30,
    retry_attempts: 3,
    batch_size: 50,
    verbose: true,
    limit: 25  // Process up to 25 contracts
  }
  
  try {
    console.log('Testing dispatch-universal-contract-queue Edge Function...')
    console.log('Payload:', JSON.stringify(testPayload, null, 2))
    
    const response = await fetch(`${supabaseUrl}/functions/v1/dispatch-universal-contract-queue`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testPayload)
    })
    
    const data = await response.json()
    
    console.log('Response Status:', response.status)
    console.log('Response Data:', JSON.stringify(data, null, 2))
    
    if (response.ok) {
      console.log('✅ Edge Function test successful!')
      console.log(`🔄 Workflow: ${data.workflow}`)
      console.log(`⏰ Dispatched at: ${data.dispatched_at}`)
      console.log(`📝 Note: ${data.note}`)
    } else {
      console.log('❌ Edge Function test failed!')
      console.log(`Error: ${data.error}`)
    }
    
  } catch (error) {
    console.error('❌ Test failed with error:', error.message)
  }
}

// Test with minimal payload
const testMinimalPayload = async () => {
  const supabaseUrl = 'YOUR_SUPABASE_URL'
  const supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY'
  
  // Minimal payload - just trigger the workflow
  const minimalPayload = {}
  
  try {
    console.log('\n--- Testing Minimal Payload ---')
    console.log('Minimal Payload:', JSON.stringify(minimalPayload, null, 2))
    
    const response = await fetch(`${supabaseUrl}/functions/v1/dispatch-universal-contract-queue`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(minimalPayload)
    })
    
    const data = await response.json()
    
    console.log('Response Status:', response.status)
    console.log('Response Data:', JSON.stringify(data, null, 2))
    
    if (response.ok) {
      console.log('✅ Minimal payload test successful!')
      console.log('Workflow will use all default settings')
    } else {
      console.log('❌ Minimal payload test failed!')
      console.log(`Error: ${data.error}`)
    }
    
  } catch (error) {
    console.error('❌ Minimal payload test failed with error:', error.message)
  }
}

// Test with custom processing limit
const testCustomLimit = async () => {
  const supabaseUrl = 'YOUR_SUPABASE_URL'
  const supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY'
  
  // Custom limit payload
  const customLimitPayload = {
    limit: 10,  // Process only 10 contracts
    verbose: true
  }
  
  try {
    console.log('\n--- Testing Custom Limit ---')
    console.log('Custom Limit Payload:', JSON.stringify(customLimitPayload, null, 2))
    
    const response = await fetch(`${supabaseUrl}/functions/v1/dispatch-universal-contract-queue`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(customLimitPayload)
    })
    
    const data = await response.json()
    
    console.log('Response Status:', response.status)
    console.log('Response Data:', JSON.stringify(data, null, 2))
    
    if (response.ok) {
      console.log('✅ Custom limit test successful!')
      console.log(`Workflow will process up to ${customLimitPayload.limit} contracts`)
    } else {
      console.log('❌ Custom limit test failed!')
      console.log(`Error: ${data.error}`)
    }
    
  } catch (error) {
    console.error('❌ Custom limit test failed with error:', error.message)
  }
}

// Run all tests
const runAllTests = async () => {
  console.log('🚀 Starting Edge Function Tests...\n')
  
  await testEdgeFunction()
  await testMinimalPayload()
  await testCustomLimit()
  
  console.log('\n🏁 All tests completed!')
  console.log('\n📋 Summary:')
  console.log('- The workflow now internally queries universal_contract_queue')
  console.log('- No contract IDs need to be specified')
  console.log('- Workflow automatically discovers what needs processing')
  console.log('- Optional limit parameter controls processing volume')
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    testEdgeFunction,
    testMinimalPayload,
    testCustomLimit,
    runAllTests
  }
}

// Run tests if this file is executed directly
if (typeof window === 'undefined') {
  runAllTests()
}
