import math
import re
from collections import Counter, defaultdict


class NaiveBayesClassifier:
    def __init__(self, alpha=1.0):
        self.alpha = alpha

        self.class_counts = Counter()
        self.word_counts = defaultdict(Counter)
        self.words_per_class = Counter()
        self.vocabulary = set()

    # =========================
    # FEATURE ENGINEERING
    # =========================
    @staticmethod
    def build_features(title, tags, complexity, reading_time):
        features = []

        # TITLE - слова и биграммы
        words = re.findall(r"[a-zа-я0-9]+", title.lower())
        features += [f"title_{w}" for w in words]

        # Биграммы из title
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            features.append(f"bigram_{bigram}")

        # Длина title
        title_len = len(words)
        if title_len <= 3:
            features.append("title_short")
        elif title_len <= 7:
            features.append("title_medium")
        else:
            features.append("title_long")

        # TAGS - более точная обработка
        if tags:
            features.append(f"tag_count_{len(tags)}")
            for tag in tags:
                clean = re.sub(r"[^a-zа-я0-9 ]", "", tag.lower()).strip()
                if clean:
                    features.append(f"tag_{clean}")

        # COMPLEXITY
        if complexity:
            complexity_clean = complexity.lower().strip()
            features.append(f"complexity_{complexity_clean}")

        # READING TIME BUCKET
        if reading_time is not None:
            if reading_time <= 5:
                bucket = "short"
            elif reading_time <= 15:
                bucket = "medium"
            else:
                bucket = "long"

            features.append(f"time_{bucket}")
            # Более точные интервалы
            features.append(f"time_exact_{reading_time}")

        return features

    # =========================
    # TRAINING
    # =========================
    def fit(self, x, y):

        self.class_counts.clear()
        self.word_counts.clear()
        self.words_per_class.clear()
        self.vocabulary.clear()

        for item, label in zip(x, y):

            features = self.build_features(
                item["title"],
                item.get("tags"),
                item.get("complexity"),
                item.get("reading_time")
            )

            self.class_counts[label] += 1

            for f in features:
                self.word_counts[label][f] += 1
                self.words_per_class[label] += 1
                self.vocabulary.add(f)

    # =========================
    # PREDICTION
    # =========================
    def predict(self, x):

        results = []
        total_docs = sum(self.class_counts.values())
        vocab_size = len(self.vocabulary)

        # если модель не обучена
        if total_docs == 0:
            return ["maybe"] * len(x)

        for item in x:

            features = self.build_features(
                item["title"],
                item.get("tags"),
                item.get("complexity"),
                item.get("reading_time")
            )

            scores = {}

            for label in self.class_counts:

                # prior
                log_prob = math.log(self.class_counts[label] / total_docs)

                denominator = self.words_per_class[label] + self.alpha * vocab_size

                for f in features:
                    count = self.word_counts[label][f]

                    prob = (count + self.alpha) / denominator
                    log_prob += math.log(prob)

                scores[label] = log_prob

            results.append(max(scores, key=scores.get))
        return results

    def evaluate_accuracy(self, x, y):

        if len(x) == 0:
            return 0.0

        preds = self.predict(x)

        correct = 0
        for p, true in zip(preds, y):
            if p == true:
                correct += 1

        return correct / len(y)

    # =========================
    # OPTIONAL: PROBABILITIES
    # =========================
    def predict_proba(self, x):

        total_docs = sum(self.class_counts.values())
        vocab_size = len(self.vocabulary)

        results = []

        for item in x:

            features = self.build_features(
                item["title"],
                item.get("tags"),
                item.get("complexity"),
                item.get("reading_time")
            )

            scores = {}

            for label in self.class_counts:

                log_prob = math.log(self.class_counts[label] / total_docs)
                denominator = self.words_per_class[label] + self.alpha * vocab_size

                for f in features:
                    count = self.word_counts[label][f]
                    prob = (count + self.alpha) / denominator
                    log_prob += math.log(prob)

                scores[label] = log_prob

            # softmax normalization
            max_log = max(scores.values())

            exp_scores = {
                k: math.exp(v - max_log)
                for k, v in scores.items()
            }

            total = sum(exp_scores.values())

            probs = {k: v / total for k, v in exp_scores.items()}
            results.append(probs)

        return results