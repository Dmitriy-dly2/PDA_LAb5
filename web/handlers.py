import sys
import os
from bottle import route, request, redirect, template, run, TEMPLATE_PATH

# --- BASE PATH ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# templates path
template_path = os.path.join(BASE_DIR, 'web', 'templates')
if template_path not in TEMPLATE_PATH:
    TEMPLATE_PATH.insert(0, template_path)

# --- DB IMPORT ---
from db.database import get_session, News, update_label


# --- ROUTES ---

@route('/test_db')
def test_db():
    s = get_session()
    try:
        rows = s.query(News).filter(News.label == None).all()
        return f"Количество новостей без метки: {len(rows)}"
    finally:
        s.close()


@route('/news')
def news_list():
    s = get_session()
    try:
        rows = s.query(News).filter(
            (News.label == None) | (News.label == 'habr')
        ).all()

        return template('news_template', rows=rows)
    finally:
        s.close()


@route('/add_label')
def add_label():
    label = request.query.get('label')
    news_id = request.query.get('id')

    if not label or not news_id:
        return "Missing label or id"

    # ВАЖНО: используем функцию из database.py
    # но она работает по habr_id, поэтому сначала получаем его

    s = get_session()
    try:
        item = s.query(News).filter(News.id == int(news_id)).first()

        if item:
            update_label(item.habr_id, label)

    finally:
        s.close()

    return redirect('/news')


@route('/recommendations')
def recommendations():
    return template('news_template', rows=[])


@route('/update_news')
def update_news():
    # У тебя тут нет импорта get_news — иначе будет crash
    from parser import get_news  # или откуда он у тебя

    get_news("https://habr.com/ru/articles/", target_count=30)
    return redirect('/news')


# --- RUN ---
if __name__ == "__main__":
    print("Server started: http://localhost:8080/news")
    run(host='localhost', port=8080, debug=True, reloader=True)