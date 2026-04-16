import math
from collections import Counter, defaultdict

class NaiveBayesClassifier:
    def __init__(self, alpha=1.0):
        self.alpha = alpha
        self.class_counts = Counter()      # Количество документов в каждом классе
        self.word_counts = defaultdict(Counter) # Сколько раз слово встретилось в классе
        self.words_per_class = Counter()   # Общее количество слов в каждом классе
        self.vocabulary = set()            # Список всех уникальных слов

    def fit(self, X, y):
        """ Обучение классификатора """
        # Сбрасываем старые данные, если они были
        self.class_counts.clear()
        self.word_counts.clear()
        self.words_per_class.clear()
        self.vocabulary.clear()

        for text, label in zip(X, y):
            self.class_counts[label] += 1
            words = text.split()
            for word in words:
                self.word_counts[label][word] += 1
                self.words_per_class[label] += 1
                self.vocabulary.add(word)

    def predict(self, X):
        """ Предсказание меток для списка текстов X """
        predictions = []
        d = len(self.vocabulary)
        total_docs = sum(self.class_counts.values())
        
        # Если данных для обучения нет, возвращаем дефолт
        if total_docs == 0:
            return ["maybe"] * len(X)

        for text in X:
            words = text.split()
            probs = {}

            for label in self.class_counts:
                # Априорная вероятность: ln(P(C))
                log_prob = math.log(self.class_counts[label] / total_docs)
                
                # Знаменатель для формулы Лапласа (один для всех слов в этом классе)
                # n_c + alpha * d
                denominator = self.words_per_class[label] + self.alpha * d
                
                for word in words:
                    if word in self.vocabulary:
                        # Числитель: n_ic + alpha
                        n_ic = self.word_counts[label][word]
                        # Считаем вероятность слова в классе
                        word_prob = (n_ic + self.alpha) / denominator
                        log_prob += math.log(word_prob)
                
                probs[label] = log_prob
            
            # Находим класс с максимальной логарифмической вероятностью
            # Если probs пуст (редко), вернем 'maybe'
            if not probs:
                predictions.append("maybe")
            else:
                predictions.append(max(probs, key=probs.get))
        
        return predictions