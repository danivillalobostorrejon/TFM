FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente de la app
COPY app/ app/

# Asegúrate de que el contenedor pueda leer variables desde el entorno
ENV PYTHONUNBUFFERED=1

# Copia el archivo de entrada (por claridad y robustez)
COPY startup.sh .

# Dale permisos de ejecución
RUN chmod +x startup.sh

# Expone el puerto
EXPOSE 8000

# Usa el script como comando principal
CMD ["./startup.sh"]
