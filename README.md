# THE MONDAY LEDGER — one page, the whole of Monday 23 November 2026

Entry for the make.fun bounty **news-image-20261123**: a single 1024×1024 page
that carries one day's news — 38 wire-verified stories from 7 regions, every
one of them dated Monday 23 November 2026.

This third version was drawn on Tuesday, with Monday complete in every time
zone. The earlier pages froze mid-day — v1 at dawn, v2 at 12:45 UTC — and so
missed what the day still had in store. V3 carries it whole: FIFA's Zurich
Congress as a confirmed result (2031 to the United States, Mexico, Costa Rica
and Jamaica; 2035 to the United Kingdom, both by acclamation), Wall Street's
historic rebound after Nvidia reinstated Jensen Huang (S&P 500 +4.73%, its
best day since April 2025; Nasdaq +6.51%; Nvidia +31%), and the final Monday
figures for the stories the day was still writing — Dymer's toll closed at 11
with the search ended on Monday evening, two tankers logged hit in Hormuz,
Delta largely back on track. The three heroes are Monday events: Asia's
market rout at Monday's closes, Ukraine's count of the 153-drone night, and
the New York rebound. One canonical figure per index or commodity across the
whole page (gold: $3,635, Monday's New York close); every story traces to a
named wire or national agency; the stories left out as other days' news are
named in the DATE CHECK box.

[![make.fun bounty](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/Revaaa28/makefun-news-image-20261123-v3/rank.svg)](https://make.fun/bounty/news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/Revaaa28/makefun-news-image-20261123-v3/reward.svg)](https://make.fun/bounty/news-image-20261123)

## Run it

```
python3 main.py                        # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=out python3 main.py # or any directory you choose
```

`main.py` uses only the Python 3.13 standard library. It copies the committed
`entry.png` into the output directory and verifies the copy byte-for-byte, so
two runs always produce identical bytes. The output directory is read from the
environment as data; nothing from the environment is ever executed.

## How the page is built

`draw.py` (Pillow) draws the page at 2048×2048 and downscales with a Lanczos
filter to the final 1024×1024, so text and the dotted world map stay crisp.
Every number on the page was checked against the wires named beside it;
`news-notes.md` lists all 38 stories with their sources, the event-day
evidence for the three heroes, what changed against v2 item by item, and the
stories excluded as unverifiable or as belonging to another day.

## License

MIT — see `LICENSE`.
