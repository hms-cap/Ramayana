Browser checks (Playwright, not run in CI). Serve the built site, then run each script:

    python site/build.py && python -m http.server 8765 --directory dist &
    python tests/e2e/chant.py   # chant view, history (close / Back), PDF download, print document
    python tests/e2e/home.py    # verse of the day, share picture, My list, kāṇḍa cards, script letter
    python tests/e2e/pwa.py     # service worker, offline reload, update check, offline pack

Screenshots and the exported PDF/PNG are written to /tmp.
    python tests/e2e/swipe.py   # sideways swipe between sargas (reading and chant views)
