# Job Viability Analysis Feature

## Overview

AI-powered job viability scoring using OpenAI to automatically evaluate Upwork job listings against Always Coded Fresh's service offerings and contact information availability.

## What It Does

The feature analyzes pending job listings on **two criteria**:

1. **Service Fit**: Does the project match Always Coded Fresh's services?
   - Custom Web Development
   - Web Design
   - E-Commerce Solutions
   - SEO Services
   - Digital Marketing

2. **Contact Leakage**: Did the client leak enough info to research them?
   - Company name mentioned
   - Website provided
   - Email/phone disclosed
   - LinkedIn profile visible
   - Any other identifiable information

**A job is marked viable only if BOTH criteria are met.**

## Architecture

### Files Created/Modified

```
app/services/job_viability_service.rb          # Main analysis logic
app/controllers/job_listings_controller.rb     # New analyze_job_viability action
app/views/job_listings/index.html.erb          # New UI button
config/routes.rb                               # New routes
Gemfile                                        # Added ruby-openai gem
```

### Data Flow

```
User clicks "🤖 Analyze Job Viability" button
         ↓
POST /job_listings/analyze_job_viability
         ↓
JobListingsController#analyze_job_viability
         ↓
JobViabilityService.analyze! (single job)
OR
JobViabilityService.bulk_analyze (up to 50 jobs)
         ↓
OpenAI API (gpt-4o-mini)
         ↓
Parse response JSON
         ↓
Update job_listing:
  - viable_post = true/false
  - classification_snippet = reasoning
         ↓
Redirect with success/failure message
```

## Usage

### Bulk Analysis (from Dashboard)

Click the **"🤖 Analyze Job Viability"** button on the Job Listings page to analyze up to 50 pending jobs at once.

```erb
<button type="submit" class="btn btn-primary" onclick="return confirm('Analyze job viability for up to 50 pending jobs?')">
  🤖 Analyze Job Viability
</button>
```

### Single Job Analysis (from Detail View)

POST to `/job_listings/:id/analyze_job_viability` to analyze a specific job.

### API Response

The service returns a JSON structure:

```json
{
  "viable": true,
  "service_fit": "Custom web development with modern tech stack",
  "contact_info_found": "Company name: Acme Corp, Website: acmecorp.com, Email in contact form",
  "reasoning": "Strong service fit with e-commerce requirements and adequate contact info available"
}
```

## Database Fields Updated

For each analyzed job, these columns are populated:

| Field | Type | Purpose |
|-------|------|---------|
| `viable_post` | boolean | Viability determination (true/false/nil) |
| `classification_snippet` | text | Detailed reasoning combining service fit + contact info found |

## OpenAI Configuration

**Model**: `gpt-4o-mini` (fast, cost-effective)
**Temperature**: 0.3 (consistent, predictable responses)
**API Key**: Set via `OPENAI_API_KEY` environment variable

### Cost Per Analysis

Approximate: $0.001 - $0.002 per job (GPT-4o mini pricing)

## Error Handling

If OpenAI analysis fails:
- JSON parsing error: Falls back to `viable: false` with error message
- API error: Logs and returns user-friendly error
- Network timeout: Caught and displayed to user

## Implementation Details

### JobViabilityService

```ruby
service = JobViabilityService.new(job_listing)
result = service.analyze!

# result contains:
# {
#   viable: true/false,
#   service_fit: string,
#   contact_info_found: string,
#   reasoning: string
# }
```

### Bulk Analysis

```ruby
result = JobViabilityService.bulk_analyze(limit: 50)

# result contains:
# {
#   analyzed: count,
#   viable: count of viable jobs
# }
```

## UI Integration

### Dashboard Button

Located in `/app/views/job_listings/index.html.erb`:

```erb
<button class="btn btn-primary" onclick="return confirm('Analyze job viability for up to 50 pending jobs?')">
  🤖 Analyze Job Viability
</button>
```

### Job Status Display

Jobs are categorized by `viable_post`:
- **nil** = Pending Analysis (gray)
- **true** = Viable Leads (green)
- **false** = Not Viable (red)

## Next Steps (Future Enhancements)

1. **Background Job Processing**: Use Rails job queue for bulk analysis
2. **Rate Limiting**: Add API throttling to stay within OpenAI limits
3. **Webhook Integration**: Real-time updates as jobs are analyzed
4. **Custom Prompt Tuning**: A/B test different evaluation criteria
5. **Contact Extraction**: Second prompt to extract actual contact info
6. **Audit Trail**: Log all viability decisions for manual review

## Testing

```ruby
# Test single analysis
job = JobListing.create(
  title: "Build E-Commerce Site",
  description: "Looking for custom Shopify store...",
  job_url: "https://upwork.com/jobs/123"
)

service = JobViabilityService.new(job)
result = service.analyze!

puts result[:viable] # Should be true or false
```

## Troubleshooting

**Q: Why did analysis fail?**
A: Check OPENAI_API_KEY is set. Verify job listing has title and description.

**Q: Why are all jobs marked not viable?**
A: Service prompt may be too strict. Review classification_snippet for details.

**Q: Can I re-analyze a job?**
A: Yes - re-running analyze will overwrite the previous viable_post value.

## Related Features

- **Contact Info Analysis**: `/analyze_contact_info` - Extracts email/phone contact details
- **Job Categorization**: Separates into Pending/Viable/Not Viable tabs

---

**Created**: November 2, 2025
**Feature**: AI-Powered Job Viability Scoring
**Status**: ✅ Ready for Testing
