class Scraper < ApplicationRecord
  validates :name, presence: true
  validates :kind, inclusion: { in: %w[automated manual custom] }, allow_nil: true
  validates :status, inclusion: { in: %w[running paused needs_login setup error] }, allow_nil: true

  def display_status
    status.presence || "setup"
  end
end
