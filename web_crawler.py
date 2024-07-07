import requests
from bs4 import BeautifulSoup
import pandas as pd
import schedule
import time
import json
import logging
import psycopg2
from typing import List, Dict, Any
import argparse
from utils import load_config, send_notification, create_logger

# Load configuration
config = load_config('../config/config.json')

# Setup logging with a default filename if 'log_filename' is not present
log_filename = config.get('log_filename', 'crawler.log')
logger = create_logger(log_filename)

def scrape_arxiv(query: str, limit: int) -> List[Dict[str, Any]]:
    """
    Scrapes arxiv.org for papers based on the query.
    
    :param query: The search query.
    :param limit: The maximum number of items to scrape.
    :return: A list of dictionaries containing the scraped data.
    """
    url = f"https://arxiv.org/search/?query={query}&searchtype=all"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    results = []
    papers = soup.find_all('li', class_='arxiv-result')
    for paper in papers[:limit]:
        title_tag = paper.find('p', class_='title')
        authors_tag = paper.find('p', class_='authors')
        abstract_tag = paper.find('p', class_='abstract')
        url_tag = paper.find('p', class_='list-title')

        title = title_tag.text.strip() if title_tag else "N/A"
        authors = authors_tag.text.strip() if authors_tag else "N/A"
        abstract = abstract_tag.text.strip() if abstract_tag else "N/A"
        url = "https://arxiv.org" + url_tag.find('a')['href'] if url_tag else "N/A"

        results.append({
            'query': query,
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'url': url,
        })
    
    return results

def scrape_paperswithcode(query: str, limit: int) -> List[Dict[str, Any]]:
    """
    Scrapes paperswithcode.com for papers based on the query.
    
    :param query: The search query.
    :param limit: The maximum number of items to scrape.
    :return: A list of dictionaries containing the scraped data.
    """
    url = f"https://paperswithcode.com/search?q={query}"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    results = []
    papers = soup.find_all('div', class_='infinite-item')
    for paper in papers[:limit]:
        title_tag = paper.find('h1')
        authors_tag = paper.find('p', class_='authors')
        paper_url_tag = paper.find('a')

        title = title_tag.text.strip() if title_tag else "N/A"
        authors = authors_tag.text.strip() if authors_tag else "N/A"
        paper_url = "https://paperswithcode.com" + paper_url_tag['href'] if paper_url_tag else "N/A"

        results.append({
            'query': query,
            'title': title,
            'authors': authors,
            'url': paper_url,
        })
    
    return results

def scrape_site(site: str, query: str, limit: int, mode: str = 'images') -> List[Dict[str, Any]]:
    """
    Scrapes a given website for either images or datasets based on the query.
    
    :param site: The base URL of the site to scrape.
    :param query: The search query.
    :param limit: The maximum number of items to scrape.
    :param mode: The mode of scraping, either 'images' or 'datasets'.
    :return: A list of dictionaries containing the scraped data.
    """
    try:
        if "arxiv.org" in site:
            return scrape_arxiv(query, limit)
        elif "paperswithcode.com" in site:
            return scrape_paperswithcode(query, limit)
        elif "google.com" in site:
            # Google scraping is not implemented due to complexity
            logger.error(f"Scraping not implemented for site: {site}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping {site} with query {query}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error scraping {site} with query {query}: {e}")
    return []

def save_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Saves the scraped data to a CSV file.
    
    :param data: The data to save.
    :param filename: The name of the CSV file.
    """
    try:
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data saved to CSV file: {filename}")
    except Exception as e:
        logger.error(f"Error saving data to CSV file {filename}: {e}")

def save_to_db(data: List[Dict[str, Any]], db_config: Dict[str, Any]) -> None:
    """
    Saves the scraped data to a PostgreSQL database.
    
    :param data: The data to save.
    :param db_config: Configuration dictionary containing database connection parameters.
    """
    try:
        conn = psycopg2.connect(
            dbname=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port']
        )
        cur = conn.cursor()
        for record in data:
            cur.execute("""
                INSERT INTO images (query, url, size, format)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (record['query'], record['url'], record.get('size', 'N/A'), record.get('format', 'N/A')))
        conn.commit()
        cur.close()
        conn.close()
        print("Data saved to PostgreSQL database")
    except Exception as e:
        logger.error(f"Error saving data to database: {e}")

def scrape_all_sites(config: Dict[str, Any], image_limit_per_query: int) -> List[Dict[str, Any]]:
    """
    Scrapes all configured sites for images or datasets based on the provided configuration.
    
    :param config: Configuration dictionary.
    :param image_limit_per_query: Maximum number of images to scrape per query.
    :return: A list of dictionaries containing the scraped data.
    """
    if 'websites' not in config:
        logger.error("Configuration missing 'websites' key")
        return []
    if 'queries' not in config:
        logger.error("Configuration missing 'queries' key")
        return []

    data = []
    for site in config['websites']:
        for query in config['queries']:
            mode = 'images' if 'images' in site else 'datasets'
            data.extend(scrape_site(site, query, image_limit_per_query, mode))
    return data

def job() -> None:
    """
    Job function to be scheduled, which scrapes data and saves it to CSV and database.
    """
    try:
        print("Job started...")
        data = scrape_all_sites(config, 1000)  # Adjust image_limit_per_query as needed
        if data:
            save_to_csv(data, config.get('csv_filename', 'output.csv'))
            save_to_db(data, config['db_config'])
            if config.get('email_notifications', {}).get('enabled', False):
                send_notification(
                    subject="Scraping Completed",
                    body="The scraping task has completed successfully.",
                    to_email=config['email_notifications'].get('email_to', '')
                )
    except Exception as e:
        logger.error(f"Unexpected error in job function: {e}")
    print("Job completed.")

def main() -> None:
    """
    Main function to handle CLI interactions for the web crawler.
    """
    parser = argparse.ArgumentParser(description="Web Crawler for Images and Datasets")
    parser.add_argument('--query', type=str, help='Search query for scraping', required=True)
    parser.add_argument('--mode', type=str, choices=['images', 'datasets'], help='Mode of scraping', required=True)
    parser.add_argument('--limit', type=int, help='Limit on the number of items to scrape', default=100)
    parser.add_argument('--schedule', type=str, choices=['daily', 'weekly'], help='Schedule interval for scraping', default='weekly')
    
    args = parser.parse_args()
    
    # Add the query to the config
    config['queries'] = [args.query]
    
    # Run the job immediately with the provided query
    data = scrape_all_sites(config, args.limit)
    if data:
        save_to_csv(data, config.get('csv_filename', 'output.csv'))
        save_to_db(data, config['db_config'])
    
    # Schedule the job
    if args.schedule == 'weekly':
        schedule.every().week.do(job)
    elif args.schedule == 'daily':
        schedule.every().day.do(job)
    
    print(f"Scheduling job to run {args.schedule}ly")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
