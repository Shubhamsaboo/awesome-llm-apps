# Heart Disease Risk Predictor

<div align="center">

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.10+-red.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.5+-yellow.svg)](https://xgboost.readthedocs.io/)

</div>

## Overview

An advanced machine learning application that predicts heart disease risk using XGBoost. Built with Streamlit and trained on over 300,000 US health records, achieving 91.5% prediction accuracy.

## Features

- **Real-time Prediction**: Instant heart disease risk assessment
- **Advanced Analytics**: Comprehensive health evaluation using 17 key parameters
- **Smart Visualization**: Color-coded risk zones with detailed explanations
- **Health Insights**: Personalized recommendations based on risk levels
- **Robust Architecture**: Error handling and input validation
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Extensible Platform**: Ready for additional disease predictions

## Requirements

### Software Dependencies
```
Python >= 3.8
streamlit >= 1.10.0
xgboost >= 1.5.0
pandas >= 1.3.0
numpy >= 1.21.0
```

### System Requirements
- RAM: 4GB minimum
- Storage: 500MB free space
- Processor: 2+ cores recommended

## Quick Start

1. **Clone the Repository**
```bash
git clone https://github.com/jvcByte/heart-disease-predictor.git
cd heart-disease-predictor
```

2. **Environment Setup**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Launch Application**
```bash
streamlit run app.py
```

4. Open browser at `http://localhost:8501`

## Usage Guide

### Input Parameters

#### Demographics
- Race
- Sex
- Age category

#### Health Metrics
- BMI category
- Sleep patterns
- Physical activity
- Health status
- Mobility assessment

#### Lifestyle
- Smoking history
- Alcohol consumption
- Exercise habits

#### Medical History
- Diabetes status
- Stroke history
- Chronic conditions

### Risk Zones

| Zone    | Range   | Action Required                    |
|---------|---------|-----------------------------------|
| Green   | 0-25%   | Maintain current health practices |
| Yellow  | 25-50%  | Consider lifestyle improvements   |
| Orange  | 50-75%  | Consult healthcare provider       |
| Red     | 75-100% | Seek medical attention           |

## Project Structure

```
heart-disease-predictor/
│
├── app.py                 # Main application file
├── requirements.txt       # Project dependencies
├── models/               
│   └── xgboost_model.pkl # Trained model
├── assets/
│   └── images/           # UI resources
├── tests/                # Unit tests
└── docs/                 # Documentation
```

## Model Information

- **Architecture**: XGBoost (Gradient Boosting)
- **Training Data**: 300,000+ US health records (2020)
- **Accuracy**: 91.5%
- **Features**: 17 health parameters
- **Validation**: K-fold cross-validation
- **Updates**: Quarterly retraining

## Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run linter
flake8 .
```

### Contributing Guidelines

1. Fork the repository
2. Create feature branch (`git checkout -b feature/Enhancement`)
3. Commit changes (`git commit -m 'Add Enhancement'`)
4. Push to branch (`git push origin feature/Enhancement`)
5. Open Pull Request

## Author

**jvcByte**
- Email: jvc8463@gmail.com
- GitHub: [@jvcByte](https://github.com/jvcByte)

## License

```
Copyright 2024 jvcByte

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Acknowledgments

- CDC BRFSS 2020 survey data
- Streamlit framework
- XGBoost library
- Healthcare professionals who validated the model

## Disclaimer

This tool is for educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the guidance of qualified healthcare professionals for medical concerns.

---

<div align="center">
Made with ❤️ by jvcByte
</div>
