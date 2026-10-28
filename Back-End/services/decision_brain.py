"""Regras de consenso do detector neural.

Recebe escores do CLIP e aplica regras explícitas de incerteza, rejeição de
objetos fora do catálogo e consenso entre múltiplas vistas. Os valores usados
são similaridades relativas, não probabilidades calibradas.
"""
from __future__ import annotations


def _biased_scores(scores, catalog_entries):
    return [
        float(score) + float(catalog_entries[idx].get("score_bias", 0.0) or 0.0)
        for idx, score in enumerate(scores)
    ]


def select_label(scores, min_score: float, min_margin: float):
    values = [float(value) for value in scores]
    if not values:
        return None
    ranked = sorted(enumerate(values), key=lambda pair: pair[1], reverse=True)
    best_index, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else -1.0
    margin = best_score - second_score
    if best_score < min_score or margin < min_margin:
        return None
    return best_index, best_score, margin


def _family_fallback(averaged_scores, catalog_entries, min_score, min_margin):
    """Colapsa ambiguidades conhecidas em um rótulo genérico seguro.

    Ex.: PET x squeeze x garrafa plástica pode ser visualmente ambíguo. Se as
    duas melhores hipóteses pertencem à mesma família e a família como um todo
    vence claramente classes externas, retornamos o fallback "Garrafa plástica"
    em vez de inventar o subtipo ou descartar uma garrafa real.
    """
    adjusted = _biased_scores(averaged_scores, catalog_entries)
    ranked = sorted(range(len(adjusted)), key=lambda idx: adjusted[idx], reverse=True)
    if len(ranked) < 2 or adjusted[ranked[0]] < min_score:
        return None
    first, second = ranked[0], ranked[1]
    family = str(catalog_entries[first].get("ambiguity_family", "") or "")
    if not family or family != str(catalog_entries[second].get("ambiguity_family", "") or ""):
        return None

    fallback_idx = next((
        idx for idx, entry in enumerate(catalog_entries)
        if entry.get("ambiguity_family") == family and entry.get("family_fallback")
    ), None)
    if fallback_idx is None:
        return None

    family_members = [
        idx for idx, entry in enumerate(catalog_entries)
        if entry.get("ambiguity_family") == family
    ]
    family_best = max(adjusted[idx] for idx in family_members)
    outside = [adjusted[idx] for idx in range(len(adjusted)) if idx not in family_members]
    outside_best = max(outside) if outside else -1.0
    family_margin = family_best - outside_best
    if family_margin < min_margin:
        return None
    return fallback_idx, family_best, family_margin, family


def decide_class(
    averaged_scores,
    view_scores,
    catalog_entries,
    proposed_group: str,
    *,
    min_score: float,
    min_margin: float,
    cross_group_margin: float,
    min_view_agreement: int,
    reject_scores=None,
    reject_margin: float = 0.0,
    reject_min_score: float = 0.0,
):
    """Retorna decisão global ou ``None`` quando a evidência é incerta."""
    adjusted = _biased_scores(averaged_scores, catalog_entries)
    chosen = select_label(adjusted, min_score, min_margin)
    fallback_family = None
    if chosen is None:
        fallback = _family_fallback(averaged_scores, catalog_entries, min_score, min_margin)
        if fallback is None:
            return None
        class_id, adjusted_score, margin, fallback_family = fallback
        # Evidência do fallback é a melhor hipótese específica da família.
        raw_score = max(
            float(averaged_scores[idx])
            for idx, entry in enumerate(catalog_entries)
            if entry.get("ambiguity_family") == fallback_family
        )
    else:
        class_id, adjusted_score, margin = chosen
        raw_score = float(averaged_scores[class_id])

    if reject_scores:
        reject_best = max(float(value) for value in reject_scores)
        if reject_best >= reject_min_score and (raw_score - reject_best) < reject_margin:
            return None
    else:
        reject_best = None

    class_count = len(catalog_entries)
    if fallback_family:
        votes = sum(
            1 for scores in view_scores
            if catalog_entries[max(
                range(class_count),
                key=lambda idx: float(scores[idx]) + float(catalog_entries[idx].get("score_bias", 0.0) or 0.0),
            )].get("ambiguity_family") == fallback_family
        )
    else:
        votes = sum(
            1
            for scores in view_scores
            if max(
                range(class_count),
                key=lambda idx: float(scores[idx]) + float(catalog_entries[idx].get("score_bias", 0.0) or 0.0),
            ) == class_id
        )
    if votes < min_view_agreement:
        return None

    entry = catalog_entries[class_id]
    chosen_group = entry.get("group", "outros")
    if chosen_group != proposed_group:
        required_votes = max(min_view_agreement, len(view_scores) - 1)
        if margin < cross_group_margin or votes < required_votes:
            return None

    return {
        "class_id": class_id,
        "score": raw_score,
        "adjusted_score": float(adjusted_score),
        "margin": float(margin),
        "reject_score": reject_best,
        "votes": votes,
        "views": len(view_scores),
        "entry": entry,
        "family_fallback": fallback_family,
    }
