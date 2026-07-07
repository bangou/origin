from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat


@dataclass(frozen=True)
class TemplateMatch:
    label: str
    score: float


@dataclass(frozen=True)
class CandidateLabel:
    label: str
    score: float
    match_source: str
    review_status: str


def _normalized_gray(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.grayscale(image).resize(size)


def score_template_matches(crop: Image.Image, template_dir: Path) -> list[TemplateMatch]:
    matches: list[TemplateMatch] = []
    for path in sorted(template_dir.glob("*.png")):
        with Image.open(path) as template:
            left = _normalized_gray(crop, template.size)
            right = _normalized_gray(template, template.size)
            diff = ImageChops.difference(left, right)
            mean_diff = ImageStat.Stat(diff).mean[0] / 255.0
        matches.append(TemplateMatch(label=path.stem, score=1.0 - mean_diff))

    return sorted(matches, key=lambda item: item.score, reverse=True)


def choose_primary_label(
    card_slot: str,
    matches: list[TemplateMatch],
    used_labels: set[str],
    threshold: float,
) -> CandidateLabel:
    del card_slot
    if not matches:
        return CandidateLabel(
            label="UNKNOWN",
            score=0.0,
            match_source="templates/cards",
            review_status="needs_review",
        )

    top_match = matches[0]
    if top_match.label in used_labels or top_match.score < threshold:
        return CandidateLabel(
            label=top_match.label,
            score=top_match.score,
            match_source="templates/cards",
            review_status="needs_review",
        )

    return CandidateLabel(
        label=top_match.label,
        score=top_match.score,
        match_source="templates/cards",
        review_status="pending",
    )
