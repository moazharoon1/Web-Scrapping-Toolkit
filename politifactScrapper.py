import requests
from bs4 import BeautifulSoup
import openpyxl

base_url = 'https://www.politifact.com'
image_meanings = {
    'meter-false': 'False',
    'tom_ruling_pof': 'Pants on Fire',
    'tom_ruling_falso': 'False',
    'meter-mostly-false': 'Mostly False',
    'meter-half-true': 'Half True',
    'meter-true': 'True',
}

def get_article_links(url, soup):
    links = set()
    base_url = "https://www.politifact.com"  # Define the base URL
    
    # Get all links from the page
    all_links = soup.find_all('a', href=True)
    
    for link_tag in all_links:
        link = link_tag['href']
        # Add base URL if not already present and meets the specified conditions
        if not link.startswith('http') and not link.startswith('//'): # and not link.startswith('#'):
            full_url = base_url + link
        else:
            full_url = link
        
        if full_url.startswith(base_url) and not full_url.startswith(base_url + '/personalities/') and not full_url.endswith(('.jpg', '.png', '.jpeg', '.gif')) and not full_url.endswith(('/image/')):
            if '/factchecks/' in full_url or '/article/' in full_url:
                # Exclude links with query parameters or fragment identifiers, ends with /list/, or are from /rss/ or /article/ endpoints
                if '?' not in full_url and '#' not in full_url and not full_url.endswith('/list/') and '/rss/' not in full_url:
                    links.add(full_url)
    
    # Append unique links to the text file without overwriting
    with open('links_to_scrape.txt', 'a') as file:
        for link in links:
            file.write(link + '\n')
    
    return links

def scrape_article(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get news heading
    news_heading = soup.find('div', class_='m-statement__quote').text.strip() if soup.find('div', class_='m-statement__quote') else ''
    
    # Get main image
    main_image_tag = soup.find('div', class_='c-image')
    main_image = main_image_tag.find('img')['src'] if main_image_tag else ''
    
    # Get image caption
    image_caption = soup.find('div', class_='c-image__caption').text.strip() if soup.find('div', class_='c-image__caption') else ''
    
    # Get author name and date
    author_name_tag = soup.find('div', class_='m-author__content')
    author_name = author_name_tag.find('a').text if author_name_tag and author_name_tag.find('a') else ''
    author_date = author_name_tag.find('span', class_='m-author__date').text.strip() if author_name_tag and author_name_tag.find('span', class_='m-author__date') else ''
    
    # Check if the URL is for an article or a fact-check
    if '/article/' in url:
        meter_label = ''  # Leave the meter label blank for articles
    else:
        # Get meter image and label
        meter_image_tag = soup.find('div', class_='m-statement__meter')
        meter_image_url = meter_image_tag.find('img', class_='c-image__original')['src'] if meter_image_tag else ''
        meter_label = ''
        if meter_image_url:
            meter_image_name = meter_image_url.split('/')[-1].split('.')[0]
            meter_label = image_meanings.get(meter_image_name, meter_image_name)
    
    # Get keywords
    keywords = [tag.text.strip() for tag in soup.find('ul', class_='m-list--horizontal').find_all('span')] if soup.find('ul', class_='m-list--horizontal') else []
    
    # Get callout body content
    callout_body = soup.find('div', class_='m-callout__body')
    callout_data = ""
    if callout_body:
        short_on_time = callout_body.find('div', class_='short-on-time')
        if short_on_time:
            p_tags = short_on_time.find_all('p')
            callout_data = "\n".join(p.text.strip() for p in p_tags)
    
    # Extract data from iframes
    iframe_data = [iframe['src'] for iframe in soup.find_all('iframe')]
    
    # Extract data from img tags inside p tags
    img_in_p_data = [img['src'] for p in soup.find_all('p') for img in p.find_all('img')]
    
    # Extract data from img tags within artembed tags
    img_in_artembed_data = [img['src'] for artembed in soup.find_all('artembed') for img in artembed.find_all('img')]
    
    # Combine all extracted data into a single list
    extra_data = iframe_data + img_in_p_data + img_in_artembed_data
    
    return news_heading, main_image, image_caption, author_name, author_date, url, meter_label, keywords, extra_data, callout_data

def scrape_politifact(url, depth=0, visited_links=None):
    if depth == 1:
        return []
    
    if visited_links is None:
        visited_links = set()
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    article_links = get_article_links(url, soup)
    data = []
    
    for link in article_links:
        if link not in visited_links:
            visited_links.add(link)
            news_heading, main_image, image_caption, author_name, author_date, url, meter_label, keywords, extra_data, summary = scrape_article(link)
            data.append([news_heading, main_image, image_caption, author_name, author_date, url, meter_label, ', '.join(keywords), ', '.join(extra_data), summary])
            # Recursively scrape articles from subsequent pages
            data += scrape_politifact(link, depth + 1, visited_links)
    
    return data

def save_to_excel(data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['News Heading', 'Main Image', 'Image Caption', 'Author Name', 'Author Date', 'Link', 'Meter Label', 'Keywords', 'Extra Data', 'Summary'])
    
    visited_urls = set()  # Keep track of visited URLs to avoid duplicates
    
    for row in data:
        url = row[5]  # URL is at index 5 in the row
        if url not in visited_urls:  # Check if the URL is visited
            ws.append(row)  # Append the row to the Excel sheet
            visited_urls.add(url)  # Add the URL to visited URLs set
    
    wb.save('politifact_data.xlsx')

def main():
    data = scrape_politifact(base_url)
    save_to_excel(data)

if __name__ == "__main__":
    main()
