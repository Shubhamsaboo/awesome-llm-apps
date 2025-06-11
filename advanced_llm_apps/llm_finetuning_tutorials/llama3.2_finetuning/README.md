## 🦙 Ajuste Fino de Llama 3.2 en 30 Líneas de Python

Este script demuestra cómo realizar el ajuste fino (finetune) del modelo Llama 3.2 utilizando la biblioteca [Unsloth](https://unsloth.ai/), que hace el proceso fácil y rápido. Puedes ejecutar este ejemplo para realizar el ajuste fino de los modelos Llama 3.1 1B y 3B de forma gratuita en Google Colab.

### Características

- Realiza el ajuste fino del modelo Llama 3.2 utilizando la biblioteca Unsloth
- Implementa Adaptación de Bajo Rango (LoRA) para un ajuste fino eficiente
- Utiliza el conjunto de datos FineTome-100k para el entrenamiento
- Configurable para diferentes tamaños de modelo (1B y 3B)

### Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/llm_finetuning_tutorials/llama3.2_finetuning
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

## Uso

1. Abre el script en Google Colab o en tu entorno Python preferido.

2. Ejecuta el script para iniciar el proceso de ajuste fino:

```bash
# Ejecuta el script completo
python finetune_llama3.2.py
```

3. El modelo ajustado se guardará en el directorio "finetuned_model".

## Cómo Funciona

1. **Carga del Modelo**: El script carga el modelo Llama 3.2 3B Instruct utilizando FastLanguageModel de Unsloth.

2. **Configuración de LoRA**: Se aplica Adaptación de Bajo Rango a capas específicas del modelo para un ajuste fino eficiente.

3. **Preparación de Datos**: Se carga el conjunto de datos FineTome-100k y se preprocesa utilizando una plantilla de chat.

4. **Configuración del Entrenamiento**: El script configura el SFTTrainer con argumentos de entrenamiento específicos.

5. **Ajuste Fino**: El modelo se ajusta con el conjunto de datos preparado.

6. **Guardado del Modelo**: El modelo ajustado se guarda en el disco.

## Configuración

Puedes modificar los siguientes parámetros en el script:

- `model_name`: Cambia a "unsloth/Llama-3.1-1B-Instruct" para el modelo 1B
- `max_seq_length`: Ajusta la longitud máxima de la secuencia
- `r`: Rango de LoRA
- Hiperparámetros de entrenamiento en `TrainingArguments`

## Personalización

- Para utilizar un conjunto de datos diferente, reemplaza la llamada a la función `load_dataset` con tu conjunto de datos deseado.
- Ajusta los `target_modules` en la configuración de LoRA para ajustar diferentes capas del modelo.
- Modifica la plantilla de chat en `get_chat_template` si estás utilizando un formato conversacional diferente.

## Ejecución en Google Colab

1. Abre un nuevo cuaderno de Google Colab.
2. Copia el script completo en una celda de código.
3. Agrega una celda al principio para instalar las bibliotecas requeridas:

```
!pip install torch transformers datasets trl unsloth
```

4. Ejecuta las celdas para iniciar el proceso de ajuste fino.

## Notas

- Este script está optimizado para ejecutarse en el nivel gratuito de Google Colab, que proporciona acceso a GPU.
- El proceso de ajuste fino puede llevar algún tiempo, dependiendo del tamaño del modelo y los recursos computacionales disponibles.
- Asegúrate de tener suficiente espacio de almacenamiento en tu instancia de Colab para guardar el modelo ajustado.