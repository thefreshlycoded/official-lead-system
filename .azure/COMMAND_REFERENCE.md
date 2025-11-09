# 🎯 Job Viability Feature - Visual Guide & Commands

## 📋 Complete Command Reference

### Setup (Do This First)

```bash
# 1. Get API key from: https://platform.openai.com/api-keys
# Copy your key (starts with sk-proj-)

# 2. Set environment variable
export OPENAI_API_KEY='sk-proj-your-key-here'

# 3. Verify it's set
echo $OPENAI_API_KEY
# Should output: sk-proj-... (not blank)

# 4. Navigate to project
cd /Users/antonioirizarry/Desktop/Projects/lead_system

# 5. Verify gems
bundle info ruby-openai
# Should show: ruby-openai (8.3.0)
```

### Testing Single Job

```bash
# Run the test script
bundle exec ruby test_job_viability.rb

# Expected output:
# ============================================================
# Job Viability Service Test Script
# ============================================================
# Finding a pending job listing...
# ✅ Found job listing: ID 123
#    Title: Design a website...
#    Description: We need a modern website...
#
# Analyzing job viability...
#
# Results:
# Viable: true
# Service Fit: Website design...
# Contact Info Found: Company name...
# Reasoning: Project matches...
#
# ✅ Test completed successfully!
```

### Testing via Web UI

```bash
# 1. Start Rails server
rails s -p 4200
# Wait for: "Listening on http://localhost:4200"

# 2. In browser, visit: http://localhost:4200/job_listings

# 3. Look for: "🤖 Analyze Job Viability" button (blue button)

# 4. Click the button

# 5. Confirm: "Analyze job viability for up to 50 pending jobs?"

# 6. Click OK

# 7. Wait 2-3 minutes for analysis

# 8. See results organized as:
#    - Viable Listings (green section)
#    - Not Viable Listings (red section)
#    - Pending Analysis (gray section)
```

### Database Inspection

```bash
# Check job counts
bundle exec ruby -e "require_relative 'config/environment'; puts \"Total: #{JobListing.count}, Pending: #{JobListing.where(viable_post: nil).count}, Viable: #{JobListing.where(viable_post: true).count}, Not Viable: #{JobListing.where(viable_post: false).count}\""

# Check a specific job
bundle exec ruby -e "require_relative 'config/environment'; j = JobListing.first; puts \"Job #{j.id}: Viable=#{j.viable_post}, Snippet: #{j.classification_snippet.truncate(100) if j.classification_snippet}\""

# Reset a job for re-analysis
bundle exec ruby -e "require_relative 'config/environment'; JobListing.find(123).update(viable_post: nil); puts 'Reset job 123'"
```

### Monitoring & Debugging

```bash
# View Rails logs
tail -f log/development.log

# Check OpenAI API usage
# Visit: https://platform.openai.com/usage/overview

# Check API key is valid
# Visit: https://platform.openai.com/api-keys

# Test connection
bundle exec ruby -e "require 'openai'; client = OpenAI::Client.new(api_key: ENV['OPENAI_API_KEY']); puts 'API Key Valid!' if client"
```

---

## 🎨 Visual Flow Diagrams

### Single Job Analysis Flow
```
┌──────────────────────────────────────────────────────────┐
│ Start: User has Job Listing ID 123                      │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
    ┌─────────────────────────────┐
    │ JobViabilityService.new(job)│
    └────────┬────────────────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │ service.analyze!                │
    │ (calls OpenAI GPT-4o-mini)      │
    └────────┬────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │ Receives JSON Response:                 │
    │ {                                       │
    │   viable: true/false,                  │
    │   service_fit: "...",                  │
    │   contact_info_found: "...",           │
    │   reasoning: "..."                     │
    │ }                                       │
    └────────┬────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │ Update Database:                        │
    │ - viable_post = true/false              │
    │ - classification_snippet = reasoning    │
    └────────┬────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │ Return Result & Display Message         │
    │ ✅ "Job marked as viable!"              │
    │ or                                      │
    │ ❌ "Job marked as not viable"           │
    └─────────────────────────────────────────┘
```

### Bulk Analysis Flow (Web UI)
```
┌──────────────────────────────────┐
│ User Clicks Button:              │
│ "🤖 Analyze Job Viability"       │
└────────┬─────────────────────────┘
         │
         ▼
    ┌─────────────────────────────┐
    │ Confirmation Dialog         │
    │ "Analyze up to 50 jobs?"    │
    │ [OK] [Cancel]               │
    └────────┬────────────────────┘
             │ OK
             ▼
    ┌─────────────────────────────────────────┐
    │ POST /job_listings/analyze_job_viability│
    │ with limit=50 parameter                 │
    └────────┬────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ Controller Calls:                        │
    │ JobViabilityService.bulk_analyze(50)    │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ Service Loop (0.5s delay between jobs): │
    │ For each pending job:                   │
    │   - Analyze with OpenAI                 │
    │   - Update database                     │
    │   - Sleep 0.5 seconds                   │
    │ Return { analyzed: 42, viable: 18 }    │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ Display Results:                         │
    │ ✅ "Analyzed 42 jobs"                   │
    │ ✅ "18 marked viable"                   │
    │ ✅ "24 marked not viable"               │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ Redirect & Show Categorized Jobs        │
    │                                          │
    │ 🟢 Viable Listings (18)                 │
    │ 🔴 Not Viable Listings (24)             │
    │ ⏳ Pending Analysis (0)                 │
    └──────────────────────────────────────────┘
```

### AI Decision Logic
```
┌──────────────────────────────────────────┐
│ Input: Job Listing                       │
│ (title, description, company, etc.)      │
└────────┬─────────────────────────────────┘
         │
         ▼
    ┌────────────────────────────────────┐
    │ Criterion 1: Service Fit           │
    │ Check if project matches:          │
    │ • Web Development                  │
    │ • Web Design                       │
    │ • E-Commerce                       │
    │ • SEO                              │
    │ • Digital Marketing                │
    └────────┬─────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   MATCH        NO MATCH
    ✅             ❌
     │              │
     │              └──────┐
     │                     │
     ▼                     ▼
 ┌─────────────────────────────────┐
 │ Criterion 2: Contact Info       │
 │ Check for:                      │
 │ • Company name                  │
 │ • Website URL                   │
 │ • Email address                 │
 │ • Phone number                  │
 │ • LinkedIn profile              │
 └────────┬────────────────────────┘
          │
   ┌──────┴──────┐
   │             │
   ▼             ▼
FOUND       NOT FOUND
 ✅           ❌
  │            │
  └──┬────┬────┘
     │    │
     ▼    ▼
  ┌──────────────┐
  │ Final Result │
  └──────────────┘
     │    │
 ✅  │    │  ❌
     ▼    ▼
   VIABLE  NOT VIABLE
```

---

## 📊 Example Job Analysis Results

### Example 1: VIABLE Job ✅

```
Input:
  Title: "Design Modern E-Commerce Website"
  Description: "We're TechCorp (www.techcorp.com), an online
               retail startup. We need a Shopify store with
               custom CSS. Contact: john@techcorp.com
               or 555-123-4567"

Analysis Result:
  {
    "viable": true,
    "service_fit": "E-commerce website design matches our web
                   design and e-commerce services",
    "contact_info_found": "Company name (TechCorp), website
                          (www.techcorp.com), email
                          (john@techcorp.com), phone
                          (555-123-4567)",
    "reasoning": "This project is a great fit for our e-commerce
                 and web design services. The client has exposed
                 multiple contact points for research and outreach."
  }

Database Update:
  viable_post = true
  classification_snippet = "E-commerce website design matches our
                           web design and e-commerce services..."
```

### Example 2: NOT VIABLE Job ❌

```
Input:
  Title: "Website Redesign"
  Description: "We need a complete website redesign. Our current
               site is outdated. Budget: $5000-10000."

Analysis Result:
  {
    "viable": false,
    "service_fit": "Website redesign matches our web design
                   services",
    "contact_info_found": "No company name, email, or contact
                          information provided",
    "reasoning": "Although this project matches our web design
                 services, the client has not exposed sufficient
                 contact information for us to research and reach
                 out to them."
  }

Database Update:
  viable_post = false
  classification_snippet = "Project matches services but
                           insufficient contact info..."
```

---

## 🔧 Configuration & Tuning

### Current Settings
```ruby
# Model: GPT-4o-mini (fast, cost-effective)
# Temperature: 0.3 (consistent, predictable)
# Max tokens: 500 (enough for response)
# Timeout: 10 seconds
# Rate limit: 0.5s between bulk jobs
```

### If You Need to Adjust

Edit: `app/services/job_viability_service.rb`

```ruby
# Change temperature (0.0 = deterministic, 1.0 = creative)
temperature: 0.3  # ← Change this value

# Change model (if needed)
model: "gpt-4o-mini"  # ← Or use "gpt-4-turbo"

# Change rate limit delay
sleep(0.5)  # ← Adjust delay between jobs
```

---

## 🐛 Troubleshooting Decision Tree

```
Problem: Test fails with API error
├─ Check: Is OPENAI_API_KEY set?
│  └─ Fix: export OPENAI_API_KEY='sk-proj-...'
│
├─ Check: Is API key valid?
│  └─ Fix: Generate new key at platform.openai.com
│
├─ Check: Is account funded?
│  └─ Fix: Add payment method to OpenAI account
│
└─ Check: Is ruby-openai installed?
   └─ Fix: bundle install

Problem: No pending jobs found
├─ Run scraper: python upwork_ai/main.py
│
└─ Or create test job in database

Problem: Jobs not updating in database
├─ Check: Rails server running?
│  └─ Fix: rails s -p 4200
│
├─ Check: Database connection?
│  └─ Fix: rails db:migrate
│
└─ Check: Logs: tail -f log/development.log

Problem: Web UI button not working
├─ Check: Page reloaded? (Cmd+Shift+R)
│
├─ Check: Server running? (rails s -p 4200)
│
└─ Check: Rails console: bundle exec rails console
   └─ Try: JobListing.count
```

---

## 📈 Performance Benchmarks

```
Single Job:          2-5 seconds
Bulk (10 jobs):      12-20 seconds
Bulk (50 jobs):      2-3 minutes
Bulk (100 jobs):     4-6 minutes

API Cost Breakdown:
• Input tokens:   ~150-200 per request
• Output tokens:  ~50-100 per response
• Total:          ~200-300 tokens per job
• Cost:           ~$0.00015 per job @ gpt-4o-mini rates

Example Costs:
• 10 jobs:    ~$0.0015
• 100 jobs:   ~$0.015
• 1000 jobs:  ~$0.15
• 10000 jobs: ~$1.50
```

---

## ✅ Success Metrics

You'll know it's working when:

```
✅ Test script runs without errors
✅ Job is analyzed in 2-5 seconds
✅ Response includes viable/service_fit/contact_info_found/reasoning
✅ Database fields updated (viable_post, classification_snippet)
✅ Web UI button is clickable
✅ Bulk analysis processes multiple jobs
✅ Jobs appear in correct categories (Viable/Not Viable/Pending)
✅ OpenAI costs are reasonable (~$0.00015 per job)
✅ No API errors in logs
✅ Error messages are clear and helpful
```

---

## 🚀 You're Ready!

All commands and visual guides are provided above. Pick your testing method:

**Option 1: Command Line (Fastest)**
```bash
export OPENAI_API_KEY='sk-proj-...'
bundle exec ruby test_job_viability.rb
```

**Option 2: Web UI (Visual)**
```bash
export OPENAI_API_KEY='sk-proj-...'
rails s -p 4200
# Then click the button in browser
```

**Option 3: Both (Complete)**
```bash
# Run command line test first
bundle exec ruby test_job_viability.rb

# Then start server and test UI
rails s -p 4200
```

---

**Ready?** Start with an API key, then run a test!
