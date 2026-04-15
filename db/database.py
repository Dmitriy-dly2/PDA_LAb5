from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError

# =========================
# BASE + ENGINE
# =========================

Base = declarative_base()

engine = create_engine(
    "sqlite:///db/news.db",
    echo=False
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


# =========================
# INIT DB
# =========================

def init_db():
    Base.metadata.create_all(bind=engine)


# =========================
# CRUD OPERATIONS
# =========================

def create_news(item: dict):
    """
    Добавление новости.
    item = {
        title, author, url, complexity, habr_id, label
    }
    """
    session = get_session()
    try:
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
    """
    Если запись существует → можно обновить
    Если нет → создать
    """
    session = get_session()
    try:
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