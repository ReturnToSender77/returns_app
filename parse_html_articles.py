from bs4 import BeautifulSoup

def parse_html_articles(html_path):
    """
    Parse all articles from the Factiva HTML file, generating IDs dynamically.
    """
    with open(html_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    articles = []
    for i, div in enumerate(soup.find_all("div", class_="article enArticle")):
        article_id = f"article-{i}"
        headline = (
            div.find_next("b", string="HD").find_next("td").get_text(strip=True)
            if div.find_next("b", string="HD") else "Unknown Headline"
        )
        author = (
            div.find_next("b", string="SN").find_next("td").get_text(strip=True)
            if div.find_next("b", string="SN") else "Unknown Author"
        )
        word_count = (
            div.find_next("b", string="WC").find_next("td").get_text(strip=True)
            if div.find_next("b", string="WC") else "Unknown Word Count"
        )
        publish_date = (
            div.find_next("b", string="PD").find_next("td").get_text(strip=True)
            if div.find_next("b", string="PD") else "Unknown Date"
        )
        source = (
            div.find_next("b", string="PUB").find_next("td").get_text(strip=True)
            if div.find_next("b", string="PUB") else "Unknown Source"
        )
        content = "\n".join(
            [p.get_text(strip=True) for p in div.find_all("p", class_="articleParagraph")]
        )
        articles.append({
            "id": article_id,
            "headline": headline,
            "author": author,
            "word_count": word_count,
            "publish_date": publish_date,
            "source": source,
            "content": content
        })
    print(f"Total articles parsed: {len(articles)}")
    return articles
