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
    && useradd --create-home --uid 10001 runner

COPY apps/runner/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r /app/requirements.lock

COPY apps/runner/main.py /app/main.py
COPY apps/runner/audit_pdf.py /app/audit_pdf.py
COPY rules/public/deprecations.yml /app/rules/public/deprecations.yml
COPY rules/public/dependency-compatibility.json /app/rules/public/dependency-compatibility.json

ENV PYTHONUNBUFFERED=1
ENV RUNNER_HTTP=1
ENV EOLKITS_DEPRECATIONS_FILE=/app/rules/public/deprecations.yml
ENV EOLKITS_DEPENDENCY_RULES_FILE=/app/rules/public/dependency-compatibility.json
ENV EOLKITS_ALLOWED_UPLOAD_ORIGIN=https://eolkits.com

USER runner
EXPOSE 8080
ENTRYPOINT ["python", "/app/main.py"]
