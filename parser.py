import requests
from bs4 import BeautifulSoup
import time

from db.database import init_db, upsert_news


BASE_URL = "https://habr.com"


def extract_news(soup):
    news_list = []

    articles = soup.find_all("article")

    for article in articles:
        try:
            # TITLE + LINK
            title_tag = article.find("a", class_="tm-title__link")
            if not title_tag:
                continue

            title = title_tag.text.strip()
            link = BASE_URL + title_tag.get("href")

            # AUTHOR
            author_tag = article.find("a", class_="tm-user-info__username")
            author = author_tag.text.strip() if author_tag else "Unknown"

            # ID
            habr_id = link.rstrip("/").split("/")[-1]

            # COMPLEXITY
            complexity_tag = article.find("span", class_="tm-article-complexity__label")
            complexity = complexity_tag.text.strip() if complexity_tag else "-"

            news_list.append({
                "title": title,
                "author": author,
                "url": link,
                "complexity": complexity,
                "habr_id": habr_id,
            })

        except Exception:
            continue

    return news_list


def extract_next_page(soup):
    next_btn = soup.find("a", attrs={"rel": "next"})
    if next_btn:
        return next_btn.get("href")
    return None


def get_news(url, target_count=300):
    news = []
    seen = set()
    max_retries = 3

    while len(news) < target_count:
        print(f"Collecting data from page: {url}")

        retry_count = 0
        while retry_count < max_retries:
            try:
                response = requests.get(url, headers={
                    "User-Agent": "Mozilla/5.0"
                }, timeout=10)

                if not response.ok:
                    print("Request failed:", response.status_code)
                    break

                soup = BeautifulSoup(response.text, "html.parser")

                news_list = extract_news(soup)

                for item in news_list:
                    # защита от дублей
                    if item["habr_id"] in seen:
                        continue

                    seen.add(item["habr_id"])

                    upsert_news(item)
                    news.append(item)

                    if len(news) >= target_count:
                        break

                next_page = extract_next_page(soup)

                if not next_page:
                    break

                url = BASE_URL + next_page

                # Добавляем задержку между запросами для предотвращения блокировки
                time.sleep(2)
                break

            except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 5 * retry_count
                    print(f"Connection timeout. Retrying in {wait_time} seconds... (attempt {retry_count}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to fetch {url} after {max_retries} attempts.")
                    break

        if retry_count >= max_retries:
            break

    return news


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    init_db()

    result = get_news(
        "https://habr.com/ru/articles/",
        target_count=300
    )

    print(f"\nDone. Collected {len(result)} articles.")