class CreateScrapers < ActiveRecord::Migration[7.1]
  def change
    create_table :scrapers do |t|
      t.string :name, null: false
      t.string :kind, default: "automated"
      t.string :status, default: "setup"
      t.datetime :last_run_at
      t.integer :total_leads_collected, default: 0
      t.boolean :enabled, default: true
      t.text :schedule
      t.text :last_result
      t.text :config_json
      t.timestamps
    end

    add_index :scrapers, :name, unique: true
    add_index :scrapers, :status
    add_index :scrapers, :enabled
  end
end
