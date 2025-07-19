# PDF Processing Documentation

## Overview

The PDF processing system converts uploaded PDF exam files into structured, machine-readable exam data using LangChain and OpenAI's GPT-4 Vision model. The system follows a 5-step workflow to extract questions, diagrams, and metadata from PDF files.

## Architecture

### Components

1. **PDFProcessor** (`backend/app/services/pdf_processing.py`)
   - Main processing class that orchestrates the 5-step workflow
   - Uses LangChain for LLM integration
   - Handles both vision and text-based LLM operations

2. **FileUtils** (`backend/app/utils/file_utils.py`)
   - Utility class for file validation, saving, and cleanup
   - Handles temporary directory management
   - Validates PDF file size and format

3. **Exam Handler** (`backend/app/api/handlers/exam_handler.py`)
   - Updated to integrate PDF processing
   - Handles async processing workflow
   - Updates exam status and stores processed data

## Processing Workflow

### Step 0: PDF Rasterization
- Converts PDF pages to high-quality PNG images (200 DPI)
- Stores images as base64 encoded strings
- Uses `pdf2image` library for conversion

### Step 1: Metadata Extraction
- Analyzes first 3 pages using GPT-4 Vision
- Extracts exam title, subject, topic, duration, difficulty level
- Returns structured metadata in JSON format

### Step 2: Diagram Extraction
- Processes each page to identify diagrams, charts, and images
- Extracts diagram descriptions and positions
- Links diagrams to questions that reference them

### Step 3: Question Extraction
- Extracts multiple choice questions from each page
- Identifies question text and all options (A, B, C, D, etc.)
- Links questions to relevant diagrams

### Step 4: Data Structuring
- Organizes extracted data into coherent exam structure
- Updates metadata with actual question count
- Creates structured JSON format

### Step 5: Answer Generation
- Uses GPT-4 text model to generate correct answers
- Creates helpful hints for each question
- Provides explanations for correct answers

## Data Models

### ExamMetadata
```python
class ExamMetadata(BaseModel):
    title: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    total_questions: Optional[int] = None
    duration_minutes: Optional[int] = None
    difficulty_level: Optional[str] = None
```

### Diagram
```python
class Diagram(BaseModel):
    id: str
    base64_image: str
    description: str
    page_number: int
    position: Dict[str, int]  # x, y coordinates
```

### Question
```python
class Question(BaseModel):
    id: str
    question_text: str
    options: List[str]
    correct_answer: Optional[str] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None
    diagram_ids: List[str] = []
    page_number: int
```

## API Integration

### Upload Endpoint
```
POST /api/exams/upload
```

**Request:**
- `pdf_file`: PDF file upload
- `title`: Exam title
- `description`: Optional description
- `duration_minutes`: Optional duration

**Response:**
```json
{
    "exam_id": 123,
    "status": "processed",
    "message": "PDF uploaded and processed successfully.",
    "filename": "exam_123_20241201_143022.pdf",
    "total_questions": 25
}
```

### Exam Status Values
- `draft`: Exam created but no PDF uploaded
- `uploaded`: PDF uploaded but not yet processed
- `processed`: PDF successfully processed with questions extracted
- `processing_failed`: PDF uploaded but processing failed

## Configuration

### Environment Variables
```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL_NAME=gpt-4-vision-preview

# Processing Configuration
MAX_FILE_SIZE_MB=50
SUPPORTED_IMAGE_FORMATS=png,jpg,jpeg
PROCESSING_TIMEOUT_SECONDS=300
```

### Dependencies
```txt
langchain==0.1.0
langchain-openai==0.0.5
langchain-community==0.0.10
pdf2image==1.16.3
pillow==10.0.0
pydantic==2.5.0
aiofiles==23.2.1
```

## Error Handling

### Processing Failures
- If PDF processing fails, the exam status is set to `processing_failed`
- The upload operation still succeeds, but questions are not extracted
- Error details are stored in the `questions_json` field

### File Validation
- Validates PDF file format
- Checks file size limits (default: 50MB)
- Ensures file is not empty

### LLM API Failures
- Graceful degradation if LLM API calls fail
- Returns partial results when possible
- Logs detailed error information

## Testing

### Test Script
Run the test script to verify PDF processing:
```bash
cd backend
python test_pdf_processing.py
```

**Requirements:**
- OpenAI API key set in environment
- Test PDF file named `test_exam.pdf` in backend directory

### Manual Testing
1. Start the FastAPI server
2. Upload a PDF through the `/api/exams/upload` endpoint
3. Check the exam status and processed data
4. Verify questions, answers, and diagrams are extracted correctly

## Performance Considerations

### Processing Time
- Typical processing time: 30-60 seconds per PDF
- Depends on number of pages and complexity
- Vision API calls are the main bottleneck

### Resource Usage
- Temporary storage for image conversion
- Memory usage scales with PDF size
- Automatic cleanup of temporary files

### Optimization Tips
- Use appropriate DPI settings (200 DPI is optimal)
- Limit concurrent processing for large files
- Monitor API rate limits

## Future Enhancements

### Planned Features
1. **Batch Processing**: Process multiple PDFs concurrently
2. **Progress Tracking**: Real-time processing status updates
3. **Multiple LLM Providers**: Support for Anthropic, Google, etc.
4. **Advanced Diagram Extraction**: Better diagram isolation and cropping
5. **Question Type Detection**: Support for different question formats
6. **Answer Validation**: Cross-check generated answers for accuracy

### Scalability Improvements
1. **Async Processing**: Background job processing
2. **Caching**: Cache processed results
3. **Compression**: Optimize image storage
4. **CDN Integration**: Store diagrams in cloud storage

## Troubleshooting

### Common Issues

1. **PDF2Image Errors**
   - Ensure poppler is installed on the system
   - Check PDF file integrity
   - Verify file permissions

2. **LLM API Errors**
   - Check API key validity
   - Monitor rate limits
   - Verify model availability

3. **Memory Issues**
   - Reduce DPI for large PDFs
   - Process pages in batches
   - Monitor system resources

### Debug Mode
Enable detailed logging by setting log level to DEBUG in your application configuration.

## Security Considerations

1. **File Validation**: Strict PDF file validation
2. **Size Limits**: Configurable file size restrictions
3. **Temporary File Cleanup**: Automatic cleanup of processing files
4. **API Key Security**: Secure storage of LLM API keys
5. **Input Sanitization**: Validate all extracted data before storage