from bs4 import BeautifulSoup

class UpworkScraper:
    def __init__(self, driver):
        self.driver = driver
        self.jobs_url = 'https://www.upwork.com/jobs/'
    
    def scrape_jobs(self):
        try:
            self.driver.get(self.jobs_url)
            time.sleep(5)  # Allow the page to load
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            jobs = soup.find_all('div', class_='job-tile')
            
            for job in jobs:
                title = job.find('h4').get_text(strip=True)
                link = job.find('a')['href']
                print(f"Job Title: {title}")
                print(f"Link: {link}")
        except Exception as e:
            print(f"Error fetching job listings: {e}")
