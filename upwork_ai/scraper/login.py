from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

class UpworkLogin:
    def __init__(self, driver, username, password):
        self.driver = driver
        self.username = username
        self.password = password

    def login(self):
        self.driver.get("https://www.upwork.com/ab/account-security/login")
        self.driver.find_element("id", "login_username").send_keys(self.username)
        self.driver.find_element("id", "login_password_continue").click()
        time.sleep(2)
        self.driver.find_element("id", "login_password").send_keys(self.password)
        self.driver.find_element("id", "login_password_continue").click()
