class RunUpworkScraperJob < ApplicationJob
  queue_as :default

  def perform(scraper_id)
    scraper = Scraper.find_by(id: scraper_id)
    return unless scraper

    # Run Python scripts to scrape and then upload
    root = Rails.root.to_s
    env = { 'PYTHONUNBUFFERED' => '1' }

    begin
      # On macOS: open a new Terminal window and run the Python scripts interactively to allow manual login
      if RbConfig::CONFIG['host_os'] =~ /darwin/
        project_dir = root
        # Use rails runner to invoke the Ruby Selenium service interactively
        command = "cd #{project_dir}; bin/rails runner 'UpworkScraper.run_interactive(max_hours_old: 24, max_pages: 3)'"
        osa = %(tell application "Terminal" to do script "#{command.gsub('"','\\\"')}" )
        system('osascript', '-e', osa)
      else
        # Fallback (non-macOS): just run via rails runner (may not show a browser if headless)
        system(env, 'bin/rails', 'runner', "UpworkScraper.run_interactive(max_hours_old: 24, max_pages: 3)")
      end

      # After scripts complete, update status metrics (best-effort)
      scraper.update(status: 'paused', last_run_at: Time.current, total_leads_collected: JobListing.where(source: scraper.name.downcase).count)
    rescue => e
      Rails.logger.error("Upwork scraper failed: #{e.class}: #{e.message}")
      scraper.update(status: 'error')
      raise
    end
  end
end
