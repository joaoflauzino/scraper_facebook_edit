import json
import os
import sys
import urllib.request
import yaml
import utils
import argparse
import getpass

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import datetime
import logging


# -------------------------------------------------------------
# -------------------------------------------------------------


def extract_and_write_posts(elements, filename, user_name):
    try:
        dir_ = 'data/' + user_name 
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        count = 0
        for x in elements:
            try:
                # html post
                post_html = utils.get_post_html(x)
                # time
                # time_str = utils.get_timestamp(x) 
                # import pdb; pdb.set_trace()
                # lista_time = time_str.split(" ")
                # time = "_".join([lista_time[0], lista_time[2], lista_time[4]]).replace(":", "_")
                name_file = dir_ + '/' + user_name + '_' + str(count)
                html = open(name_file + '.html', "w", encoding='utf-8')
                html.write(post_html)
                html.close()
                count += 1

            except Exception as error:
                print("Exception (extract_and_write_posts): ", error)
    except Exception as e:
        print("Exception (extract_and_write_posts): ", e)
    return

# -------------------------------------------------------------
# -------------------------------------------------------------


def save_to_file(name, elements, status, current_section, user_name):
    """helper function used to save links to files"""

    # status 0 = dealing with friends list
    # status 1 = dealing with photos
    # status 2 = dealing with videos
    # status 3 = dealing with about section
    # status 4 = dealing with posts
    # status 5 = dealing with group posts

    try:

        # dealing with Posts
        if status == 4:
            extract_and_write_posts(elements, name, user_name)
            return

    except Exception:
        print("Exception (save_to_file)", "Status =", str(status), sys.exc_info()[0])

    return


# ----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def scrape_data(url, scan_list, section, elements_path, save_status, file_names):
    """Given some parameters, this function can scrap friends/photos/videos/about/posts(statuses) of a profile"""
    page = []
    pos = -1
    if url[-1] == '/':
        pos = -2
    user_name = url.split("/")[pos]

    print("user_name: ", user_name)

    if save_status == 4 or save_status == 5:
        page.append(url)

    page += [url + s for s in section]

    for i, _ in enumerate(scan_list):
        
        
        try:
            driver.get(page[i])
            
            if save_status != 3:
                utils.scroll(total_scrolls, driver, selectors, scroll_time)
                pass

            data = driver.find_elements_by_xpath(elements_path[i])

            save_to_file(file_names[i], data, save_status, i, user_name)

        except Exception:
            print(
                "Exception (scrape_data)",
                str(i),
                "Status =",
                str(save_status),
                sys.exc_info()[0],
            )


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def create_original_link(url):
    if url.find(".php") != -1:
        original_link = (
            facebook_https_prefix + facebook_link_body + ((url.split("="))[1])
        )

        if original_link.find("&") != -1:
            original_link = original_link.split("&")[0]

    elif url.find("fnr_t") != -1:
        original_link = (
            facebook_https_prefix
            + facebook_link_body
            + ((url.split("/"))[-1].split("?")[0])
        )
    elif url.find("_tab") != -1:
        original_link = (
            facebook_https_prefix
            + facebook_link_body
            + (url.split("?")[0]).split("/")[-1]
        )
    else:
        original_link = url

    return original_link


def scrap_profile():

    # execute for all profiles given in input.txt file
    url = driver.current_url
    user_id = create_original_link(url)

    print("\nScraping:", user_id)

    #to_scrap = ["Friends", "Photos", "Videos", "About", "Posts"]
    to_scrap = ["Posts"] # Others: Friends, Photos, Videos and About
    for item in to_scrap:
        print("----------------------------------------")
        print("Scraping {}..".format(item))

        if item == "Posts":
            scan_list = [None]
        elif item == "About":
            scan_list = [None] * 7
        else:
            scan_list = params[item]["scan_list"]

        section = params[item]["section"]
        elements_path = params[item]["elements_path"]
        file_names = params[item]["file_names"]
        save_status = params[item]["save_status"]

        scrape_data(user_id, scan_list, section, elements_path, save_status, file_names)

        print("{} Done!".format(item))

    print("Finished Scraping Profile " + str(user_id) + ".")
    
    return


def get_item_id(url):
    """
    Gets item id from url
    :param url: facebook url string
    :return: item id or empty string in case of failure
    """
    ret = ""
    try:
        link = create_original_link(url)
        ret = link.split("/")[-1]
        if ret.strip() == "":
            ret = link.split("/")[-2]
    except Exception as e:
        print("Failed to get id: " + format(e))
    return ret



# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def login(email, password):
    """ Logging into our own profile """

    try:
        global driver

        #options = Options()
        options = webdriver.ChromeOptions()
        #options.add_argument('headless')

        #  Code to disable notifications pop up of Chrome Browser
        # options.add_argument("--disable-notifications")
        # options.add_argument("--disable-infobars")
        # options.add_argument("--mute-audio")
        # New tests
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        try:
            #driver = webdriver.Chrome(chrome_options=options)
            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(), options=options
            )
        except Exception as ERROR:
            print("Error: ",ERROR)
            print("Error loading chrome webdriver " + str(sys.exc_info()[0]))
            exit(1)

        fb_path = facebook_https_prefix + facebook_link_body
        driver.get(fb_path)
        driver.maximize_window()

        # filling the form
        driver.find_element_by_name("email").send_keys(email)
        driver.find_element_by_name("pass").send_keys(password)

        try:
            # clicking on login button
            driver.find_element_by_id("loginbutton").click()
        except NoSuchElementException:
            # Facebook new design
            driver.find_element_by_name("login").click()

        # if your account uses multi factor authentication
        mfa_code_input = utils.safe_find_element_by_id(driver, "approvals_code")

        if mfa_code_input is None:
            return

        mfa_code_input.send_keys(input("Enter MFA code: "))
        driver.find_element_by_id("checkpointSubmitButton").click()

        # there are so many screens asking you to verify things. Just skip them all
        while (
            utils.safe_find_element_by_id(driver, "checkpointSubmitButton") is not None
        ):
            dont_save_browser_radio = utils.safe_find_element_by_id(driver, "u_0_3")
            if dont_save_browser_radio is not None:
                dont_save_browser_radio.click()

            driver.find_element_by_id("checkpointSubmitButton").click()

    except Exception as e:
        print("There's some error in log in: ", e)
        print(sys.exc_info()[0])
        exit(1)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def scraper(**kwargs):

    email = input('Digite seu email: ')
    password = getpass.getpass('Digite sua senha: ')

    #urls = ['https://facebook.com/lara.mondini4', 'https://facebook.com/me', 'https://www.facebook.com/cassio.dealcantara', 'https://www.facebook.com/DiansleyRaphael', 'https://www.facebook.com/gabriel.valentin.7771',
    #'https://www.facebook.com/Arthur.MartinsS/', 'https://www.facebook.com/luflauzino.flauzino/']
    urls = ['https://www.facebook.com/fredsantosoficial']
    #urls = ['https://www.facebook.com/me']

    if len(urls) > 0:
        print("\nStarting Scraping...")
    
        login(email, password)

        for url in urls:
            driver.get(url)
            link_type = utils.identify_url(driver.current_url)
            if link_type == 0:
                scrap_profile()
        driver.close()
    else:
        print("Input file is empty.")

if __name__ == "__main__":
    
    total_scrolls = 2500 
    scroll_time = 8
    current_scrolls = 0
    old_height = 0
    driver = None

    with open("config/selectors.json") as a, open("config/params.json") as b:
        selectors = json.load(a)
        params = json.load(b)

    firefox_profile_path = selectors.get("firefox_profile_path")
    facebook_https_prefix = selectors.get("facebook_https_prefix")
    facebook_link_body = selectors.get("facebook_link_body")

    # get things rolling
    scraper()