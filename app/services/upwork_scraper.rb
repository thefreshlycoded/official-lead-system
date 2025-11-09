# frozen_string_literal: true

require 'selenium-webdriver'

class UpworkScraper
  JOBS_URL_TEMPLATE = 'https://www.upwork.com/nx/search/jobs/?q=www&sort=recency&page=%{page}&per_page=50'
  WAIT_TIMEOUT = 15

  def self.run_interactive(max_hours_old: 24, max_pages: 3)
    new.run_interactive(max_hours_old:, max_pages:)
  end

  def initialize
    @driver = nil
  end

  def run_interactive(max_hours_old:, max_pages:)
    setup_driver
    manual_login
    urls = collect_recent_job_urls(max_hours_old:, max_pages:)
    urls.each { |u| scrape_and_upsert(u[:url], u[:post_date]) }
  ensure
    @driver&.quit
  end

  private

  def setup_driver
    opts = Selenium::WebDriver::Chrome::Options.new
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1280,900')
    @driver = Selenium::WebDriver.for(:chrome, options: opts)
    @wait = Selenium::WebDriver::Wait.new(timeout: WAIT_TIMEOUT)
  end

  def manual_login
    login_url = 'https://www.upwork.com/ab/account-security/login'
    @driver.navigate.to(login_url)
    # Pause here for manual login
    Selenium::WebDriver::Wait.new(timeout: 300).until do
      @driver.current_url.include?('/home') || @driver.current_url.include?('/nx/search/jobs')
    end
  end

  def collect_recent_job_urls(max_hours_old:, max_pages:)
    page = 1
    results = []
    consecutive_old = 0
    limit_old = 5

    while page <= max_pages
      url = format(JOBS_URL_TEMPLATE, page: page)
      @driver.navigate.to(url)
      sleep 2
      job_links = @driver.find_elements(css: "article[data-test='JobTile'] h2 a")
      dates = @driver.find_elements(css: "article[data-test='JobTile'] small[data-test='job-pubilshed-date'] span:last-child")
      break if job_links.empty? || dates.empty?

      job_links.zip(dates).each do |a, date_el|
        href = a.attribute('href')
        post_date_str = date_el.text
        age_hours = age_in_hours(post_date_str)
        if age_hours >= max_hours_old
          consecutive_old += 1
          return results if consecutive_old >= limit_old
          next
        end
        consecutive_old = 0
        results << { url: href, post_date: post_date_str }
      end

      page += 1
    end

    results
  end

  def age_in_hours(label)
    s = label.to_s.downcase
    return 0 if s.include?('just now') || s.include?('seconds')
    if s.include?('minute')
      s.to_i / 60.0
    elsif s.include?('hour')
      s.to_i.to_f
    elsif s.include?('yesterday')
      24.0
    elsif s.include?('day')
      s.to_i * 24.0
    elsif s.include?('week')
      s.to_i * 24.0 * 7
    elsif s.include?('month')
      s.to_i * 24.0 * 30
    else
      0.0
    end
  end

  def scrape_and_upsert(job_url, post_date)
    @driver.navigate.to(job_url)
    sleep 2
    title_el = safe_find(css: ".job-details-content h4")
    desc_el = safe_find(css: ".job-details-content [data-test='Description']")
    location_el = safe_find(css: ".job-details-content [data-test='LocationLabel'] span")
    posted_el = safe_find(css: ".job-details-content [data-test='PostedOn'] span")
    link_el = safe_find(css: ".job-details-content [data-test='Description'] a")

    attrs = {
      job_url: job_url,
      title: title_el&.text,
      description: desc_el&.text,
      location: location_el&.text,
      posted_time: posted_el&.text,
      job_link: link_el&.attribute('href'),
      post_date: post_date,
      fresh: false,
      source: 'upwork',
      listing_type: 'job'
    }

    jl = JobListing.find_or_initialize_by(job_url: job_url)
    jl.assign_attributes(attrs)
    jl.save!
  end

  def safe_find(**kw)
    @driver.find_element(**kw)
  rescue Selenium::WebDriver::Error::NoSuchElementError
    nil
  end
end
