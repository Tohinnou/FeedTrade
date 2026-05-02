import logging

from fastapi import FastAPI

from src import Container
from src.api.routes import register_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
)

app = FastAPI(title="FeedTrade", description="Forex sentiment screener", version="1.0.0")

container = Container()


@app.on_event("startup")
async def startup():
    logging.getLogger("feedtrade").info("FeedTrade v1.0.0 startup — Clean Architecture")


register_routes(app, container.deps)
