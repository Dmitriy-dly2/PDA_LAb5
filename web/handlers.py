from bottle import route, request, redirect, template, run, TEMPLATE_PATH
import os, sys, string

# --- ПУТИ ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

TEMPLATE_DIR = os.path.join(CURRENT_DIR, 'templates')
if TEMPLATE_DIR not in TEMPLATE_PATH:
    TEMPLATE_PATH.insert(0, TEMPLATE_DIR)

# --- ИМПОРТЫ ---
from naive_bayes import NaiveBayesClassifier
from db.database import get_session, News
from sqlalchemy import or_

# --- CLEAN ---
def clean(s):
    translator = str.maketrans("", "", string.punctuation)
    return s.translate(translator).lower()

# --- РОУТЫ ---

@route('/')
def index():
    return redirect('/news')


@route('/news')
def news_list():
    s = get_session()
    try:
        print("=== NEWS DEBUG ===")
        print("ВСЕГО В БД:", s.query(News).count())

        all_news = s.query(News).all()
        print("ПЕРВЫЕ МЕТКИ:", [n.label for n in all_news[:10]])

        rows = s.query(News).filter(
            or_(
                News.label == None,
                News.label == '',
                News.label == 'habr'
            )
        ).all()

        print("НЕРАЗМЕЧЕННЫЕ:", len(rows))

        for row in rows:
            row.predicted_label = None

        return template('news_template', rows=rows, is_recommendations=False)

    finally:
        s.close()


@route('/add_label')
def add_label():
    label = request.query.get('label')
    news_id = int(request.query.get('id'))

    s = get_session()
    try:
        item = s.query(News).filter(News.id == news_id).first()
        if item:
            item.label = label
            s.commit()
            print(f"Поставили метку: {label} для id={news_id}")
    finally:
        s.close()

    return redirect('/news')


@route('/recommendations')
def recommendations():
    s = get_session()
    try:
        print("\n=== RECOMMENDATIONS DEBUG ===")

        # --- ОБУЧЕНИЕ ---
        labeled = s.query(News).filter(
            News.label.in_(['good', 'never'])
        ).all()

        print("РАЗМЕЧЕННЫЕ:", len(labeled))
        print("УНИКАЛЬНЫЕ МЕТКИ:", set(n.label for n in labeled))

        if len(set(n.label for n in labeled)) < 2:
            return "<h3>❗ Нужно разметить хотя бы 2 разных класса (good и never)</h3>"

        X_train = [clean(n.title) for n in labeled]
        y_train = [n.label for n in labeled]

        model = NaiveBayesClassifier(alpha=1.0)
        model.fit(X_train, y_train)

        # --- ПРЕДСКАЗАНИЕ ---
        unlabeled = s.query(News).filter(
            or_(
                News.label == None,
                News.label == '',
                News.label == 'habr'
            )
        ).all()

        print("НЕРАЗМЕЧЕННЫЕ:", len(unlabeled))

        X_test = [clean(n.title) for n in unlabeled]
        preds = model.predict(X_test)

        final_preds = []

        for p in preds:
            if p == 'good':
                final_preds.append('good')
            elif p == 'never':
                final_preds.append('never')
            else:
                final_preds.append('maybe')

        print("ПРЕДСКАЗАНИЯ:", preds[:10])

        for i, news in enumerate(unlabeled):
            news.predicted_label = preds[i]

        # --- СОРТИРОВКА ---
        order = {'good': 0, 'maybe': 1, 'never': 2}

        sorted_news = sorted(
            unlabeled,
            key=lambda x: order.get(x.predicted_label, 3)
        )

        return template('news_template', rows=sorted_news, is_recommendations=True)

    finally:
        s.close()


@route('/reset_labels')
def reset_labels():
    s = get_session()
    try:
        s.query(News).update({News.label: None})
        s.commit()
        print("ВСЕ МЕТКИ СБРОШЕНЫ")
    finally:
        s.close()

    return "OK"


if __name__ == "__main__":
    print(f"Шаблоны: {TEMPLATE_DIR}")
    run(host='localhost', port=8080, debug=True, reloader=True)