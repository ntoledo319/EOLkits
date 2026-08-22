FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libharfbuzz0b \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 eolkits \
    && mkdir -p /data/eolkits \
    && chown -R eolkits:eolkits /data/eolkits

COPY apps/grace-api/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r /app/requirements.lock

COPY apps/runner/main.py /app/runner/main.py
COPY apps/runner/audit_pdf.py /app/runner/audit_pdf.py
COPY apps/grace-api/eolkits_grace /app/eolkits_grace
COPY rules/public/deprecations.yml /app/rules/public/deprecations.yml
COPY rules/public/dependency-compatibility.json /app/rules/public/dependency-compatibility.json
COPY pricing.yml /app/pricing.yml

ENV PYTHONPATH=/app:/app/runner
ENV EOLKITS_DATA_DIR=/data/eolkits
ENV EOLKITS_PRICING_FILE=/app/pricing.yml
ENV EOLKITS_DEPRECATIONS_FILE=/app/rules/public/deprecations.yml
ENV EOLKITS_DEPENDENCY_RULES_FILE=/app/rules/public/dependency-compatibility.json
ENV EOLKITS_ALLOWED_UPLOAD_ORIGIN=https://eolkits.com

USER eolkits
EXPOSE 8080
CMD ["uvicorn", "eolkits_grace.app:app", "--host", "0.0.0.0", "--port", "8080"]
