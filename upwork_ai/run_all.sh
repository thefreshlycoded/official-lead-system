#!/bin/bash

# Set the virtual environment path
VENV_PATH="/Users/AlwaysCodedFresh/Desktop/Projects/upwork_scraper/upwork_scraper_env"

# Check if the virtual environment exists, if not, create it
if [ ! -d "$VENV_PATH" ]; then
  echo "Creating virtual environment at $VENV_PATH..."
  python3 -m venv "$VENV_PATH"
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Function to run a script with retry on failure
run_script_with_retry() {
  local script_path=$1
  local success=1  # 0 = success, 1 = failure
  
  while [ $success -ne 0 ]; do
    echo "Running $script_path..."
    python "$script_path"
    
    success=$?
    if [ $success -ne 0 ]; then
      echo "$script_path encountered an error. Retrying..."
      sleep 5  # Wait 5 seconds before retrying (you can adjust this as needed)
    else
      echo "$script_path completed successfully."
    fi
  done
}

# Run each script with retry logic
run_script_with_retry "/Users/AlwaysCodedFresh/Desktop/Projects/upwork_scraper/main.py"
run_script_with_retry "/Users/AlwaysCodedFresh/Desktop/Projects/upwork_scraper/ai_job_category_checker.py"
run_script_with_retry "/Users/AlwaysCodedFresh/Desktop/Projects/upwork_scraper/scrapy.py"

echo "All scripts executed successfully."
