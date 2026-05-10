FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# system deps for some Python packages (audio, numpy/scipy builds)
RUN apt-get update && \
	apt-get install -y --no-install-recommends build-essential libsndfile1 && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy and install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy app source
COPY backend/app ./app

EXPOSE 8000

# Default command to run the FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]