"""Score pre-registered decision entries against subsequent bars.

Reads forward/decisions/*.md, each carrying a flat ``key: value`` front
matter (schema in forward/decisions/README.md), marks every entry against
the spliced price series, and always reports scored / pending / malformed
counts as numbers, so a run that scored nothing cannot read as a clean one.

    python -m quant.scoring

An entry is scored once the series holds the full horizon after its
effective bar; until then it is pending, counted and named. A file that
cannot be parsed, or whose stated effective bar the trading calendar
contradicts, is malformed: reported per file with the reason and reflected
in a nonzero exit code, never skipped quietly.

The log is single-instrument by construction (SPY, like everything in the
research lane); entries carry their instrument for the record, and the
scorer marks against the spliced SPY series.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from quant.forward import load_spliced

DECISIONS_DIR = Path('forward') / 'decisions'
REQUIRED_FIELDS = (
    'entry_id',
    'written_utc',
    'rule',
    'signal_bar',
    'stance',
    'effective_bar',
    'horizon_bars',
    'falsified_if',
)
STANCES = ('LONG', 'FLAT')
FRONT_MATTER = re.compile(r'\A---\r?\n(.*?)\r?\n---(\r?\n|\Z)', re.DOTALL)


@dataclass(frozen=True)
class Entry:
    name: str
    written_utc: str
    rule: str
    signal_bar: pd.Timestamp
    stance: str
    effective_bar: pd.Timestamp
    horizon_bars: int
    falsified_if: str


@dataclass(frozen=True)
class Score:
    entry: Entry
    status: str  # 'scored' | 'pending'
    r: float | None = None  # buy-and-hold return over the entry's window
    stance_r: float | None = None  # what the stance earned: r when LONG, 0.0 when FLAT
    hit: bool | None = None  # True when the pre-registered falsifier did NOT fire


def parse_entry(text: str, name: str = '<entry>') -> Entry:
    match = FRONT_MATTER.match(text)
    if match is None:
        raise ValueError(f'{name}: front matter must open and close with --- fences')
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ':' not in line:
            raise ValueError(f'{name}: malformed front-matter line {line!r}')
        key, value = line.split(':', 1)
        fields[key.strip()] = value.strip()
    missing = [key for key in REQUIRED_FIELDS if key not in fields]
    if missing:
        raise ValueError(f'{name}: missing front-matter field(s) {missing}')
    if fields['stance'] not in STANCES:
        raise ValueError(f'{name}: stance must be one of {STANCES}, got {fields["stance"]!r}')
    try:
        signal_bar = pd.Timestamp(fields['signal_bar'])
        effective_bar = pd.Timestamp(fields['effective_bar'])
        horizon_bars = int(fields['horizon_bars'])
    except ValueError as exc:
        raise ValueError(f'{name}: unparseable date or horizon ({exc})') from exc
    if horizon_bars < 1:
        raise ValueError(f'{name}: horizon_bars must be >= 1, got {horizon_bars}')
    if effective_bar <= signal_bar:
        raise ValueError(f'{name}: effective_bar must fall after signal_bar')
    return Entry(
        name=fields['entry_id'],
        written_utc=fields['written_utc'],
        rule=fields['rule'],
        signal_bar=signal_bar,
        stance=fields['stance'],
        effective_bar=effective_bar,
        horizon_bars=horizon_bars,
        falsified_if=fields['falsified_if'],
    )


def score_entry(entry: Entry, prices: pd.DataFrame) -> Score:
    """Mark one entry to market; pending while the horizon has not elapsed.

    R = close(effective_bar + horizon - 1) / open(effective_bar) - 1: what a
    full-weight long over the entry's window returned, cost-free. LONG is
    falsified by R < 0 and FLAT by R > 0 -- the falsified_if each entry
    pre-registers. Costs live in the engine-based forward test, not here.
    """
    idx = prices.index
    if entry.effective_bar not in idx:
        if len(idx) == 0 or idx.max() < entry.effective_bar:
            return Score(entry=entry, status='pending')
        raise ValueError(
            f'{entry.name}: effective bar {entry.effective_bar.date()} is not a bar in a price series '
            f'that already extends past it'
        )
    pos = int(idx.get_loc(entry.effective_bar))
    end = pos + entry.horizon_bars - 1
    if end >= len(idx):
        return Score(entry=entry, status='pending')
    r = float(prices['close'].iloc[end] / prices['open'].iloc[pos] - 1.0)
    stance_r = r if entry.stance == 'LONG' else 0.0
    hit = (r >= 0.0) if entry.stance == 'LONG' else (r <= 0.0)
    return Score(entry=entry, status='scored', r=r, stance_r=stance_r, hit=hit)


def summarize(scores: list[Score]) -> dict:
    scored = [s for s in scores if s.status == 'scored']
    summary: dict = {'n_scored': len(scored), 'n_pending': len(scores) - len(scored)}
    if scored:
        summary['hit_rate'] = sum(1 for s in scored if s.hit) / len(scored)
        summary['avg_stance_r'] = sum(s.stance_r for s in scored) / len(scored)
        summary['avg_baseline_r'] = sum(s.r for s in scored) / len(scored)
    else:
        summary['hit_rate'] = None
        summary['avg_stance_r'] = None
        summary['avg_baseline_r'] = None
    return summary


def main() -> int:
    entry_paths = [p for p in sorted(DECISIONS_DIR.glob('*.md')) if p.name != 'README.md']
    prices = load_spliced()
    scores: list[Score] = []
    malformed: list[tuple[Path, str]] = []
    for path in entry_paths:
        try:
            entry = parse_entry(path.read_text(encoding='utf-8'), name=path.name)
            scores.append(score_entry(entry, prices))
        except ValueError as exc:
            malformed.append((path, str(exc)))

    for score in scores:
        entry = score.entry
        if score.status == 'scored':
            verdict = 'HIT' if score.hit else 'MISS'
            print(
                f'{entry.name}: {entry.stance} (signal {entry.signal_bar.date()}) scored over {entry.horizon_bars} bars: '
                f'buy&hold R={score.r * 100:+.2f}%  stance={score.stance_r * 100:+.2f}%  {verdict}'
            )
        else:
            print(
                f'{entry.name}: {entry.stance} (signal {entry.signal_bar.date()}) pending: '
                f'{entry.horizon_bars}-bar horizon from {entry.effective_bar.date()} not elapsed '
                f'(data ends {prices.index.max().date()})'
            )
    for path, error in malformed:
        print(f'{path.name}: MALFORMED -- {error}')

    totals = summarize(scores)
    print()
    print(
        f'entries={len(entry_paths)} scored={totals["n_scored"]} '
        f'pending={totals["n_pending"]} malformed={len(malformed)}'
    )
    if totals['n_scored']:
        print(
            f'hit_rate={totals["hit_rate"]:.2f} avg_stance_return={totals["avg_stance_r"] * 100:+.2f}% '
            f'avg_buy_and_hold_return={totals["avg_baseline_r"] * 100:+.2f}%'
        )
    return 1 if malformed else 0


if __name__ == '__main__':
    raise SystemExit(main())
