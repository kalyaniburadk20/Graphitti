from .neo4j_client import Neo4jClient
from .schema import CONSTRAINTS


class GraphIngestor:

    def __init__(self):
        self.client = Neo4jClient()

    def setup_schema(self):

        with self.client.driver.session(
            database=self.client.database
        ) as session:

            for query in CONSTRAINTS:
                session.run(query)

    # ---------------------------------------------------------
    # Page
    # ---------------------------------------------------------

    def ingest_page(
        self,
        url: str,
        title: str,
    ):

        query = """
        MERGE (p:Page {url: $url})
        SET p.title = $title
        """

        with self.client.driver.session(
            database=self.client.database
        ) as session:

            session.run(
                query,
                url=url,
                title=title,
            )

    # ---------------------------------------------------------
    # Chunk
    # ---------------------------------------------------------

    def ingest_chunk(
        self,
        chunk_id: str,
        text: str,
        section_heading: str,
        source_url: str,
    ):

        query = """
        MATCH (p:Page {url: $source_url})

        MERGE (c:Chunk {chunk_id: $chunk_id})

        SET
            c.text = $text,
            c.section_heading = $section_heading

        MERGE (p)-[:CONTAINS]->(c)
        """

        with self.client.driver.session(
            database=self.client.database
        ) as session:

            session.run(
                query,
                chunk_id=chunk_id,
                text=text,
                section_heading=section_heading,
                source_url=source_url,
            )

    # ---------------------------------------------------------
    # Entity
    # ---------------------------------------------------------

    def ingest_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
    ):

        query = """
        MERGE (e:Entity {entity_id: $entity_id})

        SET
            e.name = $name,
            e.type = $entity_type
        """

        with self.client.driver.session(
            database=self.client.database
        ) as session:

            session.run(
                query,
                entity_id=entity_id,
                name=name,
                entity_type=entity_type,
            )

    # ---------------------------------------------------------
    # Chunk -> Entity
    # ---------------------------------------------------------

    def ingest_chunk_entity(
        self,
        chunk_id: str,
        entity_id: str,
    ):

        query = """
        MATCH (c:Chunk {chunk_id: $chunk_id})
        MATCH (e:Entity {entity_id: $entity_id})

        MERGE (c)-[:MENTIONS]->(e)
        """

        with self.client.driver.session(
            database=self.client.database
        ) as session:

            session.run(
                query,
                chunk_id=chunk_id,
                entity_id=entity_id,
            )

    # ---------------------------------------------------------
    # Claim
    # ---------------------------------------------------------

    def ingest_claim(
        self,
        claim: dict,
    ):

        query = """
        MATCH (subject:Entity {
            entity_id: $subject_entity_id
        })

        MATCH (object:Entity {
            entity_id: $object_entity_id
        })

        MATCH (chunk:Chunk {
            chunk_id: $chunk_id
        })

        MERGE (c:Claim {
            claim_id: $claim_id
        })

        SET
            c.predicate = $predicate,
            c.confidence = $confidence,
            c.source_sentence = $source_sentence,
            c.source_url = $source_url,
            c.extracted_at = $extracted_at

        MERGE (c)-[:ABOUT_SUBJECT]->(subject)

        MERGE (c)-[:ABOUT_OBJECT]->(object)

        MERGE (c)-[:EXTRACTED_FROM]->(chunk)
        """

        with self.client.driver.session(
            database=self.client.database
        ) as session:

            session.run(
                query,
                **claim,
            )

    def create_semantic_edge(
        self,
        subject_entity_id: str,
        object_entity_id: str,
        predicate: str,
        claim_id: str,
    ):
        allowed_predicates = {
            "USES",
            "DEPENDS_ON",
            "BUILT_ON",
            "SUPPORTS",
            "REQUIRES",
            "PROVIDES",
            "INCLUDES",
            "IMPLEMENTS",
            "REPLACES",
            "COMPATIBLE_WITH",
            "INTEGRATES_WITH",
            "VALIDATES",
            "TESTED_WITH",
        }

        if predicate not in allowed_predicates:
            return

        # Relationship types cannot safely be passed
        # as ordinary Cypher parameters, so construct
        # this query only from our controlled vocabulary.
        query = f"""
    MATCH (subject:Entity {{
        entity_id: $subject_entity_id
    }})

    MATCH (object:Entity {{
        entity_id: $object_entity_id
    }})

    MATCH (claim:Claim {{
        claim_id: $claim_id
    }})

    MERGE (subject)-[r:{predicate}]->(object)

    SET r.claim_id = $claim_id,
        r.confidence = claim.confidence,
        r.source_url = claim.source_url

        """

        with self.client.driver.session(
            database=self.client.database
        ) as session:

            session.run(
                query,
                subject_entity_id=subject_entity_id,
                object_entity_id=object_entity_id,
                claim_id=claim_id,
            )

    # ---------------------------------------------------------
    # Close
    # ---------------------------------------------------------

    def close(self):
        self.client.close()