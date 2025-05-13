# Self-Healing Test Automation Framework

A robust automated testing framework with self-healing capabilities for web applications. This framework intelligently adapts to UI changes, making your tests more resilient and reducing maintenance overhead.

## Features

- **Self-Healing Mechanism**: Automatically recovers from UI changes that would break traditional automation
- **Locator Prediction Model**: Uses multiple strategies to find elements even when their attributes change
- **Easy Integration**: Works with existing Selenium/Playwright test infrastructure
- **Comprehensive Reporting**: Detailed insights into healing attempts and success rates
- **Extensible Design**: Build your own custom healing strategies 

## How It Works

The self-healing mechanism works through a locator prediction model that:

1. Learns from successful element interactions
2. Builds a knowledge base of element patterns and characteristics
3. Uses multiple fallback strategies when primary locators fail
4. Automatically updates its model based on successes

When an element can't be found with the original locator, the framework:
- Tries alternative locator strategies (ID, CSS, XPath, text)
- Analyzes nearby elements for contextual clues
- Leverages historical data about the element
- Updates its model with new successful strategies

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/self-healing-project.git
cd self-healing-project

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
from resources.locator_predict_model import LocatorPredictor
from playwright.sync_api import sync_playwright

# Initialize the model
predictor = LocatorPredictor()

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    
    # Get page HTML for prediction
    html_content = page.content()
    
    # Get predictions for an element
    predictions = predictor.predict(
        locator_id="login_button",
        html_content=html_content,
        hints=["login", "sign in", "enter"]
    )
    
    # Try predictions until element is found
    for pred in predictions[:5]:
        try:
            if pred['type'] == 'css':
                element = page.locator(pred['selector']).first
            elif pred['type'] == 'xpath':
                element = page.locator(f"xpath={pred['selector']}").first
            elif pred['type'] == 'text':
                element = page.get_by_text(pred['selector']).first
                
            if element.is_visible():
                print(f"Element found with: {pred['selector']}")
                element.click()
                
                # Train model with successful selector
                predictor.train(
                    locator_id="login_button",
                    html_content=html_content,
                    successful_selector=pred['selector'],
                    selector_type=pred['type']
                )
                break
        except Exception as e:
            print(f"Selector failed: {pred['selector']}")
    
    browser.close()
```

### Running Tests

```bash
# Run enhanced model tests across multiple sites
python utils/test_model_enhanced.py

# Run feature tests with Behave
behave features/
```

## Project Structure

```
self-healing-project/
├── resources/               # Core framework components
│   ├── locator_predict_model.py    # Self-healing prediction model
│   └── ...
├── features/               # Behave feature files and step definitions
├── utils/                  # Utility scripts
│   ├── test_model.py       # Basic model testing
│   ├── test_model_enhanced.py  # Enhanced testing across sites
│   └── create_model_data.py    # Generate training data for model
├── archive/                # Archived or deprecated files
├── model_data.json         # Trained model data
├── requirements.txt        # Project dependencies
└── README.md
```

## Test Results

The framework has been tested on multiple websites with varying levels of success:

- **Simple sites** (e.g., TGO Yemek): ~100% success rate
- **Medium complexity sites** (e.g., Wikipedia): ~40-70% success rate  
- **Complex applications** (e.g., GitHub): ~40-60% success rate

Self-healing capabilities are particularly successful at recovering from:
- ID attribute changes
- Class name modifications
- Element text changes
- Minor structural changes

## Advanced Features

### Custom Healing Strategies

```python
# Add your own healing strategy to the prediction model
from resources.locator_predict_model import LocatorPredictor

class EnhancedPredictor(LocatorPredictor):
    def custom_strategy(self, locator_id, html_content):
        # Your custom prediction logic here
        return {
            'selector': 'your-custom-selector',
            'type': 'css',
            'score': 0.9
        }
        
    def predict(self, locator_id, html_content, hints):
        # Get standard predictions
        predictions = super().predict(locator_id, html_content, hints)
        
        # Add custom prediction
        custom_pred = self.custom_strategy(locator_id, html_content)
        predictions.append(custom_pred)
        
        # Sort by score
        predictions.sort(key=lambda x: x.get('score', 0), reverse=True)
        return predictions
```

### Analytics and Reporting

To generate analytics on healing success rates:

```bash
# Generate healing analytics report
python utils/analyze_healing.py

# View report in browser
open healing_analytics.html
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the concept of self-healing tests presented in various research papers
- Built with Python, Playwright and BeautifulSoup
- Special thanks to the open source community 
