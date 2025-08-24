# 🚀 GUILD Scout Hub - Supabase Edge Function Deployment Guide

## **🏗️ New Architecture Overview**

We've migrated from direct GitHub API calls to a secure **Supabase Edge Function** architecture:

```
UI (GitHub Pages) → Supabase Edge Function → GitHub Actions API → Workflow Execution
```

**Benefits:**
- ✅ **Secure**: Secrets stay in Supabase, not exposed in client-side code
- ✅ **Deployable**: UI can be deployed to GitHub Pages without security concerns
- ✅ **Centralized**: All workflow management through one secure endpoint
- ✅ **Scalable**: Easy to add new workflows and parameters

## **📋 Prerequisites**

1. **Supabase Project** with Edge Functions enabled
2. **GitHub Personal Access Token** with `repo`, `workflow`, and `admin:org` scopes
3. **Supabase CLI** installed and configured

## **🔧 Step 1: Deploy Supabase Edge Function**

### **1.1 Install Supabase CLI**
```bash
npm install -g supabase
```

### **1.2 Login to Supabase**
```bash
supabase login
```

### **1.3 Link Your Project**
```bash
cd supabase
supabase link --project-ref YOUR_PROJECT_REF
```

### **1.4 Set Environment Variables**
```bash
supabase secrets set GITHUB_TOKEN=ghp_your_github_token_here
supabase secrets set GITHUB_OWNER=CG-Defense-Consulting
supabase secrets set GITHUB_REPO=guild-scout-hub
```

### **1.5 Deploy the Edge Function**
```bash
supabase functions deploy trigger-workflow
```

## **🔧 Step 2: Update GitHub Actions Workflows**

### **2.1 Remove Old Event Types**
Update all workflow files to use `workflow_dispatch` instead of `repository_dispatch`:

```yaml
# OLD (remove this)
on:
  repository_dispatch:
    types: [pull_single_rfq_pdf]

# NEW (use this)
on:
  workflow_dispatch:
    inputs:
      solicitation_number:
        description: 'Solicitation Number'
        required: true
        type: string
      contract_id:
        description: 'Contract ID (optional)'
        required: false
        type: string
```

### **2.2 Update Input Parameters**
Ensure all workflows accept the parameters sent by the Edge Function:

```yaml
inputs:
  solicitation_number:
    description: 'Solicitation Number'
    required: true
    type: string
  contract_id:
    description: 'Contract ID (optional)'
    required: false
    type: string
  triggered_at:
    description: 'Timestamp when workflow was triggered'
    required: false
    type: string
  triggered_by:
    description: 'Source that triggered the workflow'
    required: false
    type: string
```

## **🔧 Step 3: Test the Integration**

### **3.1 Test Edge Function Locally**
```bash
supabase functions serve trigger-workflow
```

### **3.2 Test with Sample Request**
```bash
curl -X POST http://localhost:54321/functions/v1/trigger-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "pull_single_rfq_pdf",
    "solicitation_number": "SPE4A625T34Q5"
  }'
```

### **3.3 Verify GitHub Actions Trigger**
Check your GitHub Actions tab to confirm the workflow was triggered.

## **🔧 Step 4: Deploy UI to GitHub Pages**

### **4.1 Remove Old GitHub Config**
Delete or comment out the old GitHub configuration files:
- `src/config/github.ts`
- Any direct GitHub API calls in components

### **4.2 Build and Deploy**
```bash
npm run build
# Deploy the dist/ folder to GitHub Pages
```

## **📊 Available Workflows**

The Edge Function supports these workflows:

| Workflow Name | Required Parameters | Optional Parameters |
|---------------|-------------------|-------------------|
| `pull_single_rfq_pdf` | `solicitation_number` | `contract_id` |
| `extract_nsn_amsc` | `contract_id`, `nsn` | `verbose` |
| `pull_day_rfq_pdfs` | `target_date` | - |
| `pull_day_rfq_index_extract` | `target_date` | - |
| `pull_single_award_history` | `solicitation_number` | - |
| `pull_day_award_history` | `target_date` | - |

## **🔒 Security Features**

### **CORS Configuration**
- Edge Function allows all origins (`*`)
- Can be restricted to specific domains in production

### **Input Validation**
- Required parameter validation
- Workflow name validation
- Parameter type checking

### **Error Handling**
- Comprehensive error logging
- User-friendly error messages
- Fallback error responses

## **🐛 Troubleshooting**

### **Common Issues**

1. **Edge Function Not Deploying**
   ```bash
   # Check Supabase CLI version
   supabase --version
   
   # Verify project link
   supabase status
   ```

2. **GitHub Token Issues**
   - Ensure token has correct scopes
   - Check token expiration
   - Verify repository access

3. **Workflow Not Triggering**
   - Check GitHub Actions permissions
   - Verify workflow file names match
   - Check workflow_dispatch configuration

### **Debug Commands**
```bash
# Check Edge Function logs
supabase functions logs trigger-workflow

# Test Edge Function locally
supabase functions serve trigger-workflow

# Check Supabase project status
supabase status
```

## **📈 Monitoring and Logs**

### **Edge Function Logs**
```bash
supabase functions logs trigger-workflow --follow
```

### **GitHub Actions Logs**
- Check the Actions tab in your repository
- Monitor workflow execution times
- Review error logs for debugging

## **🔄 Migration Checklist**

- [ ] Deploy Supabase Edge Function
- [ ] Set environment variables
- [ ] Update GitHub Actions workflows
- [ ] Test workflow triggers
- [ ] Remove old GitHub config from UI
- [ ] Deploy updated UI to GitHub Pages
- [ ] Verify all workflows work correctly

## **🎯 Next Steps**

1. **Deploy Edge Function** following Step 1
2. **Update Workflows** following Step 2
3. **Test Integration** following Step 3
4. **Deploy UI** following Step 4
5. **Monitor and Optimize** based on usage patterns

## **📞 Support**

If you encounter issues:
1. Check the troubleshooting section
2. Review Edge Function logs
3. Verify GitHub Actions configuration
4. Check Supabase project settings

---

**🎉 Congratulations!** You've successfully migrated to a secure, scalable workflow architecture!
