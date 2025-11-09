Rails.application.routes.draw do
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # Render dynamic PWA files from app/views/pwa/* (remember to link manifest in application.html.erb)
  # get "manifest" => "rails/pwa#manifest", as: :pwa_manifest
  # get "service-worker" => "rails/pwa#service_worker", as: :pwa_service_worker

  resources :job_listings do
    member do
      patch :mark_viable
      patch :mark_not_viable
      post :analyze_contact_info
      post :analyze_job_viability
      patch :mark_viable_manual
      patch :mark_not_viable_manual
    end
    collection do
      post :analyze_contact_info
      post :analyze_job_viability
      get :manual_evaluation
    end
  end
  resources :scrapers, only: [:index, :show] do
    member do
      post :run
      get :status
      # API endpoints for Python script communication
      get :scraper_status, to: 'scraper_status#show'
      post :signal_login_ready, to: 'scraper_status#signal_login_ready'
      post :continue, to: 'scraper_status#continue'
      post :add_progress, to: 'scraper_status#add_progress'
      post :clear_messages, to: 'scraper_status#clear_messages'
    end
  end
  resources :campaigns, only: [:index, :show]

  get "dashboard", to: "dashboard#index"
  get "analytics", to: "analytics#index"

  namespace :api do
    resources :job_listings, only: [:index, :create]
    resources :scrapers, only: [] do
      member do
        post :complete
      end
    end
  end

  # Defines the root path route ("/")
  root "dashboard#index"
end
