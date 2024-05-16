import os
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Function to extract data from a webpage
def extract_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Check if h1 tag exists
    h1_tag = soup.find('h1')
    if not h1_tag:
        print(f"No heading found for URL: {url}. Skipping extraction of data.")
        return {
            'Heading': '',
            'Article Genre': '',
            'Author Name': '',
            'Posted Time': '',
            'Updated Time': '',
            'Tweets and Iframes': '',
            'Other URLs': ''
        }
    
    heading = h1_tag.text.strip()

    # 2. Scrap article genre
    breadcrumb_nav = soup.find('nav', class_='breadcrumb-nav yoast-breadcrumb')
    article_genre = breadcrumb_nav.find_all('a')[-1]['href'] if breadcrumb_nav else ''

    # 3. Author name
    author_name_tag = soup.find('span', class_='author vcard')
    author_name = author_name_tag.find('a', class_='url fn n').text.strip() if author_name_tag else ''

    # 4. Posted time
    time_tag = soup.find('time', class_='entry-date published')
    posted_time = time_tag.text.strip() if time_tag else ''

    if 'Last updated' in posted_time:
        posted_time, updated_time = posted_time.split('Last updated')
        posted_time = posted_time.strip()
        updated_time = updated_time.strip()

    # 5. Tweets and iframes
    tweets_and_iframes = set()
    for article in soup.find_all('article'):
        if 'href' in article.attrs:
            tweets_and_iframes.add(urljoin(url, article['href']))

    # 6. Other URLs
    other_urls = set()
    for p_tag in soup.find_all('p'):
        for a_tag in p_tag.find_all('a', role='article'):
            if 'href' in a_tag.attrs:
                other_urls.add(a_tag['href'])

    return {
        'Heading': heading,
        'Article Genre': article_genre,
        'Author Name': author_name,
        'Posted Time': posted_time,
        'Updated Time': updated_time if 'updated_time' in locals() else '',
        'Tweets and Iframes': ', '.join(tweets_and_iframes),
        'Other URLs': ', '.join(other_urls)
    }

# Function to scrape a webpage and save data to Excel
def scrape_webpage(url):
    data = extract_data(url)
    df = pd.DataFrame([data])
    if os.path.exists('data.xlsx'):
        existing_df = pd.read_excel('data.xlsx')
        df = pd.concat([existing_df, df], ignore_index=True)
    df.to_excel('data.xlsx', index=False)

# Function to sanitize a filename
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '', filename)

# Function to save text content in p tags to a txt file
def save_text_to_file(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    h1_tag = soup.find('h1')
    heading = h1_tag.text.strip() if h1_tag else ''
    text_content = '\n'.join(p_tag.text.strip() for p_tag in soup.find_all('p'))

    # Create the "txt_files" directory if it doesn't exist
    if not os.path.exists('txt_files'):
        os.makedirs('txt_files')

    # Save text content to a txt file
    filename = sanitize_filename(heading) + '.txt'
    with open(f'txt_files/{filename}', 'w', encoding='utf-8') as file:
        file.write(text_content)

# Function to find links in a webpage for further scraping
def find_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    pbs_content = soup.find('div', class_='pbs-content')
    links = set()
    if pbs_content:
        links.update([link['href'] for link in pbs_content.find_all('a')])
    return links

# Function to sanitize a filename
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '', filename)

# Function to download images from a webpage
def download_images(url, folder):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Check if h1 tag exists
    h1_tag = soup.find('h1')
    if not h1_tag:
        print(f"No heading found for URL: {url}. Skipping download of images.")
        return
    
    heading = h1_tag.text.strip()
    img_tags = soup.find_all('img')

    # Create the "images" directory if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Download images
    for img_tag in img_tags:
        img_url = img_tag['src']
        img_response = requests.get(img_url)
        img_filename = f'{heading}_{os.path.basename(img_url)}'
        img_filename = sanitize_filename(img_filename)  # Sanitize filename
        with open(f'{folder}/{img_filename}', 'wb') as img_file:
            img_file.write(img_response.content)
import time
from selenium import webdriver
driver = webdriver.Chrome()


# Main function to perform scraping
def main(url, depth):
    not_needed_urls = set()
    all_links = set([url])
    for _ in range(depth):
        next_level_links = set()
        for link in all_links.copy():
            scroll_duration = 4
            start_time = time.time()
            while (time.time() - start_time) < scroll_duration:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')
            nav_tag = soup.find('nav')
            if nav_tag:
                for nav_link in nav_tag.find_all('a'):
                    nav_url = nav_link['href']
                    if urlparse(nav_url).netloc == urlparse(url).netloc:
                        not_needed_urls.add(nav_url)
            all_links.update(find_links(link))
            next_level_links.update([urljoin(link, a_tag['href']) for a_tag in soup.find_all('a') if urlparse(a_tag['href']).netloc == urlparse(url).netloc and a_tag['href'] not in not_needed_urls])
        all_links = next_level_links
    for link in all_links:
        scrape_webpage(link)
        save_text_to_file(link)
        download_images(link, 'images')

if __name__ == "__main__":
    main('https://www.altnews.in/', 1)
