require 'openai'

class JobViabilityService
  ALWAYS_CODED_FRESH_PROFILE = <<~PROMPT
    Always Coded Fresh is a digital agency specializing in:
    - Custom Web Development (full-stack, modern frameworks)
    - Web Design (responsive, UX-focused)
    - E-Commerce Solutions (online stores, payment integration)
    - SEO Services (search engine optimization)
    - Digital Marketing Strategy (paid ads, funnels, analytics)
    - Video Editing & Post-Production (long-form, shorts, ads)
    - Graphic, Brand & Social Content Design (thumbnails, decks, social media assets)

    They work with startups and enterprises of all sizes and are based in New York.
  PROMPT

  VIABILITY_PROMPT_TEMPLATE = <<~PROMPT
    You are a lead qualification specialist for Always Coded Fresh, a digital agency.

    #{ALWAYS_CODED_FRESH_PROFILE}

    Evaluate if this Upwork job listing is worth pursuing based on THREE STRICT criteria:

    1. SERVICE FIT: Must CLEARLY match at least one of our core services. Be strict - vague mentions or tangentially related work don't qualify.

    2. CONTACT LEAKAGE: Must provide actionable contact/research pathways (company name, website URL, social media profiles, email, phone, or specific person name).

    3. COMPANY DETAILS: Must have CONCRETE company information - at minimum ONE of:
       - Specific company/business name (not just "my company" or industry descriptions)
       - Website URL or domain name
       - Social media profiles with actual handles/URLs
       - Contact person with name and role

    CRITICAL: Generic descriptions like "consulting firm" or "startup" without actual company names do NOT qualify as company details.

    Only mark viable=true if ALL THREE criteria are strictly met. When in doubt, mark as NOT viable.

    Extract ALL available company details from the job posting. Look for:
    - Explicit company names (not just business type descriptions)
    - Complete website URLs (any domain mentions, even partial)
    - Social media handles/URLs with actual profile names
    - Specific contact person names and roles
    - Direct contact information (email, phone)
    - Location details that help identify the business

    Respond ONLY with valid JSON (no markdown, no code blocks):
    {
      "viable": true/false,
      "service_fit": "description of how it fits our services",
      "contact_info_found": "summary of what contact details are available",
      "company_details_present": "whether actual company details are mentioned",
      "reasoning": "brief explanation of viability decision covering all three criteria",
      "company_details": {
        "company_name": "extracted company name or null",
        "website_url": "full website URL (with https://) or null",
        "industry": "specific business type/industry or null",
        "location": {
          "city": "city name or null",
          "state": "state/province or null",
          "country": "country or null",
          "full_address": "complete address if mentioned or null"
        },
        "contact_person": {
          "name": "contact person name or null",
          "role": "job title/role or null",
          "email": "email address or null",
          "phone": "phone number or null"
        },
        "social_media": {
          "facebook": "full Facebook URL or null",
          "instagram": "full Instagram URL or null",
          "linkedin": "full LinkedIn URL or null",
          "twitter": "full Twitter URL or null",
          "youtube": "full YouTube URL or null",
          "tiktok": "full TikTok URL or null"
        },
        "business_info": {
          "size": "company size indicator (startup/small/medium/enterprise) or null",
          "founded": "founding year or null",
          "description": "brief business description if mentioned or null"
        }
      }
    }

    JOB LISTING:
    Title: <%= @job_listing.title %>
    Description: <%= @job_listing.description %>
    URL: <%= @job_listing.job_url %>
  PROMPT

  def initialize(job_listing)
    @job_listing = job_listing
    @client = OpenAI::Client.new(access_token: ENV['OPENAI_API_KEY'])
  end

  def analyze!
    # Build the prompt with actual job data
    prompt = build_prompt

    Rails.logger.info "Analyzing job viability for: #{@job_listing.title}"

    # Call OpenAI API
    response = @client.chat(
      parameters: {
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3
      }
    )

    # Parse response
    result_text = response.dig('choices', 0, 'message', 'content')&.strip

    Rails.logger.info "OpenAI Response: #{result_text}"

    # Extract JSON from response (in case it includes markdown code blocks)
    json_match = result_text.match(/\{[\s\S]*\}/)
    json_str = json_match ? json_match[0] : result_text

    result = JSON.parse(json_str)

    # Extract company details from the analysis
    company_details = result['company_details'] || {}
    location_info = company_details['location'] || {}
    contact_person = company_details['contact_person'] || {}
    social_media = company_details['social_media'] || {}

    # Prepare update attributes
    update_attrs = {
      viable_post: result['viable'],
      classification_snippet: "Service Fit: #{result['service_fit']}. Contact Info: #{result['contact_info_found']}"
    }

    # Basic company details
    update_attrs[:company_name] = company_details['company_name'] if company_details['company_name'].present?
    update_attrs[:website_url] = company_details['website_url'] if company_details['website_url'].present?
    update_attrs[:industry] = company_details['industry'] if company_details['industry'].present?

    # Location details
    update_attrs[:city] = location_info['city'] if location_info['city'].present?
    update_attrs[:state] = location_info['state'] if location_info['state'].present?
    update_attrs[:country] = location_info['country'] if location_info['country'].present?

    # Contact person details
    update_attrs[:contact_name] = contact_person['name'] if contact_person['name'].present?
    update_attrs[:contact_email] = contact_person['email'] if contact_person['email'].present?
    update_attrs[:contact_phone] = contact_person['phone'] if contact_person['phone'].present?
    update_attrs[:contact_role] = contact_person['role'] if contact_person['role'].present?

    # Social media details
    update_attrs[:facebook] = social_media['facebook'] if social_media['facebook'].present?
    update_attrs[:instagram] = social_media['instagram'] if social_media['instagram'].present?
    update_attrs[:linkedin] = social_media['linkedin'] if social_media['linkedin'].present?
    update_attrs[:twitter] = social_media['twitter'] if social_media['twitter'].present?

    # Store the complete JSON analysis for reference
    update_attrs[:viability_analysis] = result

    # Update job listing with all extracted information
    @job_listing.update(update_attrs)

    result
  rescue JSON::ParserError => e
    Rails.logger.error "Failed to parse OpenAI response: #{result_text}"
    Rails.logger.error "JSON Parse Error: #{e.message}"

    error_result = {
      viable: false,
      service_fit: 'Error parsing response',
      contact_info_found: 'N/A',
      company_details_present: 'N/A',
      reasoning: 'Failed to analyze due to parsing error',
      company_details: {}
    }

    # Store error result in database
    @job_listing.update(
      viable_post: false,
      classification_snippet: "Analysis failed: JSON parsing error",
      viability_analysis: error_result
    )

    error_result
  rescue => e
    Rails.logger.error "Job viability analysis error: #{e.message}"

    # Store general error in database
    general_error_result = {
      viable: false,
      service_fit: 'Analysis failed',
      contact_info_found: 'N/A',
      company_details_present: 'N/A',
      reasoning: "System error: #{e.message}",
      company_details: {}
    }

    @job_listing.update(
      viable_post: false,
      classification_snippet: "Analysis failed: #{e.message}",
      viability_analysis: general_error_result
    )

    general_error_result
  end

  def self.bulk_analyze(limit: 50)
    # Find pending jobs (viable_post is nil)
    pending_jobs = JobListing.where(viable_post: nil).limit(limit)

    viable_count = 0
    analyzed_count = 0

    pending_jobs.each do |job|
      begin
        analyzer = new(job)
        result = analyzer.analyze!

        viable_count += 1 if result[:viable]
        analyzed_count += 1

        # Small delay to avoid rate limiting
        sleep 0.5
      rescue => e
        Rails.logger.error "Error analyzing job #{job.id}: #{e.message}"
        # Continue with next job instead of failing
        next
      end
    end

    {
      analyzed: analyzed_count,
      viable: viable_count
    }
  end

  private

  def build_prompt
    prompt = VIABILITY_PROMPT_TEMPLATE.dup

    prompt.gsub!('<%= @job_listing.title %>', @job_listing.title.to_s)
    prompt.gsub!('<%= @job_listing.description %>', @job_listing.description.to_s)
    prompt.gsub!('<%= @job_listing.job_url %>', @job_listing.job_url.to_s)

    prompt
  end
end
