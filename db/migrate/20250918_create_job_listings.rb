class CreateJobListings < ActiveRecord::Migration[7.1]
  def change
    create_table :job_listings do |t|
      t.string :job_url, null: false
      t.string :title
      t.text :description
      t.string :location
      t.string :post_date
      t.string :posted_time
      t.string :job_link
      t.boolean :fresh, default: true

      # Source/meta
      t.string :source, default: "upwork"
      t.string :listing_type, default: "job"

      # AI classification fields
      t.boolean :relevance
      t.boolean :website_present
      t.text :website_url
      t.string :website_type
      t.text :classification_snippet

      # Contact enrichment
      t.text :emails, default: "[]"
      t.text :phones, default: "[]"
      t.string :facebook
      t.string :twitter
      t.string :linkedin
      t.string :instagram
      t.string :city
      t.string :state
      t.string :country
      t.string :industry
      t.string :owner_name
      t.boolean :manual_review, default: false

      # Generated outreach
      t.text :email_pitch
      t.text :sms_pitch

      t.timestamps
    end

    add_index :job_listings, :job_url, unique: true
    add_index :job_listings, :relevance
    add_index :job_listings, :source
    add_index :job_listings, :listing_type
  end
end
