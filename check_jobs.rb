require_relative 'config/environment'

puts "Checking job listings in database..."
total = JobListing.count
pending = JobListing.where(viable_post: nil).count
viable = JobListing.where(viable_post: true).count
not_viable = JobListing.where(viable_post: false).count

puts "Total: #{total}"
puts "Pending (viable_post = nil): #{pending}"
puts "Marked Viable: #{viable}"
puts "Marked Not Viable: #{not_viable}"

if pending > 0
  job = JobListing.where(viable_post: nil).first
  puts "\nFirst pending job:"
  puts "  ID: #{job.id}"
  puts "  Title: #{job.title&.truncate(60)}"
end
