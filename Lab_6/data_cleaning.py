import pandas as pd  # работа с таблицами

# Загружаем исходные данные
ratings_raw = pd.read_csv("Files/Ratings.csv")  # оригинальные рейтинги (с нулями)
books = pd.read_csv("Files/Books.csv", dtype={"Year-Of-Publication": str})  # год как строка

# -------------------------
# Очистка таблицы Books
# -------------------------

# Преобразуем год в число (ошибки → NaN)
books["Year-Of-Publication"] = pd.to_numeric(
    books["Year-Of-Publication"], errors="coerce"
)

# Удаляем некорректные года
books = books[
    (books["Year-Of-Publication"] >= 1900) &
    (books["Year-Of-Publication"] <= 2026)
]

# Удаляем строки с пропусками автора или издателя
books = books.dropna(subset=["Book-Author", "Publisher"])

# Удаляем ненужные колонки (картинки)
books = books.drop(columns=["Image-URL-S", "Image-URL-M", "Image-URL-L"])

# -------------------------
# Очистка таблицы Ratings
# -------------------------

# Удаляем нулевые рейтинги (это не оценки)
ratings = ratings_raw[ratings_raw["Book-Rating"] != 0]

# Удаляем книги с одной оценкой
book_counts = ratings["ISBN"].value_counts()
ratings = ratings[ratings["ISBN"].isin(book_counts[book_counts > 1].index)]

# Удаляем пользователей с одной оценкой
user_counts = ratings["User-ID"].value_counts()
ratings = ratings[ratings["User-ID"].isin(user_counts[user_counts > 1].index)]

# -------------------------
# Сохранение очищенных данных
# -------------------------

books.to_csv("Files/Books_cleaned.csv", index=False)  # сохраняем очищенные книги
ratings.to_csv("Files/Ratings_cleaned.csv", index=False)  # сохраняем очищенные рейтинги

print("Очищенные данные сохранены")