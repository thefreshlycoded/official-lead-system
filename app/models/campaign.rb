class Campaign < ApplicationRecord
  validates :name, presence: true
  enum :status, { draft: 0, active: 1, paused: 2, completed: 3 }
end
