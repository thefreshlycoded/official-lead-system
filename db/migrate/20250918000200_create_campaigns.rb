class CreateCampaigns < ActiveRecord::Migration[7.1]
  def change
    create_table :campaigns do |t|
      t.string :name, null: false
      t.text :description
      t.integer :status, default: 0
      t.integer :leads_count, default: 0
      t.datetime :launched_at
      t.timestamps
    end

    add_index :campaigns, :status
  end
end
