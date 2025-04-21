# llm_classifier.py
import openai
from typing import Dict, Any, List

class LLMClassifier:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.model = model
        openai.api_key = api_key
        
    def classify_worker_info(self, text_content: str) -> Dict[str, Any]:
        """Use LLM to extract worker information from text."""
        prompt = f"""
        Extract the following information from this document:
        1. Worker name
        2. Worker ID
        3. Hourly rate
        4. Hours worked
        5. Date of work
        
        Document content:
        {text_content}
        
        Format the response as a JSON object with the fields: worker_name, worker_id, hourly_rate, hours_worked, work_date
        """
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from documents."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response to extract the structured information
        return response.choices[0].message.content
        
    def batch_process(self, document_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple documents and extract worker information."""
        results = []
        for doc in document_list:
            worker_info = self.classify_worker_info(doc['content'])
            results.append({
                'filename': doc['filename'],
                'worker_info': worker_info
            })
        return results
