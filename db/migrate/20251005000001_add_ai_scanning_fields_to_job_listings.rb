class AddAiScanningFieldsToJobListings < ActiveRecord::Migration[8.0]
  def change
    # AI Analysis Fields
    add_column :job_listings, :viable_post, :boolean, default: nil
    add_column :job_listings, :viable_post_human, :boolean, default: nil
    add_column :job_listings, :scanned_for_relevance, :boolean, default: false
    add_column :job_listings, :scanned_for_company_details, :boolean, default: false
    add_column :job_listings, :ai_relevance_score, :decimal, precision: 3, scale: 2
    add_column :job_listings, :ai_relevance_reasoning, :text
    add_column :job_listings, :company_research_completed, :boolean, default: false
    add_column :job_listings, :company_research_notes, :text

    # Timestamps for tracking when reviews happened
    add_column :job_listings, :human_reviewed_at, :datetime
    add_column :job_listings, :ai_scanned_at, :datetime

    # Add indexes for performance
    add_index :job_listings, :viable_post
    add_index :job_listings, :viable_post_human
    add_index :job_listings, :scanned_for_relevance
    add_index :job_listings, :scanned_for_company_details
    add_index :job_listings, :ai_relevance_score
  end
end