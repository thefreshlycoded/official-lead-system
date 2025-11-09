# Job Viability Feature - Testing Guide

## 🎯 Quick Start

The Job Viability feature is now fully implemented and ready for testing! Follow these steps:

### Step 1: Set Up OpenAI API Key

```bash
export OPENAI_API_KEY='sk-proj-your-actual-api-key-here'
```

**Important**: Replace with your actual OpenAI API key from https://platform.openai.com/api-keys

### Step 2: Verify Installation

```bash
cd /Users/antonioirizarry/Desktop/Projects/lead_system

# Check if ruby-openai gem is installed
bundle list | grep openai
# Expected output: ruby-openai (8.3.0)

# Or get more details:
bundle info ruby-openai
```

### Step 3: Test Single Job Analysis

Run the test script (replace the API key):

```bash
export OPENAI_API_KEY='sk-proj-your-api-key'
bundle exec ruby test_job_viability.rb
```

Expected output:
```
============================================================
Job Viability Service Test Script
============================================================
Finding a pending job listing...
✅ Found job listing: ID 123
   Title: Design a website for my startup...
   Description: We need a modern, responsive website...

Analyzing job viability...

Results:
------------------------------------------------------------
Viable: true
Service Fit: Website design project aligns with web design services
Contact Info Found: Company name "TechStartup" visible in description
Reasoning: Project matches service offerings and sufficient contact info available
------------------------------------------------------------

✅ Test completed successfully!
   Job viable_post: true
   Job classification_snippet: Website design project aligns with...
```

### Step 4: Test via Web Interface

1. Start the Rails server:
```bash
rails s -p 4200
```

2. Navigate to: http://localhost:4200/job_listings

3. Click the "🤖 Analyze Job Viability" button

4. Check the results - jobs should appear in:
   - "Viable Listings" (viable_post = true)
   - "Not Viable Listings" (viable_post = false)

## 📊 What Gets Evaluated

The AI analyzes each job for TWO criteria:

### 1. **Service Fit** ✅
Does the job match Always Coded Fresh's services?
- Web Development
- Web Design
- E-Commerce
- SEO
- Digital Marketing

### 2. **Contact Information Leakage** ℹ️
Did the client expose enough info to research them?
- Company name
- Website URL
- Email address
- Phone number
- LinkedIn profile
- Other identifiable details

**Jobs are marked VIABLE only if BOTH criteria are met.**

## 🗄️ Database Fields Updated

After analysis, two fields are updated:

| Field | Type | Description |
|-------|------|-------------|
| `viable_post` | boolean | true = viable, false = not viable, nil = pending |
| `classification_snippet` | text | AI reasoning and findings |

## 🔧 Testing Scenarios

### Test Scenario 1: Perfect Job (Should be Viable ✅)

```
Title: "Build Modern E-Commerce Website"
Description: "We're TechCorp (www.techcorp.com). We need a Shopify store
with custom integrations. Contact: john@techcorp.com or 555-123-4567"
```

**Expected**: ✅ Viable = true
- ✅ Service Fit: E-Commerce matches services
- ✅ Contact Info: Company name, website, email, phone all present

### Test Scenario 2: No Contact Info (Should NOT be Viable ❌)

```
Title: "Website Redesign Project"
Description: "We need a complete website redesign. The site is currently
outdated and we want modern design. Budget: $5000-10000."
```

**Expected**: ❌ Viable = false
- ✅ Service Fit: Web design matches services
- ❌ Contact Info: No company name, email, or phone provided

### Test Scenario 3: Wrong Service (Should NOT be Viable ❌)

```
Title: "Need Java Developer for Mobile App"
Description: "We're building a cross-platform mobile app.
Contact: startups@example.com"
```

**Expected**: ❌ Viable = false
- ❌ Service Fit: Mobile development not in our services
- ✅ Contact Info: Email provided

## 📈 Performance Expectations

- **Single Analysis**: ~2-5 seconds (API call + processing)
- **Bulk Analysis (50 jobs)**: ~2-3 minutes (with rate limiting)
- **Rate Limiting**: 0.5 second delay between jobs to avoid API throttling

## 💰 Cost Estimation

Using `gpt-4o-mini` model:
- ~500 tokens per job analysis
- ~$0.00015 per job
- 100 jobs ≈ $0.015

## 🐛 Troubleshooting

### Issue: "API key not found"
```
Fix: export OPENAI_API_KEY='your-key-here'
```

### Issue: "Connection timeout"
```
Fix: Check internet connection
     Verify OpenAI API is accessible
     Try again after a moment
```

### Issue: "Invalid request model"
```
Fix: Ensure model name is 'gpt-4o-mini' in JobViabilityService
     Check OpenAI account has access to this model
```

### Issue: "Jobs not updating"
```
Fix: Verify database connection: rails db:migrate
    Check logs: tail -f log/development.log
    Reload in browser: Cmd/Ctrl + Shift + R
```

## 📝 Implementation Details

### Key Files

| File | Purpose |
|------|---------|
| `/app/services/job_viability_service.rb` | Main AI integration service |
| `/app/controllers/job_listings_controller.rb` | Controller action `analyze_job_viability` |
| `/app/views/job_listings/index.html.erb` | UI button for analysis |
| `/config/routes.rb` | Routes for analysis endpoints |

### API Endpoints

```ruby
# Single job analysis
POST /job_listings/:id/analyze_job_viability

# Bulk analysis (up to 50 jobs)
POST /job_listings/analyze_job_viability?limit=50
```

### Response Format (JSON)

```json
{
  "viable": true,
  "service_fit": "Website design with e-commerce integration",
  "contact_info_found": "Company name and email visible",
  "reasoning": "Project aligns with web design and e-commerce services, sufficient contact information exposed"
}
```

## ✅ Success Criteria

- [x] OpenAI gem installed
- [x] Service class created with OpenAI integration
- [x] Controller action implemented
- [x] UI button added to index view
- [x] Routes configured
- [ ] **NEXT**: Run test with OPENAI_API_KEY set
- [ ] **NEXT**: Verify analysis results match expectations
- [ ] **NEXT**: Fine-tune prompt if needed based on results
- [ ] **NEXT**: Monitor API costs in OpenAI dashboard

## 🚀 Next Steps

1. **Get OpenAI API Key**: https://platform.openai.com/api-keys
2. **Set environment variable**: `export OPENAI_API_KEY='your-key'`
3. **Run the test**: `bundle exec ruby test_job_viability.rb`
4. **Review results**: Check if jobs are categorized correctly
5. **Iterate**: Adjust prompt in `JobViabilityService` if needed

---

**Questions?** Check the service implementation at `/app/services/job_viability_service.rb` for the full prompt and logic.
