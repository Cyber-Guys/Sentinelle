import httpx

# un solo client per processo: riusa le connessioni (keep-alive/TLS) tra le chiamate
client = httpx.Client(timeout=5, follow_redirects=True)
