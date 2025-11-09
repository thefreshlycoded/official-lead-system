class JobListing < ApplicationRecord
  # Basic validations
  validates :job_url, presence: true, uniqueness: true

  scope :relevant, -> { where(relevance: true) }
  scope :fresh, -> { where(fresh: true) }

  enum :status, { new_lead: 0, contacted: 1, qualified: 2, lost: 3, closed: 4 }

  # New scopes for AI scanning and human review
  scope :unscanned_for_relevance, -> { where(scanned_for_relevance: false) }
  scope :unscanned_for_company_details, -> { where(scanned_for_company_details: false) }
  scope :viable_posts, -> { where(viable_post: true) }
  scope :non_viable_posts, -> { where(viable_post: false) }
  scope :pending_review, -> { where(viable_post: nil) }

  # Human review scopes
  scope :human_reviewed, -> { where.not(viable_post_human: nil) }
  scope :pending_human_review, -> { where(viable_post_human: nil) }
  scope :human_viable, -> { where(viable_post_human: true) }
  scope :human_not_viable, -> { where(viable_post_human: false) }

  # Comparison scopes for AI validation
  scope :ai_human_agreement, -> { where('viable_post = viable_post_human') }
  scope :ai_human_disagreement, -> { where('viable_post != viable_post_human AND viable_post IS NOT NULL AND viable_post_human IS NOT NULL') }

  # Store arrays as JSON in text columns
  def emails
    raw = read_attribute(:emails)
    return [] if raw.blank?
    return raw if raw.is_a?(Array)
    JSON.parse(raw)
  rescue JSON::ParserError
    []
  end

  def emails=(value)
    arr = Array(value).compact_blank
    write_attribute(:emails, arr.to_json)
  end

  def phones
    raw = read_attribute(:phones)
    return [] if raw.blank?
    return raw if raw.is_a?(Array)
    JSON.parse(raw)
  rescue JSON::ParserError
    []
  end

  def phones=(value)
    arr = Array(value).compact_blank
    write_attribute(:phones, arr.to_json)
  end

  def contacts_present?
    emails.any? || phones.any? || contact_email.present? || contact_phone.present? || contact_name.present?
  end

  def display_source
    source.presence || "upwork"
  end

  # AI scanning status methods
  def needs_relevance_scan?
    !scanned_for_relevance
  end

  def needs_company_research?
    viable_post == true && !scanned_for_company_details
  end

  def needs_human_review?
    viable_post_human.nil?
  end

  def ai_human_match?
    return nil if viable_post.nil? || viable_post_human.nil?
    viable_post == viable_post_human
  end

  # Update methods
  def mark_as_scanned_for_relevance!(viable:, score: nil, reasoning: nil)
    update!(
      scanned_for_relevance: true,
      viable_post: viable,
      ai_relevance_score: score,
      ai_relevance_reasoning: reasoning,
      ai_scanned_at: Time.current
    )
  end

  def mark_human_review!(viable:)
    update!(
      viable_post_human: viable,
      human_reviewed_at: Time.current
    )
  end

  def mark_company_research_complete!(notes: nil)
    update!(
      scanned_for_company_details: true,
      company_research_completed: true,
      company_research_notes: notes
    )
  end

  def as_json(options = {})
    super(options).merge(
      "emails" => emails,
      "phones" => phones
    )
  end

  # Check if this job needs human review (hasn't been reviewed yet)
  def needs_human_review?
    viable_post_human.nil?
  end

  # Check if job has any contact information
  def contacts_present?
    emails.any? || phones.any? || contact_email.present? || contact_phone.present?
  end

  # Display source with proper formatting
  def display_source
    source&.capitalize || 'Unknown'
  end

  # Check if AI and human reviews match
  def ai_human_match?
    return nil if viable_post.nil? || viable_post_human.nil?
    viable_post == viable_post_human
  end

  # Translate the scraped `posted_time` string (e.g. "2 minutes ago") into
  # an absolute timestamp using the PostedTimeParser utility.
  def parsed_posted_time(reference_time: nil)
    ref_time = reference_time || created_at || Time.zone.now
    PostedTimeParser.parse(posted_time, reference_time: ref_time)
  end

  # Resolve the most accurate posted timestamp we have for display purposes.
  def posted_at(reference_time: nil)
    ref_time = reference_time || created_at || Time.zone.now
    parsed_posted_time(reference_time: ref_time) ||
      PostedTimeParser.parse(post_date, reference_time: ref_time) ||
      created_at || ref_time
  end
end
