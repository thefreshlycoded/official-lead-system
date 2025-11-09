module Api
  class ScrapersController < ApplicationController
    protect_from_forgery with: :null_session

    def complete
      scraper = Scraper.find_by(id: params[:id])
      return render json: { error: 'not found' }, status: :not_found unless scraper
      scraper.update(status: 'paused', last_run_at: Time.current, total_leads_collected: JobListing.where(source: scraper.name.downcase).count)
      render json: { ok: true }
    end
  end
end
