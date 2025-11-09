class ScraperStatusController < ApplicationController
  # Skip CSRF for API endpoints called by Python script
  skip_before_action :verify_authenticity_token

  def show
    @scraper = Scraper.find(params[:id])
    render json: {
      status: @scraper.status,
      waiting_for_continue: session[:waiting_for_continue] == @scraper.id.to_s,
      messages: session[:scraper_messages] || []
    }
  end

  def signal_login_ready
    @scraper = Scraper.find(params[:id])
    session[:waiting_for_continue] = @scraper.id.to_s
    session[:scraper_messages] ||= []
    session[:scraper_messages] << {
      timestamp: Time.current.to_s,
      message: "Chrome opened - please log in to Upwork, then click Continue below"
    }

    render json: { success: true }
  end

  def continue
    @scraper = Scraper.find(params[:id])
    session[:waiting_for_continue] = nil
    session[:scraper_messages] ||= []
    session[:scraper_messages] << {
      timestamp: Time.current.to_s,
      message: "Continuing with scraping..."
    }

    render json: { success: true }
  end

  def add_progress
    @scraper = Scraper.find(params[:id])
    session[:scraper_messages] ||= []
    session[:scraper_messages] << {
      timestamp: Time.current.to_s,
      message: params[:message]
    }

    render json: { success: true }
  end

  def clear_messages
    @scraper = Scraper.find(params[:id])
    session[:scraper_messages] = []
    render json: { success: true }
  end
end