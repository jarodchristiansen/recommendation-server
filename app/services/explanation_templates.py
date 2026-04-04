"""User-facing explanation copy. Keep strings here so the orchestrator stays readable."""


def same_author(rec_author: str) -> str:
    return f'Another title by {rec_author} — same author as your seed book.'


def thematic_overlap(shared_labels: list[str]) -> str:
    top = shared_labels[:3]
    joined = ", ".join(f'"{s}"' for s in top)
    return f"Shares thematic overlap in {joined} with your seed book."


def shelf_popular(shelf: int) -> str:
    return f"{shelf:,} readers have shelved this — a widely loved title in related territory."


def highly_rated(avg: float, *, had_subject_overlap: bool) -> str:
    if had_subject_overlap:
        return (
            f"Highly rated ({avg:.1f} avg) with overlapping subject tags in the same genre space."
        )
    return f"Highly rated ({avg:.1f} avg) — sits in a similar neighborhood of the catalog as your pick."


def embedding_tight() -> str:
    return "Very close embedding match to your book."


def embedding_strong() -> str:
    return "Strong embedding similarity to your book."


def embedding_soft() -> str:
    return "Softer embedding match — check the subject tags fit your taste."


def rec_lane_from_tags(tags: list[str]) -> str:
    joined = ", ".join(tags[:3])
    return f"Often tagged with {joined} — a similar reading lane."


def embedding_plus_tags(strength_sentence: str, tags: list[str]) -> str:
    joined = ", ".join(tags[:3])
    return f"{strength_sentence} Often tagged with {joined} — worth a look if the themes appeal."


def embedding_no_tags(strength_sentence: str) -> str:
    return f"{strength_sentence} Browse the subjects and description to see if it fits."


def generic_semantic() -> str:
    return "Matched by semantic similarity across themes and narrative scope."
