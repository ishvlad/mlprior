from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
#https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
from slugify import slugify
from tqdm import tqdm
import numpy as np


def download_all_papers(base_url, save_dir, driver_path, acc_rej):
    driver = webdriver.Chrome(driver_path)
    driver.get(base_url)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # wait for the select element to become visible
    print('Starting web driver wait...')
    wait = WebDriverWait(driver, 60)
    print('Starting web driver wait... finished')
    res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
    print("Successful load the website!->",res)
    res = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "note")))
    print("Successful load the website notes!->",res)
    # parse the results
    divs = driver.find_elements_by_xpath('//*[@id="all-submissions"]/ul/li[@class="note "]')
    num_papers = len(divs)
    print('found number of papers:',num_papers)
    links = []
    for index, paper in enumerate(tqdm(divs)):
        a_hrefs = paper.find_elements_by_tag_name("a")
        name = slugify(a_hrefs[0].text)
        link = a_hrefs[1].get_attribute('href')
#        name = paper.find_element_by_class_name('note_content_title').text
#        link = paper.find_element_by_class_name('note_content_pdf').get_attribute('href')
#         print('Downloading paper {}/{}: {}'.format(index+1, num_papers, name))
        links.append(link)
        # download_pdf(link, os.path.join(save_dir, name))
    np.savetxt('./papers/2020_all.txt', links, fmt='%s')
    driver.close()


def download_pdf(url, name):
    r = requests.get(url, stream=True)

    with open('%s.pdf' % name, 'wb') as f:
        for chunck in r.iter_content(1024):
            f.write(chunck)
    r.close()


if __name__ == '__main__':
    year = 2020
    acc_rej = 'accepted'
    ICLR = 'https://openreview.net/group?id=ICLR.cc/%s/Conference#all-submissions' % year
    driver_path = '/usr/local/bin/chromedriver'
    save_dir_nips = '.'
    save_dir_iclr = './papers/accepted'

    download_all_papers(ICLR, save_dir_iclr, driver_path, year)