// GitHub API Configuration
export const GITHUB_CONFIG = {
  // Repository information
  OWNER: 'CG-Defense-Consulting',
  REPO: 'guild-scout-hub',
  
  // API endpoints
  API_BASE: 'https://api.github.com',
  
  // Workflow event types
  WORKFLOW_EVENTS: {
    PULL_SINGLE_RFQ_PDF: 'pull_single_rfq_pdf',
    PULL_DAY_RFQ_PDFS: 'pull_day_rfq_pdfs',
    PULL_DAY_RFQ_INDEX: 'pull_day_rq_index_extract',
    PULL_SINGLE_AWARD_HISTORY: 'pull_single_award_history',
    PULL_DAY_AWARD_HISTORY: 'pull_day_award_history',
    EXTRACT_NSN_AMSC: 'extract_nsn_amsc'
  }
};

// Get GitHub token from environment
export const getGitHubToken = (): string | null => {
  // Client-side: check for token in localStorage or sessionStorage first
  if (typeof window !== 'undefined') {
    const localToken = localStorage.getItem('github_token') || 
                       sessionStorage.getItem('github_token');
    if (localToken) {
      return localToken;
    }
    
    // Check for Vite environment variable (accessible via import.meta.env)
    const viteToken = import.meta.env.VITE_GITHUB_TOKEN;
    if (viteToken) {
      return viteToken;
    }
    
    return null;
  }
  
  // Server-side: not available in browser environment
  return null;
};


