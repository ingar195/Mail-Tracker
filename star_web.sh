python -m gunicorn -w 1 -b localhost:8000 tracker:app --log-level=debug --log-file=web.log
