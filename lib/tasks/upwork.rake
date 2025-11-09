namespace :scrapers do
  namespace :upwork do
    desc "Run Ruby Selenium Upwork scraper interactively"
    task :run_ruby, [:hours, :pages] => :environment do |t, args|
      hours = (args[:hours] || 24).to_i
      pages = (args[:pages] || 3).to_i
      UpworkScraper.run_interactive(max_hours_old: hours, max_pages: pages)
    end

    desc "Import scraped jobs JSON and upsert JobListings. Usage: rake scrapers:upwork:import_json[path,to,json,limit]"
    task :import_json, [:path, :limit] => :environment do |t, args|
      require 'json'
      path = args[:path] || Rails.root.join('upwork_ai', 'scraped_jobs.json')
      limit = args[:limit]&.to_i

      abort("File not found: #{path}") unless File.exist?(path)
      data = JSON.parse(File.read(path))
      imported = 0
      data.each do |item|
        break if limit && imported >= limit
        job_url = item['url'] || item['job_url']
        post_date = item['post_date']
        next if job_url.blank?

        jl = JobListing.find_or_initialize_by(job_url: job_url)
        jl.source ||= 'upwork'
        jl.listing_type ||= 'job'
        jl.post_date ||= post_date
        jl.fresh = true if jl.new_record?
        if jl.changed?
          jl.save!
          imported += 1
        end
      end
      puts "Imported/updated #{imported} listings from #{path}"
    end
  end
end
