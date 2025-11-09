# frozen_string_literal: true

class ScraperLauncher
  def self.launch_upwork(hours: 24, pages: 3, scraper_id: nil)
    root = Rails.root.to_s
    # Build a DATABASE_URL from the current Rails DB config so Python writes to the same DB
    db_cfg = ActiveRecord::Base.connection_db_config.configuration_hash
  db_scheme = 'postgresql+pg8000'
    db_user = db_cfg[:username]
    db_pass = db_cfg[:password]
    db_host = db_cfg[:host] || 'localhost'
    db_port = db_cfg[:port] || 5432
    db_name = db_cfg[:database]
    auth = db_user.present? ? (db_pass.present? ? "#{db_user}:#{db_pass}@" : "#{db_user}@") : ""
    database_url = "#{db_scheme}://#{auth}#{db_host}:#{db_port}/#{db_name}"

    # Detect a local Chrome binary (common bundles) and export CHROME_BIN for Python
    chrome_candidates = [
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Google Chrome 2.app/Contents/MacOS/Google Chrome",
      "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
      "/Applications/Chromium.app/Contents/MacOS/Chromium",
      "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
      "/opt/homebrew/bin/chromium",
      "/usr/local/bin/google-chrome",
      "/usr/bin/google-chrome"
    ]
    chrome_bin = chrome_candidates.find { |p| File.exist?(p) }
    if RbConfig::CONFIG['host_os'] =~ /darwin/
      # Run Python process in background without terminal visibility
      upwork_email = ENV['UPWORK_EMAIL']
      upwork_password = ENV['UPWORK_PASSWORD']
      extra_env = {}
      extra_env['UPWORK_EMAIL'] = upwork_email if upwork_email.present?
      extra_env['UPWORK_PASSWORD'] = upwork_password if upwork_password.present?

      env = {
        'DATABASE_URL' => database_url,
        'SCRAPER_ID' => scraper_id.to_s,
        'RAILS_BASE_URL' => "http://localhost:4242"  # Match the port from terminal context
      }.merge(extra_env)
      env['CHROME_BIN'] = chrome_bin if chrome_bin

      runner = File.join(root, 'script', 'run_upwork_scraper.sh')
      cmd = ["/bin/bash", runner, "--hours=#{hours}", "--pages=#{pages}"]

      # Spawn process in background, capture output to log file
      log_file = File.join(root, 'log', 'upwork_scraper.log')
      begin
        # Spawn with output redirected to log file
        spawn_options = {
          out: [log_file, 'a'],
          err: [log_file, 'a'],
          chdir: root
        }

        pid = Process.spawn(env, *cmd, spawn_options)
        Process.detach(pid)  # Don't wait for completion
        Rails.logger.info("ScraperLauncher: Started Python scraper with PID #{pid}")
        true
      rescue => e
        Rails.logger.error("ScraperLauncher background spawn failed: #{e.class}: #{e.message}")
        false
      end
    else
      # Fallback: run Python synchronously (not ideal)
  env = { 'DATABASE_URL' => database_url, 'SCRAPER_ID' => scraper_id.to_s }
      env['CHROME_BIN'] = chrome_bin if chrome_bin
      system(env, 'python3', '-m', 'pip', 'install', '-r', File.join(root, 'upwork_ai', 'requirements.txt'))
      system(env, 'python3', File.join(root, 'upwork_ai', 'run_upwork_latest.py'), "--hours=#{hours}", "--pages=#{pages}")
      true
    end
  rescue => e
    Rails.logger.error("ScraperLauncher failed: #{e.class}: #{e.message}")
    false
  end
end
