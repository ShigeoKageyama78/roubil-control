# Image de production : petite, sans outils de développement, exécutée par un utilisateur non-root.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Utilisateur sans privilèges : si l'application était compromise, l'attaquant n'aurait pas les droits root.
RUN useradd --system --no-create-home appuser && mkdir /srv/data && chown appuser /srv/data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/sante')"
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
