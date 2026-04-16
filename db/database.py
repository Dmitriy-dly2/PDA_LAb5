from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
import os
import json

# =========================
# BASE + ENGINE
# =========================

Base = declarative_base()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db/news.db")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


def get_session():
    return SessionLocal()


# =========================
# MODEL
# =========================

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String)
    author = Column(String)
    url = Column(String, unique=True)
    complexity = Column(String)
    habr_id = Column(String, unique=True)
    label = Column(String)
    tags = Column(String)
    reading_time = Column(Integer)


# =========================
# INIT DB
# =========================

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()


# =========================
# HELPERS
# =========================

def serialize_tags(tags):
    if not tags:
        return "[]"
    return json.dumps(tags, ensure_ascii=False)


def deserialize_tags(tags_str):
    if not tags_str:
        return []
    try:
        return json.loads(tags_str)
    except Exception:
        return []


def create_news(item: dict):
    session = get_session()
    try:
        item = item.copy()
        item["tags"] = serialize_tags(item.get("tags"))

        news = News(**item)
        session.add(news)
        session.commit()
        session.refresh(news)
        return news

    except IntegrityError:
        session.rollback()
        return None

    finally:
        session.close()


def get_by_habr_id(habr_id: str):
    session = get_session()
    try:
        return session.query(News).filter(News.habr_id == habr_id).first()
    finally:
        session.close()


def exists(habr_id: str) -> bool:
    return get_by_habr_id(habr_id) is not None


def update_label(habr_id: str, new_label: str):
    session = get_session()
    try:
        news = session.query(News).filter(News.habr_id == habr_id).first()

        if not news:
            return None

        news.label = new_label
        session.commit()
        session.refresh(news)
        return news

    finally:
        session.close()


def upsert_news(item: dict):
    session = get_session()
    try:
        item = item.copy()
        item["tags"] = serialize_tags(item.get("tags"))

        news = session.query(News).filter(
            News.habr_id == item["habr_id"]
        ).first()

        if news:
            for k, v in item.items():
                setattr(news, k, v)
        else:
            news = News(**item)
            session.add(news)

        session.commit()
        session.refresh(news)
        return news

    finally:
        session.close()