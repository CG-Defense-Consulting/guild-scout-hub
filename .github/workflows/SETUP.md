# Quick Setup Guide for DIBBS ETL Workflow

## 🚀 **Setup in 3 Steps**

### 1. **Configure GitHub Secrets**
Go to your repository → Settings → Secrets and variables → Actions, then add:

```
VITE_SUPABASE_URL = https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY = your_supabase_anon_key
```

### 2. **Test the Workflow**
- Go to Actions → Pull Single RFQ PDF
- Click "Run workflow"
- Enter a solicitation number (e.g., `SPE7L3-24-R-0001`)
- Click "Run workflow"

### 3. **Monitor Progress**
- Watch the workflow run in real-time
- Download artifacts (PDFs and logs) when complete
- Check for any errors in the logs

## 🔧 **Trigger Methods**

### **Manual (GitHub UI)**
- Actions tab → Pull Single RFQ PDF → Run workflow

### **Command Line**
```bash
cd etl/scripts
node trigger_workflow.js SPE7L3-24-R-0001
```

### **API/Webhook**
```bash
curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{"event_type":"pull_single_rfq_pdf","client_payload":{"solicitation_number":"SPE7L3-24-R-0001"}}'
```

## 📋 **What Happens**

1. **Setup**: Python 3.8 + Chrome + Dependencies
2. **Download**: Navigate to DIBBS, handle consent, download PDF
3. **Process**: Extract text and metadata from PDF
4. **Upload**: Store PDF in Supabase bucket + metadata in database
5. **Artifacts**: Upload PDF and logs for inspection

## ⚠️ **Troubleshooting**

- **Chrome Issues**: Workflow includes Chrome setup steps
- **Token Issues**: Verify GitHub secrets are correct
- **Permission Issues**: Check repository Actions settings
- **Timeout Issues**: Workflow has 30-minute limit

## 🎯 **Next Steps**

1. ✅ Test with a known solicitation number
2. 🔄 Create workflows for other ETL functions
3. ⏰ Set up scheduled runs
4. 📊 Add monitoring and notifications
