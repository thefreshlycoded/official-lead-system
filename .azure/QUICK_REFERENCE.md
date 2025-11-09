# Job Viability Feature - Quick Reference Card

## 🎯 Feature Summary
AI-powered job viability analyzer using OpenAI GPT-4o-mini

## 📍 Where to Find It
- **UI Button**: "🤖 Analyze Job Viability" (blue button on job listings)
- **Single Job**: `/job_listings/:id` - Click button to analyze one job
- **Bulk**: `/job_listings` - Click button to analyze up to 50 pending jobs

## ✅ What Gets Checked

| Criterion | Looks For | Passes If |
|-----------|-----------|-----------|
| **Service Fit** | Web dev? Design? E-commerce? SEO? Marketing? | At least one matches |
| **Contact Info** | Company name? Website? Email? Phone? LinkedIn? | At least one visible |
| **Verdict** | Must pass BOTH | viable_post = true |

## 📊 Results Stored

```ruby
job.viable_post           # true/false/nil
job.classification_snippet  # "Service Fit: ... Contact Info: ..."
```

## 🚀 Quick Start

```bash
# 1. Set API key
export OPENAI_API_KEY="sk-..."

# 2. Install gem
bundle install

# 3. Run Rails server
rails s

# 4. Visit job_listings page and click button
```

## 💻 API Costs

| Action | Cost |
|--------|------|
| 1 job | ~$0.01 |
| 50 jobs | ~$0.60 |
| 200 jobs/day | ~$2.40 |

## 📝 Prompt Criteria (What GPT-4 Evaluates)

### Service Fit ✅
- Custom web development
- Web design (responsive, UX)
- E-commerce solutions
- SEO services
- Digital marketing

### Contact Info ✅
- Company name
- Website URL
- Email address
- Phone number
- LinkedIn profile
- Industry clues

## 🔧 Files Changed

```
Modified:
  - config/routes.rb (added routes)
  - app/controllers/job_listings_controller.rb (added action)
  - app/views/job_listings/index.html.erb (added button)
  - Gemfile (added ruby-openai)

Created:
  - app/services/job_viability_service.rb (core logic)
  - .azure/*.md (documentation)
```

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Access denied" | Check `echo $OPENAI_API_KEY` |
| Slow response | Normal: 2-5 seconds per job |
| JSON parse error | Check Rails log, try again |
| All marked not viable | Review job content vs. services |

## 📋 Controller Routes

```ruby
# Single job analysis
POST /job_listings/:id/analyze_job_viability

# Bulk analysis (up to 50)
POST /job_listings/analyze_job_viability?limit=50
```

## 🎛️ Service Methods

```ruby
# Single job
analyzer = JobViabilityService.new(job)
result = analyzer.analyze!
# Returns: {viable: true/false, service_fit: "...", ...}

# Bulk
result = JobViabilityService.bulk_analyze(limit: 50)
# Returns: {analyzed: 45, viable: 18}
```

## 📍 Job Categories After Analysis

```
⏳ Pending Analysis (viable_post = nil)
✅ Viable Leads (viable_post = true)
❌ Not Viable (viable_post = false)
```

## 🔐 Environment Setup

```bash
# Add to .env or shell profile
OPENAI_API_KEY=sk-proj-...

# Verify it's set
echo $OPENAI_API_KEY
```

## 📱 User Flow

```
1. User views job listings index
2. Clicks "🤖 Analyze Job Viability"
3. Chooses single job or bulk (50)
4. System sends to OpenAI
5. Gets viability decision
6. Updates job in database
7. Redirects with results
8. Job now shows in proper category
```

## 🎯 Sample Response

```json
{
  "viable": true,
  "service_fit": "E-commerce with custom development",
  "contact_info_found": "Company name + website + email",
  "reasoning": "Perfect match with good contact trail"
}
```

## ⚡ Performance

| Operation | Time | Cost |
|-----------|------|------|
| Single job | 2-5s | $0.01 |
| 50 jobs | ~60s | $0.60 |
| 200 jobs | ~4m | $2.40 |

## 🔍 Database Queries

```ruby
# Check results
JobListing.where(viable_post: true).count    # Viable
JobListing.where(viable_post: false).count   # Not viable
JobListing.where(viable_post: nil).count     # Pending

# View reasoning
JobListing.where(viable_post: false)
  .pluck(:title, :classification_snippet)
```

## 📞 Support Resources

1. **Setup Help**: `.azure/job_viability_setup.md`
2. **Examples**: `.azure/job_viability_examples.md`
3. **Prompt Details**: `.azure/job_viability_prompt_guide.md`
4. **Architecture**: `.azure/job_viability_diagrams.md`
5. **Implementation**: `.azure/job_viability_implementation.md`

## ✨ Key Innovations

✅ Two-criteria gate system (service + contact both required)
✅ Bias toward outreach (if info leaked, we can find them)
✅ Cost-efficient (GPT-4o-mini ~$0.01/job)
✅ Error-resilient (graceful fallback + logging)
✅ Rate-limited (0.5s delay in bulk processing)
✅ Clean separation of concerns (controller → service → model)

## 🎓 Next Phase Options

After viability scoring works:
- 🔜 Contact extraction prompt
- 🔜 Async background processing
- 🔜 Confidence scoring
- 🔜 Rejection categorization
- 🔜 Integration with outreach system

---

**Status:** ✅ Ready to use (after API key setup)
