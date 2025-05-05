# 🧾 Worker Cost Calculator

Una aplicación web interactiva para cargar documentos laborales en PDF, extraer automáticamente información clave utilizando modelos de lenguaje (LLM) y calcular el coste por hora de los trabajadores.

## 🚀 Funcionalidades

- 📥 Subida y procesamiento de documentos PDF:
  - Modelo 190
  - Documento 10T
  - Convenio colectivo
  - IDC
  - RNT (mensual)
- 🤖 Clasificación automática del tipo de documento usando LLMs (OpenAI GPT-4/3.5).
- 📊 Extracción estructurada:
  - Salario bruto (Percepción íntegra)
  - Base de contingencias comunes y días cotizados
  - Horas del convenio laboral
  - Costes sociales fijos y adicionales (IDC)
- 🧠 Chatbot integrado con contexto en tiempo real para resolver dudas sobre trabajadores y costes.
- 📈 Cálculo de coste/hora por fórmula:

```
Coste / hora = (Salario bruto + (Base RNT anual * porcentaje SS)) / Horas convenio
```

---

## 🧱 Estructura de carpetas

```
app/
├── app_pages/
│   ├── upload_page.py         # Página de carga de documentos
│   ├── view_workers_page.py   # Visualización de datos
│   └── chat_page.py           # Chat asistente
├── chatbot.py                 # Generador de respuestas del asistente
├── database.py                # Interacción con PostgreSQL
├── llm_classifier.py          # Clasificación y extracción con LLM
├── pdf_preprocessor.py        # Extracción de texto de PDF
├── main.py                    # Entrada principal de Streamlit
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🐳 Cómo ejecutar con Docker

### 1. Crear archivo `.env` (opcional)

```env
OPENAI_API_KEY=tu_clave_aqui
DB_HOST=db
DB_NAME=mi_base
DB_USER=usuario
DB_PASSWORD=contrasena
```

### 2. Ejecutar la aplicación

```bash
docker-compose up --build
```

Visita: [http://localhost:8000](http://localhost:8000)

---

## 🧠 LLMs usados

- GPT-3.5 y GPT-4 vía OpenAI API
- Prompts diseñados para:
  - Clasificar documentos automáticamente
  - Extraer campos como percepciones, bases y cotizaciones
  - Interpretar periodos de liquidación (ej. `12/2021 -> 01-12-2021`)

---

## 🗄️ Esquema de Base de Datos

- `workers`: datos básicos del trabajador y salario
- `doc_10t`: trabajadores del documento 10T
- `contingencias_comunes`: base mensual + días cotizados
- `convenio`: horas anuales del convenio colectivo
- `cargas_sociales`: porcentajes fijos (23.6%, 5.5%, 0.8%, IT)
  
---

## ✅ Pendiente / Mejoras futuras

- Subida masiva por carpetas
- Panel de administración
- Cálculo automatizado del coste completo
- Exportación a Excel o PDF

---

## 🧑‍💼 Autor

@danivillalobostorrejon
---

## 🧩 Requisitos

- Python 3.9+
- Docker + docker-compose
- Clave de OpenAI API