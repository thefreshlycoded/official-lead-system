#!/usr/bin/env ruby

# Quick script to check scraped data in Rails
require_relative '../config/environment'

puts "🔍 Checking scraped job data in Rails..."
puts "=" * 50

total_jobs = JobListing.count
upwork_jobs = JobListing.where(source: 'upwork').count
recent_upwork = JobListing.where(source: 'upwork').order(created_at: :desc).limit(5)

puts "📊 Database Stats:"
puts "  Total jobs: #{total_jobs}"
puts "  Upwork jobs: #{upwork_jobs}"
puts "  By source: #{JobListing.group(:source).count.to_h}"
puts ""

puts "🆕 Recent Upwork Jobs:"
recent_upwork.each_with_index do |job, i|
  title = job.title&.strip || "Untitled"
  title = title[0..60] + "..." if title.length > 60
  time_ago = Time.current - job.created_at
  if time_ago < 3600
    time_str = "#{(time_ago / 60).to_i}m ago"
  elsif time_ago < 86400
    time_str = "#{(time_ago / 3600).to_i}h ago"
  else
    time_str = job.created_at.strftime("%m/%d %H:%M")
  end

  puts "  #{i+1}. #{title} (#{time_str})"
end

puts ""
puts "✅ Rails can access the scraped data!"
puts "🌐 Visit http://localhost:3000 to see the dashboard"