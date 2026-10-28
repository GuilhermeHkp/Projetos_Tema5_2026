import unittest

from services.decision_brain import decide_class, select_label


CATALOG = [
    {"display_name": "Tesoura", "group": "papelaria"},
    {"display_name": "Chave de fenda", "group": "ferramenta"},
    {"display_name": "Escova de dentes", "group": "pessoal"},
]


class DecisionBrainTests(unittest.TestCase):
    def test_rejects_small_margin(self):
        self.assertIsNone(select_label([0.30, 0.29, 0.10], 0.20, 0.035))

    def test_rejects_weak_cross_group_change(self):
        views = [[0.25, 0.30, 0.10], [0.24, 0.30, 0.11], [0.25, 0.29, 0.10]]
        avg = [sum(v[i] for v in views) / 3 for i in range(3)]
        self.assertIsNone(decide_class(
            avg, views, CATALOG, "papelaria",
            min_score=0.20, min_margin=0.035,
            cross_group_margin=0.070, min_view_agreement=2,
        ))

    def test_accepts_strong_cross_group_correction(self):
        views = [[0.10, 0.42, 0.08], [0.11, 0.43, 0.09], [0.12, 0.44, 0.08]]
        avg = [sum(v[i] for v in views) / 3 for i in range(3)]
        decision = decide_class(
            avg, views, CATALOG, "papelaria",
            min_score=0.20, min_margin=0.035,
            cross_group_margin=0.070, min_view_agreement=2,
        )
        self.assertIsNotNone(decision)
        self.assertEqual(decision["entry"]["display_name"], "Chave de fenda")
        self.assertEqual(decision["votes"], 3)

    def test_accepts_same_group_with_consensus(self):
        views = [[0.40, 0.20, 0.10], [0.39, 0.21, 0.11], [0.23, 0.22, 0.10]]
        avg = [sum(v[i] for v in views) / 3 for i in range(3)]
        decision = decide_class(
            avg, views, CATALOG, "papelaria",
            min_score=0.20, min_margin=0.035,
            cross_group_margin=0.070, min_view_agreement=2,
        )
        self.assertIsNotNone(decision)
        self.assertEqual(decision["entry"]["display_name"], "Tesoura")

    def test_rejects_out_of_catalog_when_negative_concept_is_close(self):
        views = [[0.31, 0.15, 0.10], [0.32, 0.14, 0.11], [0.30, 0.15, 0.10]]
        avg = [sum(v[i] for v in views) / 3 for i in range(3)]
        self.assertIsNone(decide_class(
            avg, views, CATALOG, "papelaria",
            min_score=0.20, min_margin=0.035,
            cross_group_margin=0.070, min_view_agreement=2,
            reject_scores=[0.305, 0.12], reject_margin=0.025, reject_min_score=0.18,
        ))

    def test_accepts_known_when_it_beats_reject_bank(self):
        views = [[0.43, 0.16, 0.10], [0.42, 0.15, 0.11], [0.44, 0.14, 0.10]]
        avg = [sum(v[i] for v in views) / 3 for i in range(3)]
        decision = decide_class(
            avg, views, CATALOG, "papelaria",
            min_score=0.20, min_margin=0.035,
            cross_group_margin=0.070, min_view_agreement=2,
            reject_scores=[0.25, 0.19], reject_margin=0.025, reject_min_score=0.18,
        )
        self.assertIsNotNone(decision)
        self.assertEqual(decision["entry"]["display_name"], "Tesoura")

    def test_collapses_ambiguous_bottle_subtypes_to_generic_family(self):
        catalog = [
            {"display_name":"Garrafa plástica","group":"recipiente","ambiguity_family":"bottle","family_fallback":True,"score_bias":-0.025},
            {"display_name":"Garrafa PET","group":"recipiente","ambiguity_family":"bottle"},
            {"display_name":"Garrafa esportiva","group":"recipiente","ambiguity_family":"bottle"},
            {"display_name":"Mouse","group":"eletrônico"},
        ]
        views = [
            [0.30, 0.41, 0.40, 0.15],
            [0.29, 0.40, 0.39, 0.16],
            [0.30, 0.39, 0.40, 0.14],
        ]
        avg = [sum(v[i] for v in views) / 3 for i in range(4)]
        decision = decide_class(
            avg, views, catalog, "recipiente",
            min_score=0.20, min_margin=0.035,
            cross_group_margin=0.070, min_view_agreement=2,
            reject_scores=[0.18], reject_margin=0.025, reject_min_score=0.18,
        )
        self.assertIsNotNone(decision)
        self.assertEqual(decision["entry"]["display_name"], "Garrafa plástica")
        self.assertEqual(decision["family_fallback"], "bottle")


if __name__ == "__main__":
    unittest.main()
