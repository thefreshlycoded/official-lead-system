module Api
  class JobListingsController < ApplicationController
    protect_from_forgery with: :null_session

    def index
      listings = JobListing.relevant.order(created_at: :desc).limit(200)
      render json: listings.as_json
    end

    def create
      attrs = permitted_attributes
      return render json: { errors: ["job_url is required"] }, status: :unprocessable_entity if attrs[:job_url].blank?

      jl = JobListing.find_or_initialize_by(job_url: attrs[:job_url])
      jl.assign_attributes(attrs)
      if jl.save
        render json: { id: jl.id }, status: :created
      else
        render json: { errors: jl.errors.full_messages }, status: :unprocessable_entity
      end
    end

    private

    PERMITTED_KEYS = [
      :job_url, :title, :description, :location, :post_date, :posted_time, :job_link, :fresh, :source, :listing_type,
      :relevance, :website_present, :website_url, :website_type, :classification_snippet,
      :facebook, :twitter, :linkedin, :instagram, :city, :state, :country, :industry, :owner_name,
      :manual_review, :email_pitch, :sms_pitch,
      :company_name, :contact_name, :contact_email, :contact_phone, :contact_role, :last_contacted_at, :contact_method,
      :status, :project_type, :budget_min, :budget_max, :timezone,
      { emails: [], phones: [] }
    ]

    # Accept either nested params under :job_listing (Python uploader) or top-level attributes.
    def permitted_attributes
      if params[:job_listing].present?
        params.require(:job_listing).permit(*PERMITTED_KEYS)
      else
        params.permit(*PERMITTED_KEYS)
      end
    end
  end
end
