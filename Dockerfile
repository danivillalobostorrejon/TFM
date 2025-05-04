FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

# Create a script to run the Streamlit app
RUN echo "#!/bin/bash\nstreamlit run app/main.py --server.port=8000 --server.address=0.0.0.0" > startup.sh
RUN chmod +x startup.sh

EXPOSE 8000

CMD ["./startup.sh"]
