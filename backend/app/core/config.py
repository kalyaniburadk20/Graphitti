import os


class Settings:
    APP_NAME: str = "Graphitti"
    VERSION: str = "0.1.0"

    MAX_CRAWL_DEPTH: int = 2
    MAX_PAGES: int = 50

    NEO4J_URI: str = os.getenv(
        "NEO4J_URI",
        "bolt://localhost:7687"
    )

    NEO4J_USERNAME: str = os.getenv(
        "NEO4J_USERNAME",
        "neo4j"
    )

    NEO4J_PASSWORD: str = os.getenv(
        "NEO4J_PASSWORD",
        "password"
    )


settings = Settings()