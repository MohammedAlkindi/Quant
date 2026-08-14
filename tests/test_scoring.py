import numpy as np
import pandas as pd
import pytest

import quant.scoring as scoring
from quant.scoring import REQUIRED_HORIZON_BARS, Entry, parse_entry, score_entry, summarize


def make_prices(opens, closes, start='2030-01-07'):  # a Monday
    idx = pd.bdate_range(start, periods=len(opens))
    return pd.DataFrame({'open': opens, 'close': closes}, index=idx, dtype=float)


def scored_prices(final_close, periods=25):
    # Effective bar sits at position 1 (2030-01-08); the 21-bar horizon ends at
    # position 21, whose close is set to final_close. Opens stay at 100, so
    # R = final_close / 100 - 1, hand-computable.
    opens = [100.0] * periods
    closes = [100.0] * periods
    closes[21] = final_close
    return make_prices(opens, closes)


def entry_text(**overrides):
    fields = {
        'entry_id': 'test-entry',
        'written_utc': '2030-01-07T11:00:00Z',
        'rule': 'ma_crossover fast=10 slow=200 on SPY daily closes',
        'signal_bar': '2030-01-07',
        'stance': 'LONG',
        'effective_bar': '2030-01-08',
        'horizon_bars': str(REQUIRED_HORIZON_BARS),
        'falsified_if': 'close(effective_bar + 20 trading bars) < open(effective_bar)',
    }
    fields.update(overrides)
    lines = '\n'.join(f'{key}: {value}' for key, value in fields.items() if value is not None)
    return f'---\n{lines}\n---\n\nProse body a reader can recompute from.\n'


def make_entry(**overrides) -> Entry:
    return parse_entry(entry_text(**overrides), name='test.md')


def test_parse_entry_round_trips_every_scoring_field():
    entry = make_entry()
    assert entry.name == 'test-entry'
    assert entry.written_utc == '2030-01-07T11:00:00Z'
    assert entry.stance == 'LONG'
    assert entry.signal_bar == pd.Timestamp('2030-01-07')
    assert entry.effective_bar == pd.Timestamp('2030-01-08')
    assert entry.horizon_bars == REQUIRED_HORIZON_BARS
    assert 'open(effective_bar)' in entry.falsified_if


def test_parse_entry_rejects_malformed_input_loudly():
    with pytest.raises(ValueError, match='fences'):
        parse_entry('no front matter here', name='x.md')
    with pytest.raises(ValueError, match='missing front-matter field.*stance'):
        parse_entry(entry_text(stance=None), name='x.md')
    with pytest.raises(ValueError, match='stance must be one of'):
        parse_entry(entry_text(stance='SHORT'), name='x.md')
    with pytest.raises(ValueError, match='unparseable'):
        parse_entry(entry_text(horizon_bars='soon'), name='x.md')
    with pytest.raises(ValueError, match='effective_bar must fall after'):
        parse_entry(entry_text(effective_bar='2030-01-07'), name='x.md')
    with pytest.raises(ValueError, match='malformed front-matter line'):
        parse_entry('---\nentry_id test-entry\n---\n', name='x.md')


def test_parse_entry_enforces_the_pre_registered_horizon():
    # 21 bars is the pre-registered horizon (decisions/README.md); the scorer
    # rejects any other value mechanically so a later entry cannot quietly
    # score itself on a friendlier window.
    with pytest.raises(ValueError, match='horizon_bars must be 21'):
        parse_entry(entry_text(horizon_bars='3'), name='x.md')
    with pytest.raises(ValueError, match='horizon_bars must be 21'):
        parse_entry(entry_text(horizon_bars='0'), name='x.md')


def test_parse_entry_requires_an_explicit_utc_written_timestamp():
    with pytest.raises(ValueError, match='explicit-UTC'):
        parse_entry(entry_text(written_utc='2030-01-07T11:00:00'), name='x.md')  # naive
    with pytest.raises(ValueError, match='explicit-UTC'):
        parse_entry(entry_text(written_utc='2030-01-07T11:00:00+04:00'), name='x.md')
    with pytest.raises(ValueError, match='unparseable'):
        parse_entry(entry_text(written_utc='yesterday-ish'), name='x.md')
    assert make_entry(written_utc='2030-01-07T11:00:00+00:00').written_utc == '2030-01-07T11:00:00+00:00'


def test_long_entry_scores_against_hand_computed_return():
    score = score_entry(make_entry(), scored_prices(108.0))
    # Horizon 21 from 2030-01-08: open 100 -> close of the 21st bar, 108.
    assert score.status == 'scored'
    assert score.r == pytest.approx(0.08)
    assert score.stance_r == pytest.approx(0.08)
    assert score.hit is True


def test_long_entry_is_falsified_by_a_negative_window():
    score = score_entry(make_entry(), scored_prices(92.0))
    assert score.r == pytest.approx(-0.08)
    assert score.hit is False


def test_flat_entry_mirrors_the_falsifier_and_earns_nothing():
    hit = score_entry(make_entry(stance='FLAT'), scored_prices(92.0))
    miss = score_entry(make_entry(stance='FLAT'), scored_prices(108.0))
    assert hit.hit is True and hit.stance_r == 0.0 and hit.r == pytest.approx(-0.08)
    assert miss.hit is False and miss.stance_r == 0.0 and miss.r == pytest.approx(0.08)


def test_a_dead_flat_window_falsifies_neither_stance():
    prices = scored_prices(100.0)
    assert score_entry(make_entry(), prices).hit is True
    assert score_entry(make_entry(stance='FLAT'), prices).hit is True


def test_entry_is_pending_before_its_effective_bar_trades():
    prices = make_prices(opens=[100], closes=[100])  # data ends 2030-01-07
    score = score_entry(make_entry(), prices)
    assert score.status == 'pending'
    assert score.r is None and score.hit is None


def test_entry_is_pending_until_the_full_horizon_has_elapsed():
    # 21 bars of data: positions 0..20, but the horizon from position 1 needs
    # position 21 -- one bar short.
    prices = make_prices(opens=[100.0] * 21, closes=[100.0] * 21)
    assert score_entry(make_entry(), prices).status == 'pending'


def test_effective_bar_the_calendar_contradicts_is_an_error_not_a_skip():
    prices = scored_prices(100.0)  # bars 2030-01-07 -> 2030-02-10
    with pytest.raises(ValueError, match='not a bar'):
        score_entry(make_entry(effective_bar='2030-01-12'), prices)  # a Saturday the series extends past


def test_summarize_counts_scored_and_pending_and_averages_outcomes():
    prices = scored_prices(108.0)
    short = make_prices(opens=[100], closes=[100])
    scores = [
        score_entry(make_entry(), prices),  # scored hit, r=+8%
        score_entry(make_entry(stance='FLAT'), prices),  # scored miss, stance 0
        score_entry(make_entry(), short),  # pending
    ]
    totals = summarize(scores)
    assert totals['n_scored'] == 2
    assert totals['n_pending'] == 1
    assert totals['hit_rate'] == pytest.approx(0.5)
    assert totals['avg_stance_r'] == pytest.approx(0.04)
    assert totals['avg_baseline_r'] == pytest.approx(0.08)


def test_summarize_with_nothing_scored_reports_counts_and_no_rates():
    totals = summarize([])
    assert totals == {'n_scored': 0, 'n_pending': 0, 'hit_rate': None, 'avg_stance_r': None, 'avg_baseline_r': None}


def prices_for_main(periods=40):
    idx = pd.bdate_range('2030-01-07', periods=periods)
    close = np.linspace(100.0, 110.0, periods)
    return pd.DataFrame(
        {'open': close - 0.05, 'high': close + 0.5, 'low': close - 0.5, 'close': close, 'volume': 1e6},
        index=idx,
    )


def test_main_always_prints_the_counts_line(tmp_path, monkeypatch, capsys):
    (tmp_path / 'scored.md').write_text(entry_text(entry_id='scored-entry'), encoding='utf-8')
    (tmp_path / 'pending.md').write_text(
        entry_text(entry_id='pending-entry', signal_bar='2030-04-01', effective_bar='2030-04-02'), encoding='utf-8'
    )
    (tmp_path / 'README.md').write_text('schema doc, not an entry', encoding='utf-8')
    monkeypatch.setattr(scoring, 'DECISIONS_DIR', tmp_path)
    monkeypatch.setattr(scoring, 'load_spliced', lambda: prices_for_main())
    assert scoring.main() == 0
    out = capsys.readouterr().out
    assert 'entries=2 scored=1 pending=1 malformed=0' in out
    assert 'hit_rate=' in out


def test_main_reports_malformed_files_and_exits_nonzero(tmp_path, monkeypatch, capsys):
    (tmp_path / 'bad.md').write_text('not an entry at all', encoding='utf-8')
    monkeypatch.setattr(scoring, 'DECISIONS_DIR', tmp_path)
    monkeypatch.setattr(scoring, 'load_spliced', lambda: prices_for_main())
    assert scoring.main() == 1
    out = capsys.readouterr().out
    assert 'MALFORMED' in out
    assert 'entries=1 scored=0 pending=0 malformed=1' in out
