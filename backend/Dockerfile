
FROM python:3.10-slim

WORKDIR /app

# Copy requirements or install directly for speed
RUN pip install fastapi uvicorn

# We copy the entire backend into /app/backend to match python module structure
COPY ./backend /app/backend
COPY ./backend/plc_compile_check.py /app/plc_compile_check.py

# Set python path
ENV PYTHONPATH=/app

CMD ["python", "plc_compile_check.py"]
