import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


class Neo4jClient:

    def __init__(self):
        self.uri = os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687",
        )

        self.username = os.getenv(
            "NEO4J_USERNAME",
            "neo4j",
        )

        self.password = os.getenv(
            "NEO4J_PASSWORD",
            "",
        )

        self.database = os.getenv(
            "NEO4J_DATABASE",
            "neo4j",
        )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password,
            ),
        )

    def verify_connection(self):
        with self.driver.session(
            database=self.database
        ) as session:

            result = session.run(
                "RETURN 1 AS value"
            )

            return result.single()["value"] == 1

    def close(self):
        self.driver.close()