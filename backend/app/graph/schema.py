CONSTRAINTS = [
    """
    CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
    FOR (e:Entity)
    REQUIRE e.entity_id IS UNIQUE
    """,

    """
    CREATE CONSTRAINT page_url_unique IF NOT EXISTS
    FOR (p:Page)
    REQUIRE p.url IS UNIQUE
    """,

    """
    CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
    FOR (c:Chunk)
    REQUIRE c.chunk_id IS UNIQUE
    """,

    """
    CREATE CONSTRAINT claim_id_unique IF NOT EXISTS
    FOR (c:Claim)
    REQUIRE c.claim_id IS UNIQUE
    """,
]