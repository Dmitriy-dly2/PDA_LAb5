from bottle import route, request, redirect, template, run, TEMPLATE_PATH
import os
import sys
import string
import json
from naive_bayes import NaiveBayesClassifier
from db.database import get_session, News, init_db, update_label
from sklearn.model_selection import train_test_split

# --- PATHS ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

TEMPLATE_DIR = os.path.join(CURRENT_DIR, 'templates')
if TEMPLATE_DIR not in TEMPLATE_PATH:
    TEMPLATE_PATH.insert(0, TEMPLATE_DIR)

# --- INIT DB ---
try:
    init_db()
except Exception as e:
    print(f"Ошибка инициализации БД: {e}")


# --- CLEAN ---
def clean(s):
    if not s:
        return ""
    translator = str.maketrans("", "", string.punctuation)
    return s.translate(translator).lower()


# =========================
# INDEX
# =========================
@route('/')
def index():
    return redirect('/news')


# =========================
# NEWS LIST
# =========================
@route('/news')
def news_list():
    s = get_session()

    try:
        print("\n=== NEWS LIST DEBUG ===")

        rows = s.query(News).filter(
            News.label.is_(None)).all()

        if rows:
            for n in rows[:5]:
                print(f"ID: {n.id}, Label: '{n.label}', Title: {n.title[:50]}")

        return template('news_template', rows=rows, is_recommendations=False)

    finally:
        s.close()


# =========================
# ADD LABEL (manual training data)
# =========================
@route('/add_label')
def add_label():
    label = request.query.get('label')
    habr_id = request.query.get('id')

    print(f"DEBUG add_label: habr_id={habr_id}, label={label}")

    result = update_label(habr_id, label)

    print(f"DEBUG add_label result: {result}")

    return redirect('/news')


# =========================
# RECOMMENDATIONS (ML PART)
# =========================
@route('/recommendations')
def recommendations():
    s = get_session()
    try:
        print("\n=== RECOMMENDATIONS DEBUG ===")

        # Ищем статьи с label в одном из этих значений
        labeled = s.query(News).filter(
            News.label.in_(['good', 'maybe', 'never'])
        ).all()

        print(f"DEBUG: Найдено помеченных статей: {len(labeled)}")

        if labeled:
            label_counts = {}
            for n in labeled:
                label_counts[n.label] = label_counts.get(n.label, 0) + 1
            print(f"DEBUG: Распределение меток: {label_counts}")

        labels_set = set(n.label for n in labeled)

        if len(labels_set) < 2:
            return "<h3>❗ Нужно минимум 2 класса: good и never</h3>"

        # Подготовка данных
        x_data = []
        y_data = []

        for n in labeled:
            x_data.append({
                "title": n.title,
                "tags": json.loads(n.tags) if n.tags else [],
                "complexity": n.complexity,
                "reading_time": n.reading_time
            })
            y_data.append(n.label)

        # При малом количестве данных (< 50) используем все для обучения
        if len(x_data) < 50:
            x_train = x_data
            y_train = y_data
            accuracy = None  # Не рассчитываем точность на обучающем наборе
        else:
            # При большом количестве разделяем 80/20
            from sklearn.model_selection import train_test_split
            x_train, x_test, y_train, y_test = train_test_split(
                x_data, y_data, test_size=0.2, random_state=42
            )

            # Обучаем модель для расчета точности
            temp_model = NaiveBayesClassifier(alpha=0.5)
            temp_model.fit(x_train, y_train)

            try:
                accuracy = temp_model.evaluate_accuracy(x_test, y_test)
                accuracy = round(accuracy * 100, 2)
                print(f"Точность на тестовом наборе: {accuracy}%")
            except Exception as e:
                print(f"Ошибка при вычислении точности: {e}")
                accuracy = 0

        # Обучаем на всех данных
        model = NaiveBayesClassifier(alpha=0.5)
        model.fit(x_train, y_train)

        unlabeled = s.query(News).filter(
            News.label.is_(None)).all()

        print(f"Найдено {len(unlabeled)} неразмеченных статей")

        if not unlabeled:
            return "<h3>❗ Нет неразмеченных статей</h3>"

        x_test = []
        for n in unlabeled:
            x_test.append({
                "title": n.title,
                "tags": json.loads(n.tags) if n.tags else [],
                "complexity": n.complexity,
                "reading_time": n.reading_time
            })

        preds = model.predict(x_test)

        for i, news in enumerate(unlabeled):
            news.predicted_label = preds[i]

        order = {'good': 0, 'maybe': 1, 'never': 2}
        sorted_news = sorted(
            unlabeled,
            key=lambda x: order.get(x.predicted_label, 3)
        )

        return template(
            'news_template',
            rows=sorted_news,
            is_recommendations=True,
            accuracy=accuracy
        )

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return f"<h3>Ошибка: {e}</h3>"
    finally:
        s.close()


# =========================
# RESET LABELS
# =========================
@route('/reset_labels')
def reset_labels():
    s = get_session()
    try:
        s.query(News).update({News.label: None})
        s.commit()
        print("LABELS RESET")
    finally:
        s.close()

    return "OK"


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    print(f"Ищу шаблоны здесь: {TEMPLATE_DIR}")
    print("Сервер запущен! Перейди по ссылке: http://localhost:8080/news")
    run(host='localhost', port=8080, debug=False, reloader=False)
