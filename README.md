# Proyecto Integrador IoT — Tótem fisiológico EAFIT

Dashboard académico desarrollado con **Python, Pandas, Plotly y Streamlit** para
explorar un conjunto de datos sintéticos de un escenario IoT con lector NFC,
sensor MAX30102 y ESP32.

> **Importante:** todos los datos son simulados. No corresponden a mediciones
> médicas reales y la aplicación no realiza diagnósticos clínicos.

## Integrantes

- Miguel Angel Gaviria Arboleda
- Jacobo Castro Saenz
- Maria Isabel Osorio Franco

## Perfil del conjunto de datos

El CSV suministrado contiene:

- **2,667 registros**
- **295 estudiantes ficticios**
- **2,590 mediciones válidas**
- **77 mediciones inválidas (2.89 %)**
- **0 valores nulos**
- Período local: **29/09/2026 19:50 a 28/10/2026 19:35**
- BPM promedio de registros válidos: **75.47 bpm**
- SpO₂ promedio de registros válidos: **97.72 %**

Hallazgos iniciales del conjunto completo:

- Día con mayor número de mediciones: **2026-09-30**, con **132 registros**.
- Estudiante con mayor número de mediciones: **EST-0241**, con **21 registros**.

Estos resultados son descriptivos y se calculan sobre datos sintéticos.

## Funcionalidades del dashboard

### Indicadores
- Total de mediciones
- Número de estudiantes
- BPM promedio de mediciones válidas
- SpO₂ promedio de mediciones válidas
- Porcentaje de mediciones inválidas

### Filtros
- Rango de fechas
- Estudiante
- Estado de medición (`valid`, `invalid` o todos)

### Visualizaciones
1. Cantidad de mediciones por día
2. Horarios de mayor utilización
3. Distribución de frecuencia cardíaca
4. Distribución de SpO₂
5. Distribución de mediciones válidas e inválidas
6. Relación BPM–SpO₂ según calidad de señal
7. Estudiantes con mayor número de mediciones

### Otras funciones
- Hallazgos automáticos según filtros
- Seguimiento histórico individual
- Revisión de calidad de datos
- Detección exploratoria de posibles atípicos mediante IQR
- Tabla de registros filtrados

## Estructura

```text
proyecto-integrador-iot/
├── app.py
├── requirements.txt
├── proyecto_integrador_eafit_max30102.csv
├── README.md
└── .gitignore
```

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en Streamlit Community Cloud

1. Subir todos los archivos a un repositorio de GitHub.
2. Entrar a Streamlit Community Cloud.
3. Crear una nueva aplicación desde el repositorio.
4. Seleccionar la rama `main`.
5. Elegir `app.py` como archivo principal.
6. Desplegar y verificar todos los filtros y visualizaciones.

## Tecnologías

- Python
- Pandas
- Plotly
- Streamlit
- GitHub
- Streamlit Community Cloud
