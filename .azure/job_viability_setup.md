# Job Viability Feature - Quick Setup Guide

## Prerequisites

### 1. OpenAI API Key
You need an OpenAI API key with GPT-4o-mini access.

**Get one at:** https://platform.openai.com/api/keys

**Add to environment:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Or add to `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

### 2. Ruby Gem Installation

```bash
# Install dependencies
bundle install

# This will install ruby-openai gem
```

## Testing the Feature

### 1. Start Rails Server
```bash
bin/rails server
```

### 2. Navigate to Job Listings
Visit: `http://localhost:3000/job_listings`

### 3. Try Analysis

#### Option A: Single Job Analysis
1. Click on any job listing to view details
2. Click "🤖 Analyze Job Viability" button
3. Wait for API response (usually 2-5 seconds)
4. View result and reasoning

#### Option B: Bulk Analysis
1. On job listings index, click "🤖 Analyze Job Viability" button
2. Confirm when prompted
3. System will analyze up to 50 pending jobs
4. See summary: "Analyzed X jobs. Found Y viable opportunities."

### 4. View Results

#### In Database
Jobs are updated with:
- `viable_post` = true/false
- `classification_snippet` = reasoning

#### In UI
Jobs are categorized in index view:
- **Pending Analysis** - viable_post is NULL (before analysis)
- **Viable Leads** - viable_post = true
- **Not Viable** - viable_post = false

## How It Works (Flow)

```
User clicks "Analyze Job Viability"
    ↓
Controller routes to analyze_job_viability action
    ↓
JobViabilityService.new(job).analyze!
    ↓
Build prompt with job details + Always Coded Fresh profile
    ↓
Call OpenAI GPT-4o-mini API
    ↓
Parse JSON response
    ↓
Update job with viable_post + reasoning
    ↓
Redirect with success message
```

## Common Issues & Troubleshooting

### "Access denied" Error
**Problem:** OpenAI API key missing or invalid
**Solution:**
```bash
# Check if key is set
echo $OPENAI_API_KEY

# If empty, set it
export OPENAI_API_KEY="sk-your-key-here"

# Or add to .env and restart server
```

### "JSON parsing error"
**Problem:** OpenAI returned malformed JSON
**Check:** Rails log will show the actual response
```bash
# Tail the log
tail -f log/development.log | grep "OpenAI Response:"
```

### Analysis is very slow
**Problem:** Network latency or API is slow
**Solution:**
- Check OpenAI status: https://status.openai.com/
- In bulk mode, system already adds 0.5s delay between calls
- Individual analysis usually 2-5 seconds

### All jobs marked as "not viable"
**Problem:** Prompt might be too strict, or jobs genuinely don't fit
**Check:**
1. View `classification_snippet` to see reasoning
2. Review actual job content vs. service offerings
3. Adjust prompt if needed in `JobViabilityService`

## Monitoring & Logs

### View Analysis Logs
```bash
# Follow development log
tail -f log/development.log | grep "viability"

# Or search logs
grep "Job viability" log/development.log
```

### Database Queries
```ruby
# Check how many jobs were analyzed
JobListing.where.not(viable_post: nil).count

# See viable leads
JobListing.where(viable_post: true)

# See rejected jobs with reasoning
JobListing.where(viable_post: false).pluck(:title, :classification_snippet)
```

## Cost Estimate

Using GPT-4o-mini:

| Operation | API Calls | Avg Cost |
|-----------|-----------|----------|
| Single job analysis | 1 | ~$0.01-0.02 |
| Bulk 50 jobs | 50 | ~$0.50-1.00 |
| Daily (assuming 200 jobs) | 200 | ~$2.00-4.00 |

**Note:** Prices approximate based on current OpenAI pricing. See https://openai.com/pricing for latest rates.

## Next Steps

### 1. Verify It's Working
- Run bulk analysis on 10 pending jobs
- Check results in UI
- Review `classification_snippet` for reasoning

### 2. Refine the Prompt (Optional)
If results don't match expectations:
- Edit `ALWAYS_CODED_FRESH_PROFILE` in `JobViabilityService`
- Edit `VIABILITY_PROMPT_TEMPLATE` with different criteria
- Re-analyze jobs to compare

### 3. Implement Contact Lookup (Future)
Create second prompt that:
- Takes viable jobs
- Extracts company details from listing text
- Uses web search or company databases

## Support

If issues arise:
1. Check Rails log: `log/development.log`
2. Verify OpenAI API key and quota
3. Review the prompt in `app/services/job_viability_service.rb`
4. Test with a single job first before bulk operations
