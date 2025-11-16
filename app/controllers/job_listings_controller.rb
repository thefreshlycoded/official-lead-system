class JobListingsController < ApplicationController
  before_action :set_job_listing, only: [:show, :mark_viable, :mark_not_viable]

  def index
    @q = params[:q].to_s.strip
    scope = JobListing.all.order(created_at: :desc)
    scope = scope.where(relevance: ActiveModel::Type::Boolean.new.cast(params[:relevant])) if params.key?(:relevant)
    scope = scope.where(source: params[:source]) if params[:source].present?
    if @q.present?
      scope = scope.where("title ILIKE :q OR description ILIKE :q OR job_url ILIKE :q", q: "%#{@q}%")
    end
    @job_listings = scope
  end

  def show
    # Show individual job listing with review buttons
  end

  def new
    @job_listing = JobListing.new
  end

  def create
    @job_listing = JobListing.new(job_listing_params)
    if @job_listing.save
      redirect_to @job_listing, notice: "Job listing created"
    else
      render :new, status: :unprocessable_entity
    end
  end

  def mark_viable
    @job_listing.mark_human_review!(viable: true)
    redirect_to @job_listing, notice: 'Job marked as viable lead!'
  end

  def mark_not_viable
    @job_listing.mark_human_review!(viable: false)
    redirect_to @job_listing, notice: 'Job marked as not viable.'
  end

  def analyze_contact_info
    if params[:id]
      @job_listing = JobListing.find(params[:id])
      # Analyze specific job
      analyzer = ContactAnalyzerService.new(@job_listing)
      if analyzer.analyze!
        redirect_to @job_listing, notice: "✅ Analysis complete! Contact information found and job marked as viable."
      else
        redirect_to @job_listing, notice: "❌ Analysis complete. No contact information found - job marked as not viable."
      end
    else
      # Analyze all unscanned jobs
      limit = params[:limit]&.to_i || 50
      result = ContactAnalyzerService.bulk_analyze(limit: limit)

      if result[:analyzed] > 0
        message = "✅ Analyzed #{result[:analyzed]} jobs. Found #{result[:viable]} viable leads with contact info."
      else
        message = "ℹ️ No unscanned jobs found to analyze."
      end

      redirect_to job_listings_path, notice: message
    end
  rescue => e
    Rails.logger.error "Contact analysis error: #{e.message}"
    if params[:id]
      redirect_to @job_listing, alert: "❌ Analysis failed: #{e.message}"
    else
      redirect_to job_listings_path, alert: "❌ Bulk analysis failed: #{e.message}"
    end
  end

  def analyze_job_viability
    if params[:id]
      @job_listing = JobListing.find(params[:id])
      # Analyze specific job
      analyzer = JobViabilityService.new(@job_listing)
      result = analyzer.analyze!

      if result[:viable]
        redirect_to @job_listing, notice: "✅ Job is viable! Service fit: #{result[:reasoning]}"
      else
        redirect_to @job_listing, notice: "❌ Job not viable. Reason: #{result[:reasoning]}"
      end
    else
      # Analyze all pending jobs (viable_post is nil)
      limit = params[:limit]&.to_i || 50
      result = JobViabilityService.bulk_analyze(limit: limit)

      if result[:analyzed] > 0
        message = "✅ Analyzed #{result[:analyzed]} jobs. Found #{result[:viable]} viable opportunities."
      else
        message = "ℹ️ No pending jobs found to analyze."
      end

      redirect_to job_listings_path, notice: message
    end
  rescue => e
    Rails.logger.error "Job viability analysis error: #{e.message}"
    if params[:id]
      redirect_to @job_listing, alert: "❌ Analysis failed: #{e.message}"
    else
      redirect_to job_listings_path, alert: "❌ Bulk analysis failed: #{e.message}"
    end
  end

  def manual_evaluation
    # Show all pending jobs for manual review
    @job_listings = JobListing.pending_human_review.order(created_at: :desc)
  end

  def mark_viable_manual
    @job_listing = JobListing.find(params[:id])
    @job_listing.mark_human_review!(viable: true)
    respond_to do |format|
      format.turbo_stream do
        flash.now[:notice] = '✅ Marked as viable!'
        remaining = JobListing.pending_human_review.count
        render turbo_stream: [
          turbo_stream.remove(view_context.dom_id(@job_listing, :card)),
          turbo_stream.replace('pending-count', partial: 'job_listings/pending_count_badge', locals: { count: remaining }),
          turbo_stream.update('flash-container', partial: 'shared/flash_messages', locals: { flash_hash: flash })
        ]
      end

      format.html do
        redirect_to manual_evaluation_job_listings_path, notice: '✅ Marked as viable!'
      end
    end
  end

  def mark_not_viable_manual
    @job_listing = JobListing.find(params[:id])
    @job_listing.mark_human_review!(viable: false)
    respond_to do |format|
      format.turbo_stream do
        flash.now[:notice] = '❌ Marked as not viable.'
        remaining = JobListing.pending_human_review.count
        render turbo_stream: [
          turbo_stream.remove(view_context.dom_id(@job_listing, :card)),
          turbo_stream.replace('pending-count', partial: 'job_listings/pending_count_badge', locals: { count: remaining }),
          turbo_stream.update('flash-container', partial: 'shared/flash_messages', locals: { flash_hash: flash })
        ]
      end

      format.html do
        redirect_to manual_evaluation_job_listings_path, notice: '❌ Marked as not viable.'
      end
    end
  end

  def upload_listing
    job_data = upload_listing_params

    if job_data[:job_url].blank?
      redirect_to job_listings_path, alert: "Job URL is required"
      return
    end

    job_listing = JobListing.find_or_initialize_by(job_url: job_data[:job_url])
    job_listing.assign_attributes(job_data)

    if job_listing.save
      action = job_listing.previously_new_record? ? "created" : "updated"
      redirect_to job_listing, notice: "✅ Job listing successfully #{action}!"
    else
      redirect_to job_listings_path, alert: "❌ Failed to save job listing: #{job_listing.errors.full_messages.join(', ')}"
    end
  end

  private

  def set_job_listing
    @job_listing = JobListing.find(params[:id])
  end

  def job_listing_params
    params.require(:job_listing).permit(:job_url, :title, :description, :location, :post_date, :posted_time, :job_link, :fresh, :source, :listing_type, :relevance, :website_present, :website_url, :website_type, :classification_snippet, :facebook, :twitter, :linkedin, :instagram, :city, :state, :country, :industry, :owner_name, :manual_review, :email_pitch, :sms_pitch, :company_name, :contact_name, :contact_email, :contact_phone, :contact_role, :last_contacted_at, :contact_method, :status, :project_type, :budget_min, :budget_max, :timezone, emails: [], phones: [])
  end

  def upload_listing_params
    params.require(:job_listing).permit(:job_url, :title, :description, :location, :post_date, :posted_time, :job_link, :fresh, :source, :listing_type, :relevance, :website_present, :website_url, :website_type, :classification_snippet, :facebook, :twitter, :linkedin, :instagram, :city, :state, :country, :industry, :owner_name, :manual_review, :email_pitch, :sms_pitch, :company_name, :contact_name, :contact_email, :contact_phone, :contact_role, :last_contacted_at, :contact_method, :status, :project_type, :budget_min, :budget_max, :timezone, :viable_post, :viable_post_human, :scanned_for_relevance, :scanned_for_company_details, :ai_relevance_score, :ai_relevance_reasoning, :company_research_completed, :company_research_notes, :viability_analysis, emails: [], phones: [])
  end
end
