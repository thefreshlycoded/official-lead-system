# This file should ensure the existence of records required to run the application in every environment (production,
# development, test). The code here should be idempotent so that it can be executed at any point in every environment.
# The data can then be loaded with the bin/rails db:seed command (or created alongside the database with db:setup).
#
# Example:
#
#   ["Action", "Comedy", "Drama", "Horror"].each do |genre_name|
#     MovieGenre.find_or_create_by!(name: genre_name)
#   end

require 'faker'

sources = %w[upwork craigslist linkedin custom]
listing_types = %w[job gig project]

# Seed Scrapers
scrapers = [
  { name: "Upwork", kind: "automated", status: "running", last_run_at: 1.hour.ago, total_leads_collected: 1200 }
]

scrapers.each do |attrs|
  Scraper.find_or_create_by!(name: attrs[:name]) do |s|
    s.kind = attrs[:kind]
    s.status = attrs[:status]
    s.last_run_at = attrs[:last_run_at]
    s.total_leads_collected = attrs[:total_leads_collected]
  end
end

# Seed Campaigns
Campaign.find_or_create_by!(name: "Q4 React Outreach") do |c|
  c.description = "Focus on React opportunities from Upwork and LinkedIn"
  c.status = :active
  c.leads_count = 45
  c.launched_at = 3.days.ago
end

Campaign.find_or_create_by!(name: "Upwork Quick Wins") do |c|
  c.description = "Low effort, high return quick proposals"
  c.status = :draft
  c.leads_count = 12
end

puts "Seeded #{Scraper.count} scrapers and #{Campaign.count} campaigns"
