import pickle
import pandas as pd
import numpy as np

from scipy.sparse import hstack
from sklearn.model_selection import train_test_split
from sklearn.metrics import ndcg_score

# =====================================================
# ЗАГРУЗКА ДАННЫХ
# =====================================================

ratings = pd.read_csv("Files/Ratings_cleaned.csv")
books = pd.read_csv("Files/Books_cleaned.csv")

# =====================================================
# ЗАГРУЗКА МОДЕЛЕЙ
# =====================================================

with open("models/svd_model.pkl", "rb") as f:
    svd = pickle.load(f)

with open("models/linreg_model.pkl", "rb") as f:
    linreg = pickle.load(f)

with open("models/tfidf.pkl", "rb") as f:
    tfidf = pickle.load(f)

with open("models/ohe.pkl", "rb") as f:
    ohe = pickle.load(f)

# =====================================================
# МАТРИЦА ПРИЗНАКОВ (КНИГИ)
# =====================================================

books = books.copy().reset_index(drop=True)

title_vec = tfidf.transform(books["Book-Title"].fillna(""))
cat = ohe.transform(books[["Book-Author", "Publisher"]])

X_books = hstack([title_vec, cat])

# =====================================================
# Рекомендация для пользователя, у которого в исходном датасете больше всего нулевых оценок
# =====================================================

zero_ratings = ratings[ratings["Book-Rating"] == 0]

if len(zero_ratings) > 0:
    user_zero = zero_ratings["User-ID"].value_counts().idxmax()
else:
    user_zero = ratings.groupby("User-ID")["Book-Rating"].mean().idxmin()

user_zero_data = ratings[ratings["User-ID"] == user_zero]
seen_books = set(user_zero_data["ISBN"])

# -----------------------------------------------------
# ШАГ 1: сначала фильтруем книги (ВАЖНОЕ ИСПРАВЛЕНИЕ)
# -----------------------------------------------------

candidate_zero = books[~books["ISBN"].isin(seen_books)].copy()
candidate_zero = candidate_zero.reset_index(drop=True)

# -----------------------------------------------------
# ШАГ 2: предсказание SVD
# -----------------------------------------------------

candidate_zero["svd_score"] = [
    svd.predict(user_zero, isbn).est
    for isbn in candidate_zero["ISBN"]
]

# -----------------------------------------------------
# ШАГ 3: фильтрация
# -----------------------------------------------------

filtered_zero = candidate_zero[candidate_zero["svd_score"] >= 8].copy()
filtered_zero = filtered_zero.reset_index(drop=True)

# -----------------------------------------------------
# ШАГ 4: построение признаков только для отфильтрованных
# -----------------------------------------------------

title_vec_zero = tfidf.transform(filtered_zero["Book-Title"].fillna(""))
cat_zero = ohe.transform(filtered_zero[["Book-Author", "Publisher"]])

X_zero = hstack([title_vec_zero, cat_zero])

# -----------------------------------------------------
# ШАГ 5: предсказание линейной регрессии
# -----------------------------------------------------

filtered_zero["linreg_score"] = linreg.predict(X_zero)

# сортировка
rec_zero_user = filtered_zero.sort_values("linreg_score", ascending=False)

print("\n📌 RECOMMENDATION #1 (ZERO USER)")
print(rec_zero_user[["Book-Title", "svd_score", "linreg_score"]].head(10))


# =====================================================
# Рекомендация для пользователя, который оценил больше всего книг
# =====================================================

user_most = ratings["User-ID"].value_counts().idxmax()
user_most_data = ratings[ratings["User-ID"] == user_most]

# разделение на train/test (ВАЖНО для оценки)
train, test = train_test_split(user_most_data, test_size=0.2, random_state=42)

test_books = set(test["ISBN"])
seen_train = set(train["ISBN"])

candidate_active = books[~books["ISBN"].isin(seen_train)].copy()

# предсказание SVD
candidate_active["svd_score"] = [
    svd.predict(user_most, isbn).est
    for isbn in candidate_active["ISBN"]
]

top10_active = candidate_active.sort_values("svd_score", ascending=False).head(10)

# =====================================================
# Метрики
# =====================================================

hit_rate = sum(isbn in test_books for isbn in top10_active["ISBN"]) / 10

relevance = np.array([
    1 if isbn in test_books else 0
    for isbn in top10_active["ISBN"]
]).reshape(1, -1)

dcg = ndcg_score(relevance, [top10_active["svd_score"].values])

print("\n📌 RECOMMENDATION #2 (ACTIVE USER)")
print(top10_active[["Book-Title", "svd_score"]])

print("\n📊 METRICS (ACTIVE USER)")
print("Hit Rate:", hit_rate)
print("DCG:", dcg)