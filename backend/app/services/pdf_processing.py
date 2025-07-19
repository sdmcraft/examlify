import os
import base64
import json
import logging
import tempfile
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from io import BytesIO

from pdf2image import convert_from_path
from PIL import Image
from openai import AzureOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ExamMetadata(BaseModel):
    """Model for exam metadata extracted from PDF"""
    title: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    total_questions: Optional[int] = None
    duration_minutes: Optional[int] = None
    difficulty_level: Optional[str] = None
    pdf_url: Optional[str] = None  # URL of the source PDF

class Question(BaseModel):
    """Model for extracted questions"""
    id: str
    question_text: str
    options: List[str]
    correct_answer: Optional[str] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None
    confidence: Optional[str] = None  # HIGH, MEDIUM, LOW, UNSURE
    page_number: int
    question_number: Optional[str] = None  # Question number (e.g., "1", "2", "3")

class ProcessedExam(BaseModel):
    """Final processed exam structure"""
    metadata: ExamMetadata
    questions: List[Question]

class PDFProcessor:
    """PDF to exam conversion processor using LangChain"""

    def __init__(self):
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # Deployment names for different models
        self.vision_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        self.text_deployment = os.getenv("AZURE_OPENAI_TEXT_DEPLOYMENT_NAME", "gpt-4o")

        self.max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", 50)) * 1024 * 1024
        self.supported_formats = os.getenv("SUPPORTED_IMAGE_FORMATS", "png,jpg,jpeg").split(",")
        self.timeout = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", 300))

    async def process_pdf_from_url(self, pdf_url: str, exam_id: int) -> Dict[str, Any]:
        """
        Main processing pipeline for converting PDF from URL to structured exam

        Args:
            pdf_url: URL of the PDF file
            exam_id: ID of the exam in database

        Returns:
            Dict containing the processed exam data
        """
        temp_file = None
        try:
            logger.info(f"Starting PDF processing for exam {exam_id} from URL: {pdf_url}")

            # Step 0: Download PDF to temp file
            logger.info("Step 0: Downloading PDF from URL")
            temp_file = await self._download_pdf(pdf_url)

            # Step 1: Rasterize PDF to images
            logger.info("Step 1: Rasterizing PDF to images")
            images = await self._rasterize_pdf(temp_file)

            # Step 2: Extract metadata (including PDF URL)
            logger.info("Step 2: Extracting metadata")
            metadata = await self._extract_metadata(images, pdf_url)

            # Step 3: Extract questions
            logger.info("Step 3: Extracting questions")
            questions = await self._extract_questions(images)

            # Step 4: Structure data
            logger.info("Step 4: Structuring data")
            structured_data = self._structure_data(metadata, questions)

            # Step 5: Generate answers and hints
            logger.info("Step 5: Generating answers and hints")
            final_exam = await self._generate_answers(structured_data)

            logger.info(f"PDF processing completed for exam {exam_id}")
            return final_exam.dict()

        except Exception as e:
            logger.error(f"Processing failed for exam {exam_id}: {str(e)}")
            raise
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info(f"Cleaned up temp file: {temp_file}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to clean up temp file {temp_file}: {str(cleanup_error)}")

    async def _download_pdf(self, pdf_url: str) -> str:
        """
        Download PDF from URL to a temporary file

        Args:
            pdf_url: URL of the PDF file

        Returns:
            Path to the temporary PDF file
        """
        try:
            logger.info(f"Downloading PDF from: {pdf_url}")

            # Create a temporary file with .pdf extension
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_path = temp_file.name
            temp_file.close()

            # Download the PDF
            response = await asyncio.to_thread(
                requests.get,
                pdf_url,
                timeout=30,
                stream=True
            )
            response.raise_for_status()

            # Check file size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                raise ValueError(f"PDF file size ({int(content_length)} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)")

            # Save to temp file
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"PDF downloaded successfully to: {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Failed to download PDF from {pdf_url}: {str(e)}")
            raise

    async def _rasterize_pdf(self, pdf_path: str) -> List[str]:
        """
        Step 1: Convert PDF pages to base64 encoded images

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of base64 encoded images (one per page)
        """
        try:
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=200,  # Good balance between quality and size
                fmt='PNG'
            )

            # Convert to base64
            base64_images = []
            for i, image in enumerate(images):
                # Convert PIL image to base64
                buffer = BytesIO()
                image.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                base64_images.append(img_str)

                logger.info(f"Converted page {i+1} to image")

            return base64_images

        except Exception as e:
            logger.error(f"Failed to rasterize PDF: {str(e)}")
            raise

    async def _extract_metadata(self, images: List[str], pdf_url: str) -> ExamMetadata:
        """
        Step 2: Extract exam metadata using LLM vision with function calling

        Args:
            images: List of base64 encoded images
            pdf_url: URL of the source PDF

        Returns:
            ExamMetadata object with extracted information
        """
        try:
            # Use first few pages for metadata extraction
            metadata_images = images[:min(3, len(images))]

            prompt = """
            Analyze these exam pages and extract the following metadata:

            1. Exam title/name
            2. Subject (e.g., Mathematics, Physics, Chemistry)
            3. Topic or chapter
            4. Total number of questions (if visible)
            5. Duration or time limit (if mentioned)
            6. Difficulty level (if indicated)

            If any information is not available, use null for that field.
            """

            # Function definition for metadata extraction
            functions = [
                {
                    "name": "extract_exam_metadata",
                    "description": "Extract metadata from exam pages",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Exam title or name"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Subject name (e.g., Mathematics, Physics)"
                            },
                            "topic": {
                                "type": "string",
                                "description": "Topic or chapter covered"
                            },
                            "total_questions": {
                                "type": "integer",
                                "description": "Total number of questions in the exam"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Exam duration in minutes"
                            },
                            "difficulty_level": {
                                "type": "string",
                                "description": "Difficulty level (e.g., Easy, Intermediate, Hard)"
                            }
                        },
                        "required": ["title"]
                    }
                }
            ]

            # Create messages with images for Azure OpenAI
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                          for img in metadata_images]
                    ]
                }
            ]

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.vision_deployment,
                messages=messages,
                functions=functions,
                function_call={"name": "extract_exam_metadata"},
                max_tokens=16000,
                temperature=0.1
            )

            # Extract function call arguments
            function_call = response.choices[0].message.function_call
            metadata_json = json.loads(function_call.arguments)

            # Add PDF URL to metadata
            metadata_json['pdf_url'] = pdf_url

            return ExamMetadata(**metadata_json)

        except Exception as e:
            logger.error(f"Failed to extract metadata: {str(e)}")
            # Return default metadata with PDF URL
            return ExamMetadata(title="Untitled Exam", pdf_url=pdf_url)

    async def _extract_questions(self, images: List[str]) -> List[Question]:
        """
        Step 3: Extract questions from images using LLM vision with function calling

        Args:
            images: List of base64 encoded images

        Returns:
            List of Question objects
        """
        try:
            questions = []

            # Function definition for question extraction
            functions = [
                {
                    "name": "extract_questions",
                    "description": "Extract questions and options from exam pages",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "questions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "type": "string",
                                            "description": "Unique question ID"
                                        },
                                        "question_number": {
                                            "type": "string",
                                            "description": "Question number (e.g., '1', '2', 'Q1')"
                                        },
                                        "question_text": {
                                            "type": "string",
                                            "description": "The question text"
                                        },
                                        "options": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Multiple choice options (A, B, C, D, etc.)"
                                        }
                                    },
                                    "required": ["id", "question_text", "options"]
                                }
                            }
                        },
                        "required": ["questions"]
                    }
                }
            ]

            for page_num, image in enumerate(images):
                prompt = f"""
                Analyze this exam page (page {page_num + 1}) and extract all questions with their multiple choice options.

                For each question, provide:
                1. A unique ID (q_{page_num + 1}_1, q_{page_num + 1}_2, etc.)
                2. The question number (e.g., "1", "2", "3", "Q1", "Question 1")
                3. The question text
                4. All multiple choice options (A, B, C, D, etc.)

                Look for question numbers in formats like:
                - "1.", "2.", "3."
                - "Q1", "Q2", "Q3"
                - "Question 1", "Question 2"
                - "1)", "2)", "3)"

                If no questions are found on this page, return an empty questions array.
                If the question number cannot be determined, use null for question_number.
                """

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}}
                        ]
                    }
                ]

                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.vision_deployment,
                    messages=messages,
                    functions=functions,
                    function_call={"name": "extract_questions"},
                    max_tokens=16000,
                    temperature=0.1
                )

                # Extract function call arguments
                function_call = response.choices[0].message.function_call
                page_questions = json.loads(function_call.arguments)

                # Add page number to each question
                for question_data in page_questions.get("questions", []):
                    question = Question(
                        id=question_data["id"],
                        question_text=question_data["question_text"],
                        options=question_data["options"],
                        page_number=page_num + 1,
                        question_number=question_data.get("question_number")
                    )
                    questions.append(question)

            return questions

        except Exception as e:
            logger.error(f"Failed to extract questions: {str(e)}")
            return []

    def _structure_data(self, metadata: ExamMetadata, questions: List[Question]) -> ProcessedExam:
        """
        Step 4: Structure the extracted data into a coherent exam format

        Args:
            metadata: Extracted exam metadata
            questions: List of extracted questions

        Returns:
            ProcessedExam object with structured data
        """
        try:
            # Update metadata with actual question count
            metadata.total_questions = len(questions)

            return ProcessedExam(
                metadata=metadata,
                questions=questions
            )

        except Exception as e:
            logger.error(f"Failed to structure data: {str(e)}")
            raise

    async def _generate_answers(self, processed_exam: ProcessedExam) -> ProcessedExam:
        """
        Step 5: Generate correct answers and hints for each question using function calling
        You should research the question and the options to generate the answer and hint.

        Args:
            processed_exam: ProcessedExam object with questions

        Returns:
            ProcessedExam object with answers and hints added
        """
        try:
            updated_questions = []

            # Function definition for answer generation
            functions = [
                {
                    "name": "generate_answer_and_hint",
                    "description": "Generate correct answer and hint for a question",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "correct_answer": {
                                "type": "string",
                                "description": "Letter of the correct option (A, B, C, D, etc.) or 'UNSURE' if uncertain"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Brief explanation of why this answer is correct, or why you're unsure"
                            },
                            "hint": {
                                "type": "string",
                                "description": "Helpful hint that guides without giving away the answer, or what concepts to review"
                            },
                            "confidence": {
                                "type": "string",
                                "description": "Confidence level: 'HIGH', 'MEDIUM', 'LOW', or 'UNSURE'",
                                "enum": ["HIGH", "MEDIUM", "LOW", "UNSURE"]
                            }
                        },
                        "required": ["correct_answer", "explanation", "hint", "confidence"]
                    }
                }
            ]

            for i, question in enumerate(processed_exam.questions):
                try:
                    print(f"Processing question {i+1}/{len(processed_exam.questions)}: {question.question_text[:50]}...")  # Debug log

                    # Create context for the question
                    context = f"""
                    Subject: {processed_exam.metadata.subject or 'General'}
                    Topic: {processed_exam.metadata.topic or 'General'}

                    Question: {question.question_text}
                    Options: {', '.join(question.options)}
                    """

                    # Generate correct answer and hint
                    answer_prompt = f"""
                    Analyze the following question and determine the correct answer. If you are confident about the answer, provide it along with an explanation and hint. If you are unsure or the question requires specialized knowledge beyond your training, indicate this clearly.

                    {context}

                    IMPORTANT GUIDELINES:
                    1. Only provide a confident answer if you are reasonably certain it is correct
                    2. If the question involves complex calculations, diagrams, or specialized knowledge you're unsure about, indicate this
                    3. For questions you can answer confidently, provide:
                       - The letter of the correct option (A, B, C, D, etc.)
                       - A brief explanation of why this is correct
                       - A helpful hint that guides without giving away the answer
                    4. For questions you cannot answer confidently, provide:
                       - "UNSURE" as the correct_answer
                       - An explanation of why you're unsure
                       - A hint about what concepts to review

                    Be honest about your limitations. It's better to indicate uncertainty than to provide incorrect answers.
                    """

                    print(f"Sending request to Azure OpenAI for question {i+1}...")  # Debug log

                    try:
                        # Try with function calling first
                        response = await asyncio.to_thread(
                            self.client.chat.completions.create,
                            model=self.text_deployment,
                            messages=[{"role": "user", "content": answer_prompt}],
                            functions=functions,
                            function_call={"name": "generate_answer_and_hint"},
                            max_tokens=2000,
                            temperature=0.1
                        )
                    except Exception as func_error:
                        print(f"Function calling failed for question {i+1}, trying without functions: {str(func_error)}")  # Debug log
                        # Fallback to regular completion without function calling
                        response = await asyncio.to_thread(
                            self.client.chat.completions.create,
                            model=self.text_deployment,
                            messages=[{"role": "user", "content": answer_prompt + "\n\nPlease respond in JSON format:\n{\n  \"correct_answer\": \"A\",\n  \"explanation\": \"Explanation here\",\n  \"hint\": \"Hint here\"\n}"}],
                            max_tokens=2000,
                            temperature=0.1
                        )

                        # Try to parse JSON from response
                        try:
                            import re
                            response_text = response.choices[0].message.content
                            # Extract JSON from response
                            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                            if json_match:
                                answer_data = json.loads(json_match.group())
                            else:
                                # If no JSON found, create default response
                                answer_data = {
                                    "correct_answer": "UNSURE",
                                    "explanation": "Unable to determine correct answer due to processing issues",
                                    "hint": "Please review the question carefully and consult your study materials",
                                    "confidence": "UNSURE"
                                }
                        except Exception as json_error:
                            print(f"JSON parsing failed for question {i+1}: {str(json_error)}")  # Debug log
                            answer_data = {
                                "correct_answer": "UNSURE",
                                "explanation": "Unable to determine correct answer due to processing issues",
                                "hint": "Please review the question carefully and consult your study materials",
                                "confidence": "UNSURE"
                            }

                        # Skip function call extraction since we used fallback
                        question_dict = question.dict()
                        question_dict.update({
                            'correct_answer': answer_data.get('correct_answer'),
                            'explanation': answer_data.get('explanation'),
                            'hint': answer_data.get('hint'),
                            'confidence': answer_data.get('confidence', 'UNSURE')
                        })
                        updated_question = Question(**question_dict)
                        updated_questions.append(updated_question)
                        continue

                    print(f"Received response for question {i+1}")  # Debug log

                    # Check if function call was successful
                    if not response.choices[0].message.function_call:
                        print(f"No function call in response for question {i+1}")  # Debug log
                        # Use the original question without answers
                        updated_questions.append(question)
                        continue

                    # Extract function call arguments
                    function_call = response.choices[0].message.function_call
                    answer_data = json.loads(function_call.arguments)

                    print(f"Extracted answer data for question {i+1}: {answer_data}")  # Debug log

                    # Update question with answer and hint
                    question_dict = question.dict()
                    question_dict.update({
                        'correct_answer': answer_data.get('correct_answer'),
                        'explanation': answer_data.get('explanation'),
                        'hint': answer_data.get('hint'),
                        'confidence': answer_data.get('confidence', 'UNSURE')
                    })
                    updated_question = Question(**question_dict)

                    updated_questions.append(updated_question)

                except Exception as e:
                    print(f"Error processing question {i+1}: {str(e)}")  # Debug log
                    # Use the original question without answers
                    updated_questions.append(question)

            # Create updated processed exam
            return ProcessedExam(
                metadata=processed_exam.metadata,
                questions=updated_questions
            )

        except Exception as e:
            logger.error(f"Failed to generate answers: {str(e)}")
            # Return original exam without answers if generation fails
            return processed_exam