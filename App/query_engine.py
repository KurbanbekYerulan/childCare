"""
Query engine that coordinates between Screenpipe and LLaMA.
"""

import config

class QueryEngine:
    def __init__(self, screenpipe_connector, llama_client, time_window=300):
        """Initialize the query engine."""
        self.screenpipe = screenpipe_connector
        self.llama = llama_client
        self.time_window = time_window
        
    def process_query(self, query):
        """Process a user query against recent screen content."""
        # Get recent OCR text
        ocr_text = self.screenpipe.get_recent_ocr_text(self.time_window)
        
        if not ocr_text:
            return "No screen content found in the specified time window."
            
        # Truncate OCR text if it's too long
        if len(ocr_text) > config.MAX_OCR_TEXT_LENGTH:
            ocr_text = ocr_text[:config.MAX_OCR_TEXT_LENGTH] + "...[truncated]"
            
        # Send to LLaMA
        response = self.llama.query(ocr_text, query)
        return response
        
    def analyze_current_app(self):
        """Analyze the current app being used based on screen content."""
        # Get recent OCR text
        ocr_text = self.screenpipe.get_recent_ocr_text(self.time_window)
        
        if not ocr_text:
            return "No screen content found in the specified time window."
            
        # Truncate OCR text if it's too long
        if len(ocr_text) > config.MAX_OCR_TEXT_LENGTH:
            ocr_text = ocr_text[:config.MAX_OCR_TEXT_LENGTH] + "...[truncated]"
        
        # Get app name from Screenpipe if available
        app_info = self.screenpipe.get_current_app_info()
        app_name = app_info.get("app_name", "Unknown")
        window_name = app_info.get("window_name", "")
        
        # Create a specialized prompt for app analysis
        analysis_prompt = f"""
Based on the screen content, analyze the application that appears to be in use.
If you can identify the app, provide the following information in this exact format:

Currently Using: [App Name]
Category of App: [App Category - e.g., Social Media, Productivity, Gaming, etc.]
Is this App suitable for minors: [Yes/No]
The recommended usage time for minors: [Recommended time]
Age Rating: [Appropriate age rating]
Potential Concerns: [List any potential concerns for parents]
Educational Value: [Rate from 1-10 and explain]
Alternative Apps: [Suggest 2-3 more educational/appropriate alternatives if needed]

If the app name is clearly visible in the OCR text, use that. Otherwise, make your best guess based on the content.
Current app name according to system: {app_name} {window_name}
        """
        
        # Send to LLaMA
        response = self.llama.query(ocr_text, analysis_prompt)
        return response 