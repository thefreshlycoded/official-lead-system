class ScrapersController < ApplicationController
  protect_from_forgery except: [:run]

  def index
    @scrapers = Scraper.order(:name)
  end

  def show
    @scraper = Scraper.find(params[:id])
    @recent_leads = JobListing.where(source: @scraper.name.downcase).order(created_at: :desc).limit(20)
    if @scraper.last_run_at
      @new_since_last_run = JobListing.where(source: @scraper.name.downcase).where("created_at >= ?", @scraper.last_run_at).count
    else
      @new_since_last_run = nil
    end
  end

  def run
    @scraper = Scraper.find(params[:id])
    @scraper.update(status: 'running', last_run_at: Time.current)
  launched = ScraperLauncher.launch_upwork(hours: 24, pages: 3, scraper_id: @scraper.id)
    notice = if launched
      "Scraper launched. Chrome should open — log in if prompted, then refresh this page later to see new leads. If Chrome doesn't appear, check macOS Privacy & Security > Automation permissions."
    else
      "Failed to launch scraper. Check log/upwork_scraper.log and macOS permissions."
    end
    redirect_to @scraper, notice: notice
  end

  def status
    @scraper = Scraper.find(params[:id])
    render json: { id: @scraper.id, status: @scraper.display_status, last_run_at: @scraper.last_run_at, total: @scraper.total_leads_collected }
  end
end
