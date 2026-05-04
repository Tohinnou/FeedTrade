import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI

from src import Container
from src.api.routes import register_routes
from src.infrastructure.database import engine, Base, async_session
from src.infrastructure.repositories.article_repository import SQLAlchemyArticleRepository

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
)

# Initialize container without DB session first
container = Container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Update container with DB session & repo
    async with async_session() as session:
        app.state.repo = SQLAlchemyArticleRepository(session)
        app.state.container = container
        container.deps["repo"] = app.state.repo
        # Inject repo into existing use cases
        container._get_sentiment.repo = app.state.repo
        yield
        await session.close()

app = FastAPI(title="FeedTrade", description="Forex sentiment screener", version="1.0.0", lifespan=lifespan)

register_routes(app, container.deps)
