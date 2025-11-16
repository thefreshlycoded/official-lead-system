module Api
  class UploadJobListingsController < ApplicationController
    protect_from_forgery with: :null_session

    # Single job upload
    def upload
      job_data = permitted_job_params

      return render json: { error: "job_url is required" }, status: :unprocessable_entity if job_data[:job_url].blank?

      job_listing = JobListing.find_or_initialize_by(job_url: job_data[:job_url])
      job_listing.assign_attributes(job_data)

      if job_listing.save
        render json: {
          success: true,
          id: job_listing.id,
          job_url: job_listing.job_url,
          created: job_listing.previously_new_record?
        }, status: :created
      else
        render json: {
          success: false,
          error: "Failed to save job listing",
          errors: job_listing.errors.full_messages
        }, status: :unprocessable_entity
      end
    end

    # Batch job upload
    def batch_upload
      jobs_data = params[:jobs] || []

      return render json: { error: "No jobs provided" }, status: :unprocessable_entity if jobs_data.empty?

      results = {
        success: true,
        total: jobs_data.length,
        created: 0,
        updated: 0,
        failed: 0,
        errors: []
      }

      jobs_data.each_with_index do |job_data, index|
        begin
          # Ensure job_url is present
          if job_data[:job_url].blank?
            results[:failed] += 1
            results[:errors] << "Job #{index + 1}: job_url is required"
            next
          end

          job_listing = JobListing.find_or_initialize_by(job_url: job_data[:job_url])
          was_new_record = job_listing.new_record?

          job_listing.assign_attributes(job_data.permit(*permitted_keys))

          if job_listing.save
            if was_new_record
              results[:created] += 1
            else
              results[:updated] += 1
            end
          else
            results[:failed] += 1
            results[:errors] << "Job #{index + 1} (#{job_data[:job_url]}): #{job_listing.errors.full_messages.join(', ')}"
          end
        rescue => e
          results[:failed] += 1
          results[:errors] << "Job #{index + 1}: #{e.message}"
        end
      end

      results[:success] = results[:failed] == 0
      status_code = results[:success] ? :ok : :unprocessable_entity

      render json: results, status: status_code
    end

    private

    def permitted_keys
      [
        :job_url, :title, :description, :location, :post_date, :posted_time,
        :job_link, :fresh, :source, :listing_type, :relevance, :website_present,
        :website_url, :website_type, :classification_snippet, :facebook, :twitter,
        :linkedin, :instagram, :city, :state, :country, :industry, :owner_name,
        :manual_review, :email_pitch, :sms_pitch, :company_name, :contact_name,
        :contact_email, :contact_phone, :contact_role, :last_contacted_at,
        :contact_method, :status, :project_type, :budget_min, :budget_max,
        :timezone, :viable_post, :viable_post_human, :scanned_for_relevance,
        :scanned_for_company_details, :ai_relevance_score, :ai_relevance_reasoning,
        :company_research_completed, :company_research_notes, :viability_analysis,
        { emails: [], phones: [] }
      ]
    end

    def permitted_job_params
      params.require(:job).permit(*permitted_keys)
    end
  end
end