from bs4 import BeautifulSoup
import re
from dateutil.parser import parse as date_parse

def parse_html_articles(html_path):
    """
    Parse all articles from the Factiva HTML file, generating IDs dynamically.

    Args:
        html_path (str): The file path to the HTML file containing the articles.

    Returns:
        list: A list of dictionaries, each containing the parsed details of an article.
              Each dictionary has the following keys:
              - id (str): The unique identifier for the article.
              - headline (str): The headline of the article.
              - author (str): The author of the article.
              - word_count (int): The word count of the article.
              - publish_date (datetime): The publication date of the article.
              - source (str): The source of the article.
              - content (str): The main content of the article.
    """
    with open(html_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    articles = []
    for i, div in enumerate(soup.find_all("div", class_="article enArticle")):
        headline = (
            div.find_next("b", string="HD").find_next("td").get_text(strip=True)
            if div.find_next("b", string="HD") else "Unknown Headline"
        )
        author = (
            div.find_next("b", string="SN").find_next("td").get_text(strip=True)
            if div.find_next("b", string="SN") else "Unknown Author"
        )
        word_count_text = (
            div.find_next("b", string="WC").find_next("td").get_text(strip=True)
            if div.find_next("b", string="WC") else None
        )
        # extract the integer from the word count string (e.g., "233 words")
        word_count = int(re.search(r"(\d+)", word_count_text).group(1)) if word_count_text else None

        publish_date_text = (
            div.find_next("b", string="PD").find_next("td").get_text(strip=True)
            if div.find_next("b", string="PD") else None
        )
        # convert publish_date to datetime, or set to None if parsing fails
        publish_date = date_parse(publish_date_text) if publish_date_text else None

        source = (
            div.find_next("b", string="PUB").find_next("td").get_text(strip=True)
            if div.find_next("b", string="PUB") else "Unknown Source"
        )
        content = "\n".join(
            [p.get_text(strip=True) for p in div.find_all("p", class_="articleParagraph")]
        )
        articles.append({
            "headline": headline,
            "author": author,
            "word_count": word_count,
            "publish_date": publish_date,
            "source": source,
            "content": content
        })
    print(f"Total articles parsed: {len(articles)}")
    return articles
