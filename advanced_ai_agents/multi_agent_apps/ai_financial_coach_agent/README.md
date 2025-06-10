# Agente Asesor Financiero de IA con Google ADK 💰

El **Asesor Financiero de IA** es un asesor financiero personalizado impulsado por el framework ADK (Agent Development Kit) de Google. Esta aplicación proporciona un análisis financiero completo y recomendaciones basadas en las entradas del usuario, incluyendo ingresos, gastos, deudas y objetivos financieros.

## Características

- **Sistema de Análisis Financiero Multiagente**
    - Agente de Análisis de Presupuesto: Analiza patrones de gasto y recomienda optimizaciones
    - Agente de Estrategia de Ahorro: Crea planes de ahorro personalizados y estrategias de fondos de emergencia
    - Agente de Reducción de Deuda: Desarrolla estrategias optimizadas de pago de deudas utilizando los métodos de avalancha y bola de nieve

- **Análisis de Gastos**:
  - Admite tanto la carga de CSV como la entrada manual de gastos
  - Análisis de transacciones CSV con seguimiento de fecha, categoría y monto
  - Desglose visual del gasto por categoría
  - Categorización automatizada de gastos y detección de patrones

- **Recomendaciones de Ahorro**:
  - Estrategias de dimensionamiento y creación de fondos de emergencia
  - Asignaciones de ahorro personalizadas para diferentes objetivos
  - Técnicas prácticas de automatización para un ahorro constante
  - Seguimiento del progreso y recomendaciones de hitos

- **Gestión de Deudas**:
  - Manejo de múltiples deudas con optimización de tasas de interés
  - Comparación entre los métodos de avalancha y bola de nieve
  - Cronograma visual de pago de deudas y análisis de ahorro de intereses
  - Recomendaciones procesables para la reducción de deudas

- **Visualizaciones Interactivas**:
  - Gráficos circulares para el desglose de gastos
  - Gráficos de barras para ingresos vs. gastos
  - Gráficos de comparación de deudas
  - Métricas de seguimiento del progreso


## Cómo Ejecutar

Sigue los pasos a continuación para configurar y ejecutar la aplicación:

1. **Obtener Clave API**:
   - Obtén una Clave API de Gemini gratuita desde Google AI Studio: https://aistudio.google.com/apikey
   - Crea un archivo `.env` en la raíz del proyecto y agrega tu clave API:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

2. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/ai_agent_tutorials/ai_financial_coach_agent
   ```

3. **Instala las Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecuta la Aplicación Streamlit**:
   ```bash
   streamlit run ai_financial_coach_agent.py
   ```

## Formato de Archivo CSV

La aplicación acepta archivos CSV con las siguientes columnas requeridas:
- `Date`: Fecha de la transacción en formato YYYY-MM-DD
- `Category`: Categoría del gasto
- `Amount`: Monto de la transacción (admite símbolos de moneda y formato de comas)

Ejemplo:
```csv
Date,Category,Amount
2024-01-01,Housing,1200.00
2024-01-02,Food,150.50
2024-01-03,Transportation,45.00
```

Se puede descargar un archivo CSV de plantilla directamente desde la barra lateral de la aplicación.
