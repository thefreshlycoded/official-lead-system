class DashboardController < ApplicationController
  def index
    @total = JobListing.count
    @relevant = JobListing.where(relevance: true).count
    @irrelevant = JobListing.where(relevance: false).count
    @unknown = @total - @relevant - @irrelevant

    @by_source = JobListing.group(:source).count
    @recent = JobListing.order(created_at: :desc).limit(10)
  end
end
