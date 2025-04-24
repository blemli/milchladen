#!/usr/bin/env python

import click, json, os, pathlib, re
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from icecream import ic
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException

driver = None
ORDER_URL='https://www.galaxus.ch/de/order'
AUTH_URL='https://id.digitecgalaxus.ch/n/p/22/en'

def click_by_text(driver,text):
    element=driver.find_element(By.XPATH, f"//button[normalize-space(text()) = '{text}']")
    if element.is_displayed() and element.is_enabled():
        element.click()
    else:
        raise ElementNotInteractableException(f"Element with text '{text}' is not interactable.")

def get_driver(debug):
    global driver
    options = uc.ChromeOptions()
    if not debug:
            options.add_argument('--headless')
    options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
    profile_dir = os.path.join(str(pathlib.Path.home()), '.galaxus_chrome_profile')
    os.makedirs(profile_dir, exist_ok=True)
    print(f"[DEBUG] Using Chrome user-data-dir: {profile_dir}")
    options.add_argument(f'--user-data-dir={profile_dir}')
    options.add_argument('--profile-directory=Default')
    driver = uc.Chrome(options=options)
    

def is_logged_in():
    """Check if the user is logged in by looking for a specific element on the page"""
    global driver
    print(f"[DEBUG] Cookies at start of is_logged_in: {driver.get_cookies()}")
    try:
        driver.get(ORDER_URL)
        if driver.current_url.startswith(AUTH_URL):
            return False
        return True
    except Exception as e:
        return False

@click.group()
@click.option("--debug", is_flag=True, help="Run in debug mode (non-headless)")
@click.pass_context
def cli(ctx, debug):
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ChromeDriverManager().install()
    get_driver(debug=debug)
    print(f"[DEBUG] Cookies in profile on startup: {driver.get_cookies()}")
    if ctx.invoked_subcommand != "auth" and not is_logged_in():
        click.echo("Not logged in. Please login first.")
        return
    
@cli.group()
def order():
    pass

@cli.group()
def auth():
    pass

        
@auth.command("login")
@click.option("--debug", is_flag=True, help="Run in debug mode (non-headless)")
def login(debug=False):
    """Command to login to Galaxus"""
    global driver
    driver.get(ORDER_URL)
    while not driver.current_url.startswith(ORDER_URL):
        sleep(1)
    click.echo("sucessfully logged in")
    # Debug: list cookies after login
    cookies = driver.get_cookies()
    click.echo(f"[DEBUG] Cookies in session: {cookies}")
    sleep(6)  # Wait to ensure cookies are flushed to disk
    click.echo("Session saved to profile. You won't need to login next time.")
    driver.quit()


@auth.command("logout")
@click.option("--debug", is_flag=True, help="Run in debug mode (non-headless)")
def logout(debug=False):
    """Command to logout from Galaxus"""
    global driver
    # Navigate to the logout URL
    driver.get(f"{AUTH_URL}/logout")
    sleep(3)
    click_by_text(driver, "Sign out")
    sleep(6)
    if not debug: driver.quit()
        
def extract_orders(driver):
    """
    Extracts orders from a Galaxus orders page using a Selenium driver.

    Returns:
        dict: Mapping order ID (str) to a dict with keys:
            - date (str): Order date in format 'DD.MM.YYYY'
            - total (float): Total amount in CHF
    """
    orders = {}
    order_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.ypxwrOx2.ypxwrOx')
    for block in order_blocks:
        # Extract header text, e.g. "Bestellung 142386311 vom 22.3.2025"
        header = block.find_element(By.CSS_SELECTOR, 'div.yZWibtS h2').text
        match = re.search(r'Bestellung\s+(\d+)\s+vom\s+([\d\.]+)', header)
        if not match:
            continue
        order_id, date_str = match.group(1), match.group(2)

        # Extract total amount text, e.g. "CHF 69.90" or "CHF 0.–"
        total_text = block.find_element(By.CSS_SELECTOR, 'div.yZWibtS1 span span.yZWibtS5').text
        # Clean and convert to float
        # Remove currency, non-breaking spaces, replace dash with zero
        cleaned = total_text.replace('CHF', '').replace('\u00A0', '').replace('–', '0').strip()
        try:
            total_amount = float(cleaned)
        except ValueError:
            # Fallback: replace comma with dot if necessary
            cleaned = cleaned.replace(',', '.')
            total_amount = float(cleaned)

        orders[order_id] = {
            'date': date_str,
            'total': total_amount,
        }

    return orders


@order.command("list")
@click.option("--debug", is_flag=True, help="Run in debug mode (non-headless)")
@click.option("--output", "-o", type=click.Path(), help="Save output to a file")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def order_list(debug, output, verbose):
    try:
        global driver
        driver.get(ORDER_URL)
        print("downloading orders",end='')
        while True:
            print(".", end='')
            try:
                click_by_text(driver, "Mehr anzeigen")
                count=0 
            except ElementNotInteractableException as e:
                sleep(0.5)
                count+=1
                if count > 20:
                    break
            except ElementClickInterceptedException as e:
                sleep(0.5)
                continue
        print(" done")
        orders= extract_orders(driver)
        if not debug:
            driver.quit()
        if verbose:     
            click.echo(f"Final count: {len(orders)} orders")
        if output:
            with open(output, 'w') as f:
                json.dump(orders, f, indent=4)
            click.echo(f"Orders saved to {output}")
        else:
            click.echo(json.dumps(orders, indent=4))
    except Exception as e:
        click.echo(f"Error: {str(e)}")
 
            
if __name__ == '__main__':
    cli()
