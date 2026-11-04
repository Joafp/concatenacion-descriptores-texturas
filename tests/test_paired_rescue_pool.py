from run_budgeted_rescue_paired import candidate_pool
from run_rescue_nested_selection import COMMON_21


def test_matched_static_draws_and_color_closure():
    ranked = list(COMMON_21)
    plain = set(candidate_pool(ranked, 42, 5, 4, False))
    for position in (0, 7, 21):
        colored_rank = ranked.copy()
        colored_rank.insert(position, 'rgb_ngram_svd')
        colored = set(candidate_pool(colored_rank, 42, 5, 4, True))
        assert plain == {s for s in colored if 'rgb_ngram_svd' not in s}
        assert colored == plain | {tuple(sorted((*s, 'rgb_ngram_svd'))) for s in plain}
        assert len(colored) == 2 * len(plain)
    assert tuple(sorted(ranked[:2])) in plain
    assert candidate_pool(ranked, 42, 5, 4, False) == sorted(plain)


def test_ngram_rank_does_not_change_static_core_draws():
    ranked = list(reversed(COMMON_21))
    expected = candidate_pool(ranked, 17, 20, 4, False)
    actual = candidate_pool(['rgb_ngram_svd', *ranked], 17, 20, 4, False)
    assert actual == expected
    assert all('rgb_ngram_svd' not in s for s in actual)
