import re


class AnswerClaimParser:

    RELATION_PATTERNS = {
        "depends on": "DEPENDS_ON",
        "uses": "USES",
        "supports": "SUPPORTS",
        "provides": "PROVIDES",
        "built on": "BUILT_ON",
        "compatible with": "COMPATIBLE_WITH",
        "validates": "VALIDATES",
        "tested with": "TESTED_WITH",
        "tested using": "TESTED_WITH",
    }

    def parse(
        self,
        answer: str,
    ) -> list[dict]:

        claims = []

        sentences = [
            sentence.strip()
            for sentence in re.split(
                r"[.!?]+",
                answer,
            )
            if sentence.strip()
        ]

        for sentence in sentences:

            lowered = sentence.lower()

            for phrase, predicate in (
                self.RELATION_PATTERNS.items()
            ):

                match = re.search(
                    rf"\b{re.escape(phrase)}\b",
                    lowered,
                )

                if not match:
                    continue

                subject = (
                    sentence[:match.start()]
                    .strip()
                )

                object_text = (
                    sentence[match.end():]
                    .strip()
                )

                if not subject or not object_text:
                    continue

                # -------------------------------------------------
                # Handle coordinated objects:
                #
                # FastAPI depends on Pydantic and Starlette.
                #
                # becomes two claims.
                # -------------------------------------------------

                object_parts = re.split(
                    r"\s+\band\b\s+",
                    object_text,
                    flags=re.IGNORECASE,
                )

                object_parts = [
                    part.strip(
                        " ,;:"
                    )
                    for part in object_parts
                    if part.strip(
                        " ,;:"
                    )
                ]

                for object_part in object_parts:

                    claims.append(
                        {
                            "subject": subject,
                            "predicate": predicate,
                            "object": object_part,
                        }
                    )

                break

        return claims