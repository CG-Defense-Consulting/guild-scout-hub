# GitHub Token Setup for DIBBS ETL Workflows

## 🔑 **Setting Up GitHub Token**

To enable the "Pull this RFQ PDF" functionality in the Contract Tracker UI, you need to configure a GitHub Personal Access Token.

### **Step 1: Create GitHub Personal Access Token**

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "DIBBS ETL Workflows")
4. Set expiration as needed (recommended: 90 days)
5. Select the following scopes:
   - `repo` - Full control of private repositories
   - `workflow` - Update GitHub Action workflows
6. Click "Generate token"
7. **Copy the token immediately** (you won't see it again!)

### **Step 2: Configure the Token**

#### **Option A: Environment Variable (Recommended)**
Add to your `.env` file:
```bash
VITE_GITHUB_TOKEN=ghp_your_token_here
```

#### **Option B: Browser Storage (Development)**
1. Open browser console on your app
2. Run: `localStorage.setItem('github_token', 'ghp_your_token_here')`
3. Refresh the page

### **Step 3: Verify Setup**

1. Open the Contract Tracker UI
2. Click on a contract to view details
3. Go to the "Automations" tab
4. You should see a "Pull this RFQ PDF" button
5. Click it to trigger the workflow

## 🚀 **How It Works**

### **Workflow Trigger**
1. User clicks "Pull this RFQ PDF" button
2. UI sends request to GitHub API
3. GitHub Actions workflow is triggered
4. Workflow downloads PDF from DIBBS
5. PDF is uploaded to Supabase storage
6. UI automatically detects the new PDF
7. RFQ link now points to Supabase instead of DIBBS

### **Benefits**
- **Faster Access**: PDFs stored locally in Supabase
- **Reliable**: No more broken DIBBS links
- **Trackable**: Full audit trail of downloads
- **Automated**: No manual intervention needed

## 🔧 **Troubleshooting**

### **"GitHub Token Required" Error**
- Verify token is set in `.env` or browser storage
- Check token has correct permissions
- Ensure token hasn't expired

### **"Failed to trigger workflow" Error**
- Check GitHub repository permissions
- Verify workflow file exists in `.github/workflows/`
- Check GitHub Actions are enabled for the repository

### **PDF Not Appearing**
- Check GitHub Actions tab for workflow status
- Verify Supabase storage permissions
- Check browser console for errors

## 📋 **Security Notes**

- **Never commit tokens** to version control
- **Use environment variables** in production
- **Rotate tokens regularly** (every 90 days)
- **Limit token scope** to minimum required permissions
- **Monitor token usage** in GitHub settings

## 🎯 **Next Steps**

1. ✅ Set up GitHub token
2. 🔄 Test workflow triggering
3. 📊 Monitor workflow execution
4. 🚀 Scale to other ETL functions
5. ⏰ Set up scheduled workflows

## 📚 **Additional Resources**

- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub Actions Workflows](https://docs.github.com/en/actions/using-workflows)
- [Repository Dispatch API](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)
