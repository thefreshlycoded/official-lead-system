class AnalyticsController < ApplicationController
  def index
    # simple aggregates by day for last 7 days
    @by_day = JobListing.where('created_at >= ?', 7.days.ago)
                        .group("DATE(created_at)")
                        .count
    @by_source = JobListing.group(:source).count
  end
end
