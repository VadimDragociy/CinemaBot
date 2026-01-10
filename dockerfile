FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
COPY .env .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]
