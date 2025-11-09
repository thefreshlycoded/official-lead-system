class ExtendJobListingsWithContactAndProjectFields < ActiveRecord::Migration[7.1]
  def change
    change_table :job_listings, bulk: true do |t|
      t.string  :company_name
      t.string  :contact_name
      t.string  :contact_email
      t.string  :contact_phone
      t.string  :contact_role
      t.datetime :last_contacted_at
      t.string  :contact_method

      t.integer :status, default: 0 # enum: new, contacted, qualified, lost, closed
      t.string  :project_type
      t.integer :budget_min
      t.integer :budget_max
      t.string  :timezone
    end

    add_index :job_listings, :status
    add_index :job_listings, :project_type
  end
end
