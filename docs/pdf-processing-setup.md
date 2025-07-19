# PDF Processing Setup Guide

## Prerequisites

### System Dependencies

#### Ubuntu/Debian
```bash
# Install poppler-utils for PDF processing
sudo apt-get update
sudo apt-get install poppler-utils

# Install Python development tools
sudo apt-get install python3-dev python3-pip python3-venv
```

#### macOS
```bash
# Install poppler using Homebrew
brew install poppler

# Install Python (if not already installed)
brew install python3
```

#### Windows
```bash
# Download and install poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
# Add poppler to your PATH environment variable

# Install Python from: https://www.python.org/downloads/
```

### Python Dependencies

Install the required Python packages:

```bash
cd backend
pip install -r requirements.txt
```

## Environment Configuration

### 1. Create Environment File

Copy the example environment file:
```bash
cp env.example .env
```

### 2. Configure Azure OpenAI

Edit the `.env` file and add your Azure OpenAI configuration:
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=2fc838464a1d4cd88c3ab99b5b7623c8
AZURE_OPENAI_ENDPOINT=https://satyam-oai.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-04-14
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-41
AZURE_OPENAI_TEXT_DEPLOYMENT_NAME=gpt-41


# Processing Configuration
MAX_FILE_SIZE_MB=50
SUPPORTED_IMAGE_FORMATS=png,jpg,jpeg
PROCESSING_TIMEOUT_SECONDS=300
```

### 3. Get Azure OpenAI Configuration

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint" section
4. Copy the endpoint URL and API key
5. Note your deployment name for GPT-4o (supports both text and vision with improved performance)
6. Update the `.env` file with your configuration

## Database Setup

### 1. Run Database Migration

Execute the migration script to add the status column:
```bash
# Connect to your MySQL database
mysql -u your_username -p your_database_name < database/add_status_column.sql
```

### 2. Verify Migration

Check that the status column was added:
```sql
DESCRIBE exams;
```

You should see the `status` column with type `VARCHAR(50)`.

## Testing the Setup

### 1. Create Test PDF

Create a simple test PDF with multiple choice questions. You can use any PDF creation tool or convert a Word document to PDF.

### 2. Run Test Script

```bash
cd backend
python test_pdf_processing.py
```

Expected output:
```
🚀 Starting PDF processing test...
📄 Processing PDF...
✅ PDF processing completed successfully!
📊 Exam Title: Your Exam Title
📚 Subject: Mathematics
📝 Topic: Algebra
❓ Total Questions: 10
📊 Diagrams Found: 2

📋 Sample Questions:
  1. What is the value of x in the equation 2x + 5 = 15?...
     Options: 4 options
     Correct Answer: A

🎉 All tests passed!
```

### 3. Test API Endpoint

Start the FastAPI server:
```bash
cd backend
uvicorn app.main:app --reload
```

Upload a PDF using the API:
```bash
# Step 1: Create a new exam
curl -X POST "http://localhost:8000/api/exams" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Exam",
    "description": "Test exam for PDF processing"
  }'

# Step 2: Upload PDF to the created exam (replace {exam_id} with the actual ID from step 1)
curl -X POST "http://localhost:8000/api/exams/{exam_id}/upload" \
  -H "Authorization: Bearer your_jwt_token" \
  -F "pdf_file=@test_exam.pdf"
```

## Troubleshooting

### Common Issues

#### 1. Poppler Not Found
**Error:** `pdf2image.exceptions.PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and accessible?`

**Solution:**
- Install poppler-utils: `sudo apt-get install poppler-utils` (Ubuntu/Debian)
- Or install poppler: `brew install poppler` (macOS)
- Ensure poppler is in your PATH

#### 2. Azure OpenAI API Key Issues
**Error:** `openai.AuthenticationError: Incorrect API key provided`

**Solution:**
- Verify your Azure OpenAI API key is correct
- Check that your Azure OpenAI resource is active
- Ensure the endpoint URL is correct
- Verify deployment name matches your Azure setup
- Check that the API version is supported

#### 3. Memory Issues
**Error:** `MemoryError` or slow processing

**Solution:**
- Reduce PDF file size
- Lower DPI setting in the processor (currently 200)
- Process smaller PDFs first

#### 4. Database Connection Issues
**Error:** `sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError)`

**Solution:**
- Check database connection settings
- Ensure MySQL server is running
- Verify database credentials

### Debug Mode

Enable debug logging by setting the log level in your application:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization

### 1. API Rate Limits

Azure OpenAI has rate limits for API calls. Monitor your usage:
- GPT-4 Vision: Varies by tier (typically 500-1000 requests per minute)
- GPT-4 Text: Varies by tier (typically 500-1000 requests per minute)
- Check your Azure OpenAI resource quotas in the Azure portal

### 2. Processing Optimization

- Use appropriate DPI settings (200 DPI is optimal)
- Process smaller PDFs for faster results
- Consider batch processing for multiple files

### 3. Resource Management

- Monitor memory usage during processing
- Clean up temporary files automatically
- Use appropriate timeout settings

## Security Considerations

### 1. API Key Security

- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate API keys regularly

### 2. File Upload Security

- Validate file types and sizes
- Scan uploaded files for malware
- Implement proper access controls

### 3. Data Privacy

- Ensure compliance with data protection regulations
- Implement proper data retention policies
- Secure storage of processed exam data

## Next Steps

After successful setup:

1. **Test with Real PDFs**: Upload actual exam PDFs to test the system
2. **Monitor Performance**: Track processing times and success rates
3. **Optimize Prompts**: Fine-tune LLM prompts for better extraction
4. **Scale Up**: Consider implementing background processing for large files
5. **Add Features**: Implement additional question types and formats

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for detailed error messages
3. Test with a simple PDF first
4. Verify all dependencies are properly installed
5. Check OpenAI API status and rate limits