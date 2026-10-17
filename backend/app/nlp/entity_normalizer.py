import re


TECH_ALIASES = {
    "fast api": "FastAPI",
    "fastapi": "FastAPI",

    "starlette": "Starlette",

    "pydantic": "Pydantic",

    "httpx": "HTTPX",
    "httpx library": "HTTPX",

    "orjson": "orjson",
    "orjsonresponse": "ORJSONResponse",

    "oauth2": "OAuth2",
    "oauth 2": "OAuth2",

    "json schema": "JSON Schema",
    "json-schema": "JSON Schema",

    "websockets": "WebSockets",

    "swagger": "Swagger",
    "openapi": "OpenAPI",

    "python": "Python",
    "json": "JSON",
"graphql": "GraphQL",
"uvicorn": "Uvicorn",
"typer": "Typer",
"testclient": "TestClient",
"jwt": "JWT",
"cli": "CLI",
"api": "API",
"redoc": "ReDoc",
}


TECHNOLOGY_TYPES = {
    "FastAPI": "FRAMEWORK",
    "Starlette": "LIBRARY",
    "Pydantic": "LIBRARY",
    "HTTPX": "LIBRARY",
    "orjson": "LIBRARY",
    "ORJSONResponse": "RESPONSE_CLASS",
    "OAuth2": "PROTOCOL",
    "JSON Schema": "STANDARD",
    "WebSockets": "PROTOCOL",
    "Swagger": "TOOL",
    "OpenAPI": "STANDARD",
    "Python": "PROGRAMMING_LANGUAGE",
    "JSON": "DATA_FORMAT",
"GraphQL": "API_QUERY_LANGUAGE",
"Uvicorn": "SERVER",
"Typer": "CLI_FRAMEWORK",
"TestClient": "TESTING_TOOL",
"JWT": "AUTHENTICATION_STANDARD",
"CLI": "INTERFACE",
"API": "API",
"ReDoc": "DOCUMENTATION_TOOL",
}


def normalize_entity(text: str) -> str:
    cleaned = text.strip()

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    )

    key = cleaned.lower()

    return TECH_ALIASES.get(
        key,
        cleaned,
    )


def map_entity_type(
    normalized_text: str,
    spacy_label: str,
) -> str:

    if normalized_text in TECHNOLOGY_TYPES:
        return TECHNOLOGY_TYPES[
            normalized_text
        ]

    return spacy_label