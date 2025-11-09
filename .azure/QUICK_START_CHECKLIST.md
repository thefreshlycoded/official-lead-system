# 🚀 Job Viability Feature - Quick Start Checklist

## Pre-Testing Setup (5 minutes)

### ☐ 1. Get OpenAI API Key
- [ ] Visit https://platform.openai.com/api-keys
- [ ] Log in with your account (or create one)
- [ ] Click "Create new secret key"
- [ ] Copy the key (starts with `sk-proj-`)
- [ ] Keep it safe (you'll need it momentarily)

### ☐ 2. Set Environment Variable
```bash
export OPENAI_API_KEY='sk-proj-YOUR-KEY-HERE'
```

Replace `YOUR-KEY-HERE` with your actual API key.

**Verify it's set**:
```bash
echo $OPENAI_API_KEY
# Should print: sk-proj-...
```

### ☐ 3. Navigate to Project
```bash
cd /Users/antonioirizarry/Desktop/Projects/lead_system
```

### ☐ 4. Verify Gems Are Installed
```bash
bundle info ruby-openai
# Expected: ruby-openai (8.3.0)
```

---

## Testing Phase 1: Single Job Analysis (5 minutes)

### ☐ 1. Check Database
```bash
bundle exec ruby -e "require_relative 'config/environment'; puts \"Pending jobs: #{JobListing.where(viable_post: nil).count}\""
```

If result is 0:
- [ ] Run scraper to get some jobs: `python upwork_ai/main.py`
- [ ] Or manually add a test job to database

### ☐ 2. Run Single Test
```bash
bundle exec ruby test_job_viability.rb
```

**Expected Output**:
```
============================================================
Job Viability Service Test Script
============================================================
...
✅ Found job listing: ID 123
   Title: Design a website...
   Description: We need a modern website...

Analyzing job viability...

Results:
------------------------------------------------------------
Viable: true
Service Fit: Website design project aligns...
Contact Info Found: Company name visible
Reasoning: Project matches services...
------------------------------------------------------------

✅ Test completed successfully!
   Job viable_post: true
   Job classification_snippet: Website design...
```

### ☐ 3. Verify Database Updated
```bash
bundle exec ruby -e "require_relative 'config/environment'; job = JobListing.where(viable_post: true).first; puts \"Job ID: #{job&.id}, Viable: #{job&.viable_post}\" if job"
```

---

## Testing Phase 2: Web UI & Bulk Analysis (5 minutes)

### ☐ 1. Start Rails Server
```bash
rails s -p 4200
```

Wait for output:
```
=> Rails 8.0.2.1 application starting in development
=> Listening on http://localhost:4200
```

### ☐ 2. Open Job Listings Page
- [ ] Visit http://localhost:4200/job_listings in browser
- [ ] You should see your job listings
- [ ] Look for the "🤖 Analyze Job Viability" button

### ☐ 3. Run Bulk Analysis
- [ ] Click "🤖 Analyze Job Viability" button
- [ ] Confirm the popup: "Analyze job viability for up to 50 pending jobs?"
- [ ] Click OK
- [ ] Wait for analysis to complete (2-3 minutes for ~50 jobs)
- [ ] Watch for success message

### ☐ 4. Check Results
- [ ] Page should refresh automatically
- [ ] Look for sections:
  - "Viable Listings" (green, with ✅)
  - "Not Viable Listings" (red, with ❌)
  - "Pending Analysis" (gray, with ⏳)

### ☐ 5. Spot Check Accuracy
- [ ] Review 3-5 jobs marked viable:
  - Do they match our services? (Web Dev, Design, E-Commerce, SEO, Marketing)
  - Did they expose contact info? (name, website, email, phone)
- [ ] Review 3-5 jobs marked not viable:
  - Do they NOT match our services?
  - OR did they NOT expose contact info?

---

## Testing Phase 3: Error Handling (3 minutes)

### ☐ 1. Test Invalid API Key
```bash
export OPENAI_API_KEY='sk-proj-invalid-key'
bundle exec ruby test_job_viability.rb
```

Expected: ❌ Error message about invalid API key

### ☐ 2. Test Missing API Key
```bash
unset OPENAI_API_KEY
bundle exec ruby test_job_viability.rb
```

Expected: ❌ Error about missing OPENAI_API_KEY

### ☐ 3. Reset Valid Key
```bash
export OPENAI_API_KEY='sk-proj-YOUR-ACTUAL-KEY'
```

---

## Results Summary

### ✅ Success Looks Like:
- [ ] Single job analysis completes in 2-5 seconds
- [ ] Returns JSON with viable/service_fit/contact_info_found/reasoning
- [ ] Database is updated with viable_post and classification_snippet
- [ ] Bulk analysis processes multiple jobs
- [ ] Web UI button works and shows results
- [ ] Jobs are correctly categorized (viable vs not viable)
- [ ] Error messages are clear and helpful

### 🔴 If Something Fails:
1. Check OPENAI_API_KEY is set: `echo $OPENAI_API_KEY`
2. Check API key is valid (try in playground: https://platform.openai.com/playground)
3. Check internet connection
4. Check OpenAI service status: https://status.openai.com/
5. Check logs: `tail -f log/development.log`
6. Review troubleshooting section in TESTING_GUIDE.md

---

## Monitoring & Next Steps

### 📊 Check API Usage
1. Visit https://platform.openai.com/usage/overview
2. Look for today's API costs
3. Should be minimal (under $0.10 for testing)

### 📈 Success Indicators
- [ ] All jobs classified (viable or not)
- [ ] No API errors
- [ ] Costs are reasonable
- [ ] Categorization seems accurate

### 🚀 After Successful Testing
1. **Run Regular Analysis**: Click button weekly to analyze new jobs
2. **Fine-Tune Prompt**: Adjust if categorization isn't accurate
3. **Monitor Costs**: Keep eye on OpenAI usage
4. **Plan Phase 2**: Contact information extraction

---

## Quick Reference Commands

```bash
# Set API key
export OPENAI_API_KEY='sk-proj-your-key'

# Verify setup
cd /Users/antonioirizarry/Desktop/Projects/lead_system
bundle info ruby-openai

# Check pending jobs
bundle exec ruby -e "require_relative 'config/environment'; puts JobListing.where(viable_post: nil).count"

# Run single test
bundle exec ruby test_job_viability.rb

# Start server
rails s -p 4200

# View logs
tail -f log/development.log

# Check API usage
# https://platform.openai.com/usage/overview
```

---

## FAQ

**Q: How long does analysis take?**
A: Single job: 2-5 seconds. Bulk (50 jobs): 2-3 minutes.

**Q: How much does it cost?**
A: About $0.00015 per job. 100 jobs = $0.015.

**Q: Can I stop the analysis?**
A: Yes, stop the Rails server (Ctrl+C). Jobs analyzed before stopping will be saved.

**Q: What if a job doesn't have enough info?**
A: It will be marked as "not viable" due to lack of contact information.

**Q: Can I re-analyze a job?**
A: Update `viable_post` to `nil` in database, then re-run analysis.

**Q: Where do I see the AI reasoning?**
A: In the `classification_snippet` field in database (also visible in test output).

---

## 📞 Need Help?

1. **Check Documentation**:
   - `/.azure/TESTING_GUIDE.md` - Comprehensive testing guide
   - `/.azure/IMPLEMENTATION_COMPLETE.md` - Full implementation details
   - `/.azure/JOB_VIABILITY_FEATURE.md` - Feature overview

2. **Check Code**:
   - `/app/services/job_viability_service.rb` - Service implementation
   - `/app/controllers/job_listings_controller.rb` - Controller action
   - `/test_job_viability.rb` - Test script

3. **Common Issues**:
   - API key not set → `export OPENAI_API_KEY='...'`
   - Gem not found → `bundle install`
   - API timeout → Check internet connection

---

**Status**: 🟢 Ready to Test
**Estimated Time**: 15-20 minutes total
**Next Milestone**: Successful single job analysis
