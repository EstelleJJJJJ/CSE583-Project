# Examples

`find_parks_example.py` runs the package end to end on the bundled snapshot, so it works
offline and without an API key. Install the package first (`pip install -e .` from the
repository root), then run:

```
python examples/find_parks_example.py
```

It prints, in order: Washington parks with hiking and camping under a $35 entrance fee,
parks anywhere with stargazing and a campground, California parks with accessible
restrooms, a side-by-side table for Olympic, Mount Rainier and North Cascades, a summary
of Olympic National Park, and Mount Rainier's month-by-month visitation profile. Each
search row carries a `match_reasons` sentence that says which requested criteria the park
meets and which it does not.
