#!/usr/bin/env python

import click
import json
import os
import subprocess
import sys
from splinter import Browser
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from icecream import ic
import pathlib
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
ChromeDriverManager().install()

def perform_login(debug=False):
    """Internal function to perform login and return the driver"""
    options = uc.ChromeOptions()
    if not debug:
            options.add_argument('--headless')
    options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
    profile_dir = os.path.join(str(pathlib.Path.home()), '.galaxus_chrome_profile')
    os.makedirs(profile_dir, exist_ok=True)
    options.add_argument(f'--user-data-dir={profile_dir}')
    driver = uc.Chrome(options=options)
    driver.get('https://www.galaxus.ch/de/order')
    sleep(3)
    if driver.current_url == 'https://www.galaxus.ch/de/order':
        click.echo("Already logged in.")
        return driver
    sleep(30)  # Give more time for the page to load
    return driver

def get_credentials():
    try:
        cmd = ["op", "item", "get", "bnxq7l2ghbs6dhn3qkgjwji5wu", "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to get credentials from 1Password: {result.stderr}")
            
        data = json.loads(result.stdout)
        
        username = None
        password = None
        
        for field in data.get("fields", []):
            if field.get("label") == "username":
                username = field.get("value")
            elif field.get("label") == "password":
                password = field.get("value")
        
        if not username or not password:
            raise Exception("Username or password not found in 1Password item")
            
        return username, password
    except Exception as e:
        click.echo(f"Error retrieving credentials: {str(e)}", err=True)
        sys.exit(1)

@click.group()
def cli():
    pass

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
    driver = perform_login(debug)
    if driver:
        # Wait a bit to ensure cookies are saved
        sleep(5)
        click.echo("Session saved to profile. You won't need to login next time.")
        driver.quit()
        


@order.command("list")
@click.option("--debug", is_flag=True, help="Run in debug mode (non-headless)")
@click.option("--output", "-o", type=click.Path(), help="Save output to a file")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def order_list(debug, output, verbose):
    try:
        driver = perform_login(debug)
        if not driver:
            click.echo("Login failed")
            return
        if verbose:
            click.echo("Visiting orders page...")
        driver.get('https://www.galaxus.ch/de/orders')
        sleep(2)
        if verbose:
            click.echo(f"Current URL: {driver.current_url}")
            if driver.current_url != 'https://www.galaxus.ch/de/orders':
                click.echo("Not on orders page. Login might have failed.")
        orders = []
        try:
            order_elements = driver.find_elements(By.CSS_SELECTOR, '.order-item, .orderItem, tr')
            if verbose:
                click.echo(f"Found {len(order_elements)} potential order elements")
            
            for i, order in enumerate(order_elements):
                try:
                    if verbose:
                        click.echo(f"Processing order element {i+1}...")
                        click.echo(f"HTML: {order.get_attribute('outerHTML')[:200]}...")
                    
                    id_elem = order.find_elements(By.CSS_SELECTOR, '.order-number, .orderNumber, td:nth-child(1)')
                    date_elem = order.find_elements(By.CSS_SELECTOR, '.order-date, .orderDate, td:nth-child(2)')
                    status_elem = order.find_elements(By.CSS_SELECTOR, '.order-status, .orderStatus, td:nth-child(3)')
                    total_elem = order.find_elements(By.CSS_SELECTOR, '.order-total, .orderTotal, td:nth-child(4)')
                    
                    if verbose:
                        click.echo(f"ID element found: {len(id_elem) > 0}")
                        click.echo(f"Date element found: {len(date_elem) > 0}")
                        click.echo(f"Status element found: {len(status_elem) > 0}")
                        click.echo(f"Total element found: {len(total_elem) > 0}")
                    
                    if len(id_elem) > 0 and len(date_elem) > 0 and len(status_elem) > 0 and len(total_elem) > 0:
                        order_data = {
                            'id': id_elem[0].text.strip(),
                            'date': date_elem[0].text.strip(),
                            'status': status_elem[0].text.strip(),
                            'total': total_elem[0].text.strip()
                        }
                        orders.append(order_data)
                        if verbose:
                            click.echo(f"Added order: {order_data}")
                except Exception as e:  
                    if verbose:
                        click.echo(f"Error processing order element {i+1}: {str(e)}")
        except Exception as e:
            click.echo(f"Error finding order elements: {str(e)}")                   
        if verbose:     
            click.echo(f"Found {len(orders)} orders")
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
