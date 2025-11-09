class ContactAnalyzerService
  def initialize(job_listing)
    @job_listing = job_listing
  end

  def analyze!
    return handle_missing_description unless @job_listing.description.present?

    analysis_result = analyze_description(@job_listing.description, @job_listing.title)

    @job_listing.update!(
      emails: analysis_result[:emails],
      phones: analysis_result[:phones],
      website_url: analysis_result[:websites].first,
      company_name: analysis_result[:company_name],
      viable_post: analysis_result[:has_contact_info],
      classification_snippet: analysis_result[:analysis_summary],
      scanned_for_company_details: true
    )

    analysis_result[:has_contact_info]
  end

  def self.bulk_analyze(limit: 50)
  jobs = JobListing.where(scanned_for_company_details: [false, nil])
           .order(created_at: :desc)
           .limit(limit)

    analyzed_count = 0
    viable_count = 0

  jobs.each do |job|
      analyzer = new(job)
      if analyzer.analyze!
        viable_count += 1
      end
      analyzed_count += 1
    rescue => e
      Rails.logger.error "Error analyzing job #{job.id}: #{e.message}"
    end

    { analyzed: analyzed_count, viable: viable_count }
  end

  private

  def handle_missing_description
    @job_listing.update!(
      viable_post: false,
      scanned_for_company_details: true,
      classification_snippet: "No job description available to analyze",
      emails: [],
      phones: [],
      website_url: nil,
      company_name: nil
    )

    false
  end

  def analyze_description(description, title = nil)
    text = [title, description].compact.join(" ")

    # Extract emails
    emails = extract_emails(text)

    # Extract phones
    phones = extract_phones(text)

    # Extract websites
    websites = extract_websites(text)

    # Extract company name
    company_name = extract_company_name(text)

    # Determine if contact info is present
    has_contact_info = emails.any? || phones.any? || websites.any?

    # Create analysis summary
    summary_parts = []
    summary_parts << "#{emails.size} email(s)" if emails.any?
    summary_parts << "#{phones.size} phone(s)" if phones.any?
    summary_parts << "#{websites.size} website(s)" if websites.any?
    summary_parts << "company: #{company_name}" if company_name.present?

    analysis_summary = summary_parts.any? ? summary_parts.join("; ") : "No contact information found"

    {
      emails: emails,
      phones: phones,
      websites: websites,
      company_name: company_name,
      has_contact_info: has_contact_info,
      analysis_summary: analysis_summary
    }
  end

  def extract_emails(text)
    email_patterns = [
      /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/,
      /\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/,
      /\b[A-Za-z0-9._%+-]+\s*\[\s*at\s*\]\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/,
      /\b[A-Za-z0-9._%+-]+\s*\(\s*at\s*\)\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/
    ]

    emails = []
    email_patterns.each do |pattern|
      matches = text.scan(pattern)
      emails.concat(matches.map { |match| match.gsub(/\s+/, '').gsub(/[\[\]()]/, '').gsub(/\s*at\s*/, '@') })
    end

    emails.uniq.select { |email| valid_email?(email) }
  end

  def extract_phones(text)
    phone_patterns = [
      /\b(?:\+?1[-.\s]?)?(?:\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}\b/,
      /\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b/,
      /\b\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b/,
      /\b1[-.\s]?[0-9]{3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b/
    ]

    phones = []
    phone_patterns.each do |pattern|
      matches = text.scan(pattern)
      phones.concat(matches.map { |match| normalize_phone(match) })
    end

    phones.uniq.select { |phone| valid_phone?(phone) }
  end

  def extract_websites(text)
    website_patterns = [
      /https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?/,
      /www\.(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?/,
      /(?:^|\s)([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:\s|$)/
    ]

    websites = []
    website_patterns.each do |pattern|
      matches = text.scan(pattern)
      websites.concat(matches.flatten.map { |match| normalize_website(match.strip) })
    end

    websites.uniq.select { |website| valid_website?(website) }
  end

  def extract_company_name(text)
    # Look for company indicators
    company_patterns = [
      /(?:company|business|agency|firm|corp|corporation|inc|llc|ltd|co\.)\s*:?\s*([A-Za-z0-9\s&.-]{2,30})/i,
      /(?:we are|i am from|working for|employed by)\s+([A-Za-z0-9\s&.-]{2,30})/i,
      /([A-Za-z0-9\s&.-]{2,30})\s+(?:company|business|agency|firm|corp|corporation|inc|llc|ltd)/i
    ]

    company_patterns.each do |pattern|
      match = text.match(pattern)
      if match && match[1]
        company = match[1].strip.gsub(/[^\w\s&.-]/, '')
        return company if company.length > 2 && company.length < 50
      end
    end

    nil
  end

  def valid_email?(email)
    email.present? &&
    email.include?('@') &&
    email.match?(/\A[^@\s]+@[^@\s]+\z/) &&
    !email.match?(/\.(jpg|jpeg|png|gif|pdf|doc|docx)$/i)
  end

  def valid_phone?(phone)
    digits = phone.gsub(/\D/, '')
    digits.length >= 10 && digits.length <= 15
  end

  def valid_website?(website)
    website.present? &&
    website.length > 5 &&
    (website.include?('.com') || website.include?('.org') || website.include?('.net') ||
     website.include?('.co') || website.include?('.io') || website.match?(/\.[a-z]{2,4}$/i))
  end

  def normalize_phone(phone)
    phone.gsub(/\D/, '').gsub(/^1/, '') # Remove non-digits and leading 1
  end

  def normalize_website(website)
    website = website.downcase
    website = "http://#{website}" unless website.start_with?('http')
    website
  end
end