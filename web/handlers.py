import sys
import os
from bottle import route, request, redirect, template, run, TEMPLATE_PATH
from sqlalchemy import func

# --- НАСТРОЙКА ПУТЕЙ (Чтобы работало везде) ---

# Находим корень проекта (PDA_LAb5)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Добавляем корень в пути поиска модулей, чтобы импорт "from db.database" работал
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Настраиваем путь к шаблонам относительно этого файла
# Это исправит ошибку "Template not found" на другом компе
template_path = os.path.join(BASE_DIR, 'web', 'templates')
if template_path not in TEMPLATE_PATH:
    TEMPLATE_PATH.insert(0, template_path)

try:
    from db.database import get_session, News
except ImportError:
    print("Ошибка: Не удалось найти db.database. Проверь, что папка db на месте!") 
      
# --- СТРАНИЦЫ САЙТА ---
@route('/test_db')
def test_db():
    s = get_session()
    rows = s.query(News).filter(News.label == None).all()
    return f"Количество новостей в базе: {len(all_news)}"

@route('/news')
def news_list():
    s = get_session()
    try:
        rows = s.query(News).filter((News.label == None) | (News.label == 'habr')).all()
        return template('news_template', rows=rows)
    finally:
        s.close()

@route('/add_label')
def add_label():
    label = request.query.get('label')
    news_id = request.query.get('id')
    
    s = get_session()
    try:
        # Находим конкретную новость и сохраняем твой выбор
        item = s.query(News).filter(News.id == int(news_id)).first()
        if item:
            item.label = label
            s.commit() # Данные сохранены в БД
    finally:
        s.close()
    
    # Возвращаемся обратно: новость с меткой больше не попадет в список
    return redirect('/news')

@route('/recommendations')
def recommendations():
    s = get_session()
    try:
        # Пока ML-классификатор не готов, мы просто передаем пустой список.
        rows = [] 
        
        return template('news_template', rows=rows)
    finally:
        s.close()

@route('/update_news')
def update_news():
    get_news("https://habr.com/ru/articles/", target_count=30)
    return redirect('/news')

# --- ЗАПУСК ---
if __name__ == "__main__":
    print("Сервер запущен! Перейди по ссылке: http://localhost:8080/news")
    run(host='localhost', port=8080, debug=True, reloader=True)