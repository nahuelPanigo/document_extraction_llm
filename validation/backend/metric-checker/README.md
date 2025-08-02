# Metric Checker Backend

A FastAPI-based backend service for comparing JSON metadata files and calculating various metrics between predicted and ground truth data.

## Features

- **JSON File Comparison**: Compare predicted outputs with ground truth data
- **Multiple Metrics**: Supports exact equality and list percentage matching metrics
- **RESTful API**: FastAPI-based REST API with automatic documentation
- **CORS Support**: Configured for frontend integration
- **Error Handling**: Comprehensive error handling and validation
- **Flexible Input**: Accepts raw file uploads via multipart/form-data

## Architecture

```
backend/metric-checker/
├── index.py              # FastAPI application and routes
├── run_metrics.py        # Main metric comparison logic
├── metric_checker.py     # Core MetricChecker class
└── README.md            # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend/metric-checker
   ```

2. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn python-multipart
   ```

3. **Run the application:**
   ```bash
   python index.py
   ```
   Or with uvicorn directly:
   ```bash
   uvicorn index:app --host 0.0.0.0 --port 8000 --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### POST /api/metrics
Compare two JSON files and calculate metrics.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Parameters:
  - `original_file`: Ground truth JSON file (File)
  - `predicted_file`: Predicted output JSON file (File)

**Response:**
```json
{
  "detailed_results": [
    {
      "metric_type": "exact_equality",
      "field_name": null,
      "total_items": 10,
      "exact_matches": 8,
      "accuracy": 0.8,
      "mismatches": [...]
    },
    {
      "metric_type": "list_percentage_match",
      "field_name": "keywords",
      "total_items": 10,
      "perfect_matches": 6,
      "average_percentage": 0.75,
      "details": [...]
    }
  ],
  "summary": {
    "total_metrics_run": 2,
    "exact_equality_metrics": [...],
    "list_percentage_metrics": [...],
    "overall_performance": {
      "average_exact_accuracy": 0.8,
      "average_list_percentage": 0.75
    }
  }
}
```

**Error Response:**
```json
{
  "error": "Error message description"
}
```

### Interactive API Documentation

Once the server is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Metrics Supported

### 1. Exact Equality Metric
Compares fields for exact matches between predicted and ground truth data.

- **Overall Comparison**: Compares entire JSON objects
- **Field-Specific**: Compares individual fields like 'title', 'abstract', 'creator', etc.
- **Output**: Accuracy percentage, exact matches count, mismatch details

### 2. List Percentage Match Metric
Compares list-type fields and calculates percentage overlap.

- **Supported Fields**: 'subject', 'keywords' (configurable)
- **Output**: Average percentage match, perfect matches count, detailed comparisons
- **Features**: Shows matching, missing, and extra elements

## Usage Examples

### Using curl

```bash
curl -X POST "http://localhost:8000/api/metrics" \
  -F "original_file=@ground_truth.json" \
  -F "predicted_file=@model_output.json"
```

### Using Python requests

```python
import requests

url = "http://localhost:8000/api/metrics"
files = {
    'original_file': open('ground_truth.json', 'rb'),
    'predicted_file': open('model_output.json', 'rb')
}

response = requests.post(url, files=files)
results = response.json()
print(results)
```

### Using JavaScript/Frontend

```javascript
const formData = new FormData();
formData.append('original_file', originalFile);
formData.append('predicted_file', predictedFile);

fetch('http://localhost:8000/api/metrics', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Configuration

### CORS Settings
The backend is configured to accept requests from:
- `http://localhost:3000` (React frontend)

To modify CORS settings, edit the `origins` list in `index.py`:

```python
origins = [
    "http://localhost:3000",
    "http://your-frontend-domain.com",
]
```

### Supported Fields
The following metadata fields are analyzed by default:
- `title`
- `abstract`
- `creator`
- `keywords`
- `subject`
- `language`
- `date`

## File Format Requirements

### Input Files
- **Format**: JSON files (.json extension)
- **Structure**: Array of objects or single object
- **Encoding**: UTF-8
- **Size**: No explicit limit (limited by server configuration)

### Example JSON Structure
```json
[
  {
    "id": "item1",
    "title": "Example Title",
    "abstract": "Example abstract text",
    "creator": "Author Name",
    "keywords": ["keyword1", "keyword2"],
    "subject": ["subject1", "subject2"],
    "language": "en",
    "date": "2024-01-01"
  }
]
```

## Error Handling

The API handles various error scenarios:

- **Invalid JSON**: Returns validation error with details
- **Missing files**: Returns error requesting both files
- **File processing errors**: Returns specific error messages
- **Server errors**: Returns 500 status with error details

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn index:app --host 0.0.0.0 --port 8000 --reload

# Or directly
python index.py
```

### Testing

You can test the API using the provided sample files or the interactive documentation at `http://localhost:8000/docs`.

### Code Structure

- **`index.py`**: FastAPI application setup, CORS configuration, and API endpoints
- **`run_metrics.py`**: Main logic for processing file uploads and running metric comparisons
- **`metric_checker.py`**: Core MetricChecker class containing metric calculation algorithms

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Use a different port
   uvicorn index:app --host 0.0.0.0 --port 8001
   ```

2. **CORS errors from frontend**
   - Ensure the frontend URL is in the `origins` list
   - Check that requests are sent to the correct backend URL

3. **File upload issues**
   - Verify files are valid JSON format
   - Check file permissions and accessibility

4. **Import errors**
   ```bash
   # Install missing dependencies
   pip install fastapi uvicorn python-multipart
   ```

### Logs and Debugging

The application outputs logs to the console. For debugging:
- Check console output for error messages
- Use the interactive API docs at `/docs` for testing
- Verify JSON file structure and content

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of a thesis validation system for metadata comparison and analysis.