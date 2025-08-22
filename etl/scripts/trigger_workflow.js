#!/usr/bin/env node
/**
 * Script to trigger GitHub Actions workflow for pulling single RFQ PDF
 * 
 * Usage:
 *   node trigger_workflow.js <solicitation_number> [options]
 * 
 * Options:
 *   --token <github_token>     GitHub personal access token
 *   --owner <owner>            Repository owner (default: current user)
 *   --repo <repo>              Repository name (default: current repo)
 *   --verbose                  Enable verbose logging
 *   --output-dir <dir>         Custom output directory
 */

const https = require('https');
const { execSync } = require('child_process');

// Configuration
const DEFAULT_OWNER = process.env.GITHUB_REPOSITORY_OWNER || 'kayacelebi';
const DEFAULT_REPO = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'guild-scout-hub';

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    solicitation_number: null,
    token: process.env.GITHUB_TOKEN,
    owner: DEFAULT_OWNER,
    repo: DEFAULT_REPO,
    verbose: false,
    output_dir: null
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    switch (arg) {
      case '--token':
        options.token = args[++i];
        break;
      case '--owner':
        options.owner = args[++i];
        break;
      case '--repo':
        options.repo = args[++i];
        break;
      case '--verbose':
        options.verbose = true;
        break;
      case '--output-dir':
        options.output_dir = args[++i];
        break;
      case '--help':
      case '-h':
        showHelp();
        process.exit(0);
        break;
      default:
        if (!options.solicitation_number) {
          options.solicitation_number = arg;
        } else {
          console.error(`Unknown argument: ${arg}`);
          showHelp();
          process.exit(1);
        }
    }
  }

  if (!options.solicitation_number) {
    console.error('Error: Solicitation number is required');
    showHelp();
    process.exit(1);
  }

  if (!options.token) {
    console.error('Error: GitHub token is required (set GITHUB_TOKEN env var or use --token)');
    process.exit(1);
  }

  return options;
}

function showHelp() {
  console.log(`
Usage: node trigger_workflow.js <solicitation_number> [options]

Arguments:
  solicitation_number          DIBBS solicitation number to download

Options:
  --token <github_token>      GitHub personal access token
  --owner <owner>             Repository owner (default: ${DEFAULT_OWNER})
  --repo <repo>               Repository name (default: ${DEFAULT_REPO})
  --verbose                   Enable verbose logging
  --output-dir <dir>          Custom output directory
  --help, -h                  Show this help message

Environment Variables:
  GITHUB_TOKEN                GitHub personal access token
  GITHUB_REPOSITORY_OWNER     Repository owner
  GITHUB_REPOSITORY           Repository name (format: owner/repo)

Examples:
  node trigger_workflow.js SPE7L3-24-R-0001
  node trigger_workflow.js SPE7L3-24-R-0001 --verbose
  node trigger_workflow.js SPE7L3-24-R-0001 --output-dir ./custom-dir
  node trigger_workflow.js SPE7L3-24-R-0001 --owner myorg --repo myrepo
`);
}

function makeRequest(options, data) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(data);
    
    const req = https.request({
      hostname: 'api.github.com',
      port: 443,
      path: `/repos/${options.owner}/${options.repo}/dispatches`,
      method: 'POST',
      headers: {
        'Authorization': `token ${options.token}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'DIBBS-ETL-Trigger',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: responseData
          });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${responseData}`));
        }
      });
    });

    req.on('error', (err) => {
      reject(err);
    });

    req.write(postData);
    req.end();
  });
}

async function triggerWorkflow(options) {
  console.log(`🚀 Triggering workflow for solicitation: ${options.solicitation_number}`);
  console.log(`📁 Repository: ${options.owner}/${options.repo}`);
  
  if (options.verbose) {
    console.log(`🔧 Options:`, options);
  }

  const payload = {
    event_type: 'pull_single_rfq_pdf',
    client_payload: {
      solicitation_number: options.solicitation_number
    }
  };

  // Add optional parameters
  if (options.output_dir) {
    payload.client_payload.output_dir = options.output_dir;
  }
  
  if (options.verbose) {
    payload.client_payload.verbose = true;
  }

  try {
    console.log('📡 Sending request to GitHub...');
    const response = await makeRequest(options, payload);
    
    if (response.statusCode === 204) {
      console.log('✅ Workflow triggered successfully!');
      console.log('📋 Check the Actions tab in your GitHub repository to monitor progress.');
      
      // Try to get the workflow run URL
      try {
        const workflowUrl = `https://github.com/${options.owner}/${options.repo}/actions`;
        console.log(`🔗 View workflow runs: ${workflowUrl}`);
      } catch (err) {
        // Ignore errors getting workflow URL
      }
    } else {
      console.log(`⚠️  Unexpected response: ${response.statusCode}`);
      console.log(`📄 Response: ${response.data}`);
    }
    
  } catch (error) {
    console.error('❌ Failed to trigger workflow:', error.message);
    
    if (error.message.includes('401')) {
      console.error('💡 Check your GitHub token - it may be invalid or expired');
    } else if (error.message.includes('404')) {
      console.error('💡 Check repository owner and name');
    } else if (error.message.includes('403')) {
      console.error('💡 Check repository permissions and workflow access');
    }
    
    process.exit(1);
  }
}

// Main execution
if (require.main === module) {
  try {
    const options = parseArgs();
    triggerWorkflow(options);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

module.exports = { triggerWorkflow, parseArgs };
