import os
import numpy as np
import pandas as pd
import pickle

from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from surprise import accuracy

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split as sk_train_test_split
from sklearn.metrics import mean_absolute_error

from scipy.sparse import hstack

# =====================================================
# 📁 ПАПКА ДЛЯ МОДЕЛЕЙ
# =====================================================

os.makedirs("models", exist_ok=True)

# =====================================================
# 📌 ЗАГРУЗКА ДАННЫХ
# =====================================================

ratings = pd.read_csv("Files/Ratings_cleaned.csv")
books = pd.read_csv("Files/Books_cleaned.csv")

# =====================================================
# 🤖 1. SVD
# =====================================================

book_counts = ratings["ISBN"].value_counts()
user_counts = ratings["User-ID"].value_counts()

ratings_svd = ratings[
    ratings["ISBN"].isin(book_counts[book_counts >= 1].index) &
    ratings["User-ID"].isin(user_counts[user_counts >= 1].index)
]

reader = Reader(rating_scale=(1, 10))

data = Dataset.load_from_df(
    ratings_svd[["User-ID", "ISBN", "Book-Rating"]],
    reader
)

trainset, testset = train_test_split(data, test_size=0.2)

svd = SVD(n_factors=120, n_epochs=25)
svd.fit(trainset)

preds = svd.test(testset)
svd_mae = accuracy.mae(preds)

print("SVD MAE:", svd_mae)

# save SVD
with open("models/svd_model.pkl", "wb") as f:
    pickle.dump(svd, f)

# =====================================================
# 📊 2. LINEAR REGRESSION (СТАБИЛЬНАЯ ВЕРСИЯ)
# =====================================================

# target = средний рейтинг книги
book_avg = ratings.groupby("ISBN")["Book-Rating"].mean().reset_index()
book_avg.columns = ["ISBN", "target"]

data_lr = books.merge(book_avg, on="ISBN")

# -------------------------
# TEXT FEATURES (TF-IDF)
# -------------------------
tfidf = TfidfVectorizer(max_features=500)
title_vec = tfidf.fit_transform(data_lr["Book-Title"].fillna(""))

# -------------------------
# CATEGORICAL FEATURES
# -------------------------
encoder = OneHotEncoder(handle_unknown="ignore")
cat = encoder.fit_transform(
    data_lr[["Book-Author", "Publisher"]]
)

# -------------------------
# TARGET (СТАБИЛИЗАЦИЯ)
# -------------------------
y = np.clip(data_lr["target"].values, 1, 10)

# -------------------------
# FEATURE MATRIX (БЕЗ YEAR!)
# -------------------------
X = hstack([title_vec, cat])

# -------------------------
# TRAIN / TEST
# -------------------------
X_train, X_test, y_train, y_test = sk_train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -------------------------
# MODEL (СТАБИЛЬНАЯ SGD)
# -------------------------
linreg = SGDRegressor(
    max_iter=5000,
    tol=1e-4,
    learning_rate="adaptive",
    eta0=0.01
)

linreg.fit(X_train, y_train)

# -------------------------
# EVALUATION
# -------------------------
preds_lr = linreg.predict(X_test)
lr_mae = mean_absolute_error(y_test, preds_lr)

print("Linear Regression MAE:", lr_mae)

# =====================================================
# 💾 SAVE EVERYTHING
# =====================================================

with open("models/linreg_model.pkl", "wb") as f:
    pickle.dump(linreg, f)

with open("models/tfidf.pkl", "wb") as f:
    pickle.dump(tfidf, f)

with open("models/ohe.pkl", "wb") as f:
    pickle.dump(encoder, f)

print("✔ Models saved to /models")