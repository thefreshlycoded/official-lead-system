# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.0].define(version: 2025_11_07_203805) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "pg_catalog.plpgsql"

  create_table "campaigns", force: :cascade do |t|
    t.string "name", null: false
    t.text "description"
    t.integer "status", default: 0
    t.integer "leads_count", default: 0
    t.datetime "launched_at"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["status"], name: "index_campaigns_on_status"
  end

  create_table "job_listings", force: :cascade do |t|
    t.string "job_url", null: false
    t.string "title"
    t.text "description"
    t.string "location"
    t.string "post_date"
    t.string "posted_time"
    t.string "job_link"
    t.boolean "fresh", default: true
    t.string "source", default: "upwork"
    t.string "listing_type", default: "job"
    t.boolean "relevance"
    t.boolean "website_present"
    t.text "website_url"
    t.string "website_type"
    t.text "classification_snippet"
    t.text "emails", default: "[]"
    t.text "phones", default: "[]"
    t.string "facebook"
    t.string "twitter"
    t.string "linkedin"
    t.string "instagram"
    t.string "city"
    t.string "state"
    t.string "country"
    t.string "industry"
    t.string "owner_name"
    t.boolean "manual_review", default: false
    t.text "email_pitch"
    t.text "sms_pitch"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.string "company_name"
    t.string "contact_name"
    t.string "contact_email"
    t.string "contact_phone"
    t.string "contact_role"
    t.datetime "last_contacted_at"
    t.string "contact_method"
    t.integer "status", default: 0
    t.string "project_type"
    t.integer "budget_min"
    t.integer "budget_max"
    t.string "timezone"
    t.boolean "viable_post"
    t.boolean "viable_post_human"
    t.boolean "scanned_for_relevance", default: false
    t.boolean "scanned_for_company_details", default: false
    t.decimal "ai_relevance_score", precision: 3, scale: 2
    t.text "ai_relevance_reasoning"
    t.boolean "company_research_completed", default: false
    t.text "company_research_notes"
    t.datetime "human_reviewed_at"
    t.datetime "ai_scanned_at"
    t.json "viability_analysis"
    t.index ["ai_relevance_score"], name: "index_job_listings_on_ai_relevance_score"
    t.index ["job_url"], name: "index_job_listings_on_job_url", unique: true
    t.index ["listing_type"], name: "index_job_listings_on_listing_type"
    t.index ["project_type"], name: "index_job_listings_on_project_type"
    t.index ["relevance"], name: "index_job_listings_on_relevance"
    t.index ["scanned_for_company_details"], name: "index_job_listings_on_scanned_for_company_details"
    t.index ["scanned_for_relevance"], name: "index_job_listings_on_scanned_for_relevance"
    t.index ["source"], name: "index_job_listings_on_source"
    t.index ["status"], name: "index_job_listings_on_status"
    t.index ["viable_post"], name: "index_job_listings_on_viable_post"
    t.index ["viable_post_human"], name: "index_job_listings_on_viable_post_human"
  end

  create_table "scrapers", force: :cascade do |t|
    t.string "name", null: false
    t.string "kind", default: "automated"
    t.string "status", default: "setup"
    t.datetime "last_run_at"
    t.integer "total_leads_collected", default: 0
    t.boolean "enabled", default: true
    t.text "schedule"
    t.text "last_result"
    t.text "config_json"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["enabled"], name: "index_scrapers_on_enabled"
    t.index ["name"], name: "index_scrapers_on_name", unique: true
    t.index ["status"], name: "index_scrapers_on_status"
  end
end
