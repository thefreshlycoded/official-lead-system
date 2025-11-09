# Job Viability Analysis Feature - Implementation Summary

## Overview
Implemented an AI-powered job viability scoring system using OpenAI that evaluates Upwork job listings on two criteria:
1. **Service Fit** - Does it match Always Coded Fresh's services?
2. **Contact Leakage** - Are there enough company details to research them?

## Files Modified

### 1. **Controller** (`app/controllers/job_listings_controller.rb`)
Added new action `analyze_job_viability` that:
- Analyzes individual jobs or bulk processes pending listings
- Calls `JobViabilityService` for AI evaluation
- Updates `viable_post` field with viability determination
- Stores reasoning in `classification_snippet`

### 2. **Routes** (`config/routes.rb`)
Added routes for the new action:
```ruby
post :analyze_job_viability  # Both member and collection routes
```

### 3. **Views** (`app/views/job_listings/index.html.erb`)
Added button alongside existing "Analyze Contact Info":
```erb
<button class="btn btn-primary">🤖 Analyze Job Viability</button>
```
- Blue button for distinction from contact analysis (green)
- Confirmation dialog before processing
- Supports limit parameter (default 50 jobs)

### 4. **Service** (`app/services/job_viability_service.rb`) - NEW FILE
Core analysis logic:

**Key Methods:**
- `analyze!` - Analyzes single job using OpenAI GPT-4o-mini
- `bulk_analyze` - Batch processes pending jobs with rate limiting
- Private `build_prompt` - Constructs contextual prompt with job data

**Prompt Strategy:**
- Profiles Always Coded Fresh services upfront
- Evaluates both service fit AND contact information presence
- Returns JSON with viability decision and reasoning
- Handles JSON parsing gracefully with error recovery

### 5. **Gemfile**
Added dependency:
```ruby
gem "ruby-openai"
```

## Workflow

### Single Job Analysis
1. User clicks "🤖 Analyze Job Viability" on job listing detail page
2. `analyze_job_viability#show` calls `JobViabilityService.new(job).analyze!`
3. Service sends job title/description to OpenAI with viability criteria
4. OpenAI returns JSON with viability decision
5. Job updated with `viable_post` boolean and reasoning
6. User redirected with success/failure message

### Bulk Analysis
1. User clicks "🤖 Analyze Job Viability" on index page
2. `analyze_job_viability` (collection) processes up to 50 pending jobs
3. Service loops through jobs with 0.5s delay between API calls (rate limiting)
4. Returns summary: "Analyzed X jobs. Found Y viable opportunities."
5. User redirected to index with results

## Data Persistence

**Updated Fields:**
- `viable_post` (boolean) - Set to true/false based on AI analysis
- `classification_snippet` (text) - Stores service fit + contact info details

Example classification_snippet:
```
Service Fit: Web development project, matches our custom dev services. Contact Info: Company name (XYZ Corp), website (xyz.com), and email contact visible.
```

## OpenAI Integration

**Model:** `gpt-4o-mini` (cost-effective, fast for classification)

**Prompt Design:**
- Clear business context (Always Coded Fresh profile)
- Two explicit criteria for evaluation
- JSON response format for easy parsing
- Includes actual job title/description/URL

**Error Handling:**
- JSON parsing errors caught and logged
- API errors propagate to controller
- Graceful fallback in bulk processing

## Next Steps for Enhancement

**Optional Future Features:**
1. **Contact Research Prompt** - Secondary OpenAI call to extract company details from job listing text
2. **Confidence Scoring** - Add scoring (0-100) for viability confidence
3. **Categorization** - Categorize non-viable reasons (budget, service mismatch, insufficient info, etc.)
4. **Background Jobs** - Use Solid Queue for async processing of large batches
5. **A/B Testing** - Compare AI scores with manual human reviews to refine prompt

## Testing the Feature

```bash
# Install gem
bundle install

# Single job (on /job_listings/:id page):
POST /job_listings/:id/analyze_job_viability

# Bulk (on /job_listings page, click button):
POST /job_listings/analyze_job_viability?limit=50
```

Expected response:
```json
{
  "viable": true/false,
  "service_fit": "Description of service match",
  "contact_info_found": "What company details are visible",
  "reasoning": "Why viable or not viable"
}
```
