- Oro CRM ----- Stammer.ai

- With the chatbot AI and CRM
- Add some add dollars into leads, calling leads to close them
- Restaurants and Automotive, hair salons and barber shops

- CRM For people selling AI Services ---- Agency's Specific Stammer -----

- Landing Pages Restaurant Specific CRMz
    3 Product Pages
      * Chat bot service - give examples of restaurant and automotive (Package the restaurant and automotive to a specific landing page) ----- AI bot efficiency, add ons talk just like him
      *
      *
-



-




Voice chat - twilio AI services

text over orders w links
    Niche specific - one on one with customer to know the business needs

POS - system and how to connect with it

Printer

Signal To know there system is down

Reliable internet service - Verizon, starlink



- With the chatbot AI and CRM
-















# Official Lead SystemCurrent Tasks

  - Add Joel to Main website Repo

A Rails application with integrated web scraping for job opportunity management.  - Onboard on how to



## Quick Start  - Get Script to login in without any manual effort

  - Have chrome running on the server

### 1. Scrape Job Listings  - Work on Chatbot

      - Start off with a simple bot

```bash        CRM what should be tracked

cd upwork_ai          How to make it agnostic to frameworks, JS library?

python main.py  -

```



Manual login required:

- Email: hi@alwayscodedfresh.com

- Password: [Use your credentials]

- 2FA: bonneville# official-lead-system



Wait for scraper to finish pulling new listings.



### 2. AI Viability Analysis1st step: Scrape all new Job listings

    python upwork_ai/main.py

Set your OpenAI API key as an environment variable:

  Manual Login with email and password

```bash

export OPENAI_API_KEY="your-openai-api-key-here"      hi@alwayscodedfresh.com

```      Yachtzeex5!

      bonneville

Then run the Rails console:

  Wait until scraper finishes and all new listings are pulled

```bash

bin/rails console

```2nd Step: Log into rails console and invoke the AI Viability Script

  In root of application run:

Execute the viability analysis:

OPENAI_API_KEY="your-openai-api-key-here" bin/rails console

```ruby

JobListing.where(viable_post: nil).each do |job|

  analyzer = JobViabilityService.new(job)

  result = analyzer.analyze!      JobListing.where(viable_post: nil).each do |job|

  puts "#{job.title}: #{result['viable'] ? 'STILL VIABLE' : 'NOW NOT VIABLE'}"        analyzer = JobViabilityService.new(job)

  sleep 1        result = analyzer.analyze!

end        puts "#{job.title}: #{result['viable'] ? 'STILL VIABLE' : 'NOW NOT VIABLE'}"

```        sleep 1

      end
## Current Tasks

- [ ] Add automated login (no manual effort)
- [ ] Chrome server deployment
- [ ] Chatbot development
- [ ] CRM tracking system
- [ ] Framework-agnostic JS library

## Security

⚠️ **Important**: Never commit API keys to the repository. Always use environment variables for sensitive credentials.