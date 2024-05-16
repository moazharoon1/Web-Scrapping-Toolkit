import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Function to scrape a single page
def scrape_page(driver, M_LABEL_MAP):
    # Get the HTML content of the page
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # Extract individual posts
    articles = soup.find_all('article')
    for article in articles:
        # Find the div with the class 'status__wrapper' within each article
        status_wrapper = article.find('div', class_='status__wrapper')
        if status_wrapper:
            # Extract the aria-label attribute
            M_LABEL_MAP = status_wrapper.get('aria-label')
            if M_LABEL_MAP and M_LABEL_MAP not in M_LABEL_MAP:
                thumbnail_hrefs = []
                # Find all <a> tags with class "media-gallery__item-thumbnail"
                thumbnails = status_wrapper.find_all('a', class_='media-gallery__item-thumbnail', href=True)
                for thumbnail in thumbnails:
                    T_HREF = thumbnail['href']
                    thumbnail_hrefs.append(T_HREF)

                link_hrefs = []
                links_posts = status_wrapper.find_all('a', class_='status-card', href=True)
                for link in links_posts:
                    L_HREF = link['href']
                    link_hrefs.append(L_HREF)

                # Store thumbnail and link hrefs against aria-label in the map
                M_LABEL_MAP[M_LABEL_MAP] = {'thumbnail_hrefs': thumbnail_hrefs, 'link_hrefs': link_hrefs}


# Function to scrape multiple pages
def scrape_multiple_pages(base_url, num_pages, articles_per_page):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    driver = webdriver.Chrome(options=chrome_options)  # You need to have ChromeDriver installed
    driver.get(base_url)
    M_LABEL_MAP = {}  # Initialize an empty dictionary to store aria-labels and thumbnail hrefs

    for _ in range(num_pages):
        scrape_page(driver, M_LABEL_MAP)
        # Scroll down to load more content if needed
        for _ in range(articles_per_page):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # Adjust as needed, wait for the new content to load

    driver.quit()
    return M_LABEL_MAP


# Function to write data to a CSV file
def write_to_csv(M_LABEL_MAP, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['M_LABEL', 'TN_HREF', 'L_HREF']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for aria_label, hrefs in M_LABEL_MAP.items():
            thumbnail_hrefs = ','.join(hrefs['TN_HREF'])
            link_hrefs = ','.join(hrefs['L_HREF'])
            writer.writerow({'M_LABEL': aria_label, 'TN_HREF': thumbnail_hrefs, 'L_HREF': link_hrefs})
    print(f"Data has been written to {filename}")


base_url = 'https://mastodon.social/explore'
num_pages_to_scrape = 10  # Reduce the number of pages to scrape
articles_per_page = 20  # Limit the number of articles extracted per page
aria_label_map = scrape_multiple_pages(base_url, num_pages_to_scrape, articles_per_page)

filename = 'scraped_data.csv'  # Change the filename if needed
write_to_csv(aria_label_map, filename)
