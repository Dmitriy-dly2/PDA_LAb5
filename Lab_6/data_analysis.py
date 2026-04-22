import pandas as pd  # импорт библиотеки для работы с таблицами (DataFrame)
import matplotlib.pyplot as plt  # импорт библиотеки для построения графиков
import seaborn as sns  # импорт библиотеки для более красивых визуализаций

# Загружаем датасет с рейтингами книг из CSV-файла
ratings = pd.read_csv("Files/Ratings.csv")

ratings.head()  # вывод первых 5 строк таблицы для быстрого просмотра данных
ratings.info()  # информация о структуре данных (типы столбцов, пропуски)
print(ratings.describe().T)  # статистическое описание числовых колонок (транспонированное для удобства)

# Настройка визуального стиля графиков
sns.set_context("notebook")  # оптимизация отображения для ноутбуков (размеры элементов)
sns.set_style("whitegrid")  # стиль с белым фоном и сеткой

# Строим гистограмму распределения рейтингов
ratings["Book-Rating"].hist()  # создаем гистограмму по столбцу рейтингов
plt.xlabel("Rating value")  # подпись оси X
plt.ylabel("Rating count")  # подпись оси Y
plt.savefig("Rating distribution.png")  # сохраняем график в файл

# Загружаем датасет с информацией о книгах
books = pd.read_csv("Files/Books.csv")

books.head()  # просмотр первых строк
books.info()  # структура датасета

# Считаем количество книг по годам публикации и выводим 10 самых редких годов
print(books["Year-Of-Publication"].value_counts().sort_values(ascending=True)[:10])

# Находим строки, где год публикации содержит нечисловые значения
print(books[books["Year-Of-Publication"].map(str).str.match("[^0-9]")])

# Находим книги с пропущенными значениями автора или издателя
print(books[(books["Book-Author"].isnull()) | (books["Publisher"].isnull())])