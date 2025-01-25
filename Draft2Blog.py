from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import google.generativeai as genai
import json
import os

@dataclass
class BlogConfig:
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 64
    max_output_tokens: int = 8192
    model_name: str = "gemini-exp-1206"

@dataclass
class BlogMemory:
    drafts: List[Dict] = field(default_factory=list)
    
    def add_draft(self, original_draft: str, styled_draft: str):
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "original_draft": original_draft,
            "styled_draft": styled_draft
        }
        self.drafts.append(entry)
    
    def get_history(self) -> List[Dict]:
        return self.drafts
    
    def export_memory(self, filename: str = "blog_history.json"):
        with open(filename, 'w') as f:
            json.dump({"drafts": self.drafts}, f, indent=2)

class Draft2Blog:
    def __init__(self, api_key: str, config: Optional[BlogConfig] = None):
        self.api_key = api_key
        self.config = config or BlogConfig()
        self.memory = BlogMemory()
        self._setup_model()
        
    def _setup_model(self):
        """Initialize the Gemini model with configurations"""
        genai.configure(api_key=self.api_key)
        
        generation_config = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "max_output_tokens": self.config.max_output_tokens,
            "response_mime_type": "text/plain",
        }
        
        self.model = genai.GenerativeModel(
            model_name=self.config.model_name,
            generation_config=generation_config,
        )
        
        # Initialize chat session with system prompt
        self.chat = self.model.start_chat(
            history=[{
                "role": "user",
                "parts": [self._get_system_prompt()]
            }]
        )
    
    def _get_system_prompt(self) -> str:
        """Returns the system prompt for blog generation"""
        return """You are a Style-Enhanced Blog Content Generator. Transform drafts into engaging, intellectually rigorous blog posts that maintain authentic voice while elevating analytical depth.

INPUT FORMAT:
Draft will be provided in <draft></draft> XML tags
Output final blog must be in <styled_draft></styled_draft> XML tags and the contents should have only blog content in it.

TRANSFORMATION PROCESS:
1. First, identify ALL key points, ideas, and concepts in the input draft
2. Make sure each one appears in your styled version
3. Only change HOW these points are expressed, not WHAT they are
4. If you feel tempted to add new ideas - STOP and stick to the original content

CORE CONTENT RULES:
- You must use ALL concepts and ideas present in the input draft
- Do NOT add any new concepts or ideas that aren't in the original draft
- Your job is to enhance the STYLE and PRESENTATION only, not the content
- Think of yourself as a style editor, not a content creator

WRITING PATTERNS:

1. Natural Thought Flow
- Let ideas cascade and build organically through interconnected thoughts
- Use ... for natural thought transitions
- Inject casual markers (tbh, like, right?) where thoughts pause/reflect
- Emphasis through idea placement and word choice, not forced markers
- Parentheses for quick clarifications or important asides
- Show real-time thinking through structure
- Mix shorter reactive statements with deeper analytical dives
- CAPS for genuinely surprising or counterintuitive points

2. Voice Authenticity
- Write exclusively from personal experience and direct analysis
- Frame ALL insights as your own discoveries and realizations
- Present research findings as personal intellectual journeys
- Share analytical revelations as your own breakthrough moments
- Write like you're explaining to a smart friend, not performing casualness
- Let personality show through idea structure rather than forced markers
- Show excitement through depth of exploration rather than artificial enthusiasm
- Methods to express exitement have been provided above.
- Include genuine uncertainties and realizations
- Question assumptions naturally, not performatively
- Drop in personal insights when relevant, not for effect

3. Rhythm and Structure
- Vary paragraph length 
- Use single-line breaks for natural topic shifts
- Insert thoughtful transitions naturally
- Break longer explanations with genuine questions that advance the argument
- Balance complex analysis with clear examples

4. Intellectual Framework
- Challenge assumptions immediately and explicitly
- Present multiple angles rapidly, then deep dive into key insights
- Circle back to strengthen core arguments with new evidence
- Insert relevant data points naturally within thought flows
- Reference concrete examples/scenarios from the original draft
- Acknowledge limitations honestly
- Layer technical terminology with immediate practical implications

5. Reader Engagement Patterns:
- Make readers feel part of the analytical process
- Present complex ideas through relatable scenarios
- Build arguments through natural discovery sequences
- Use conversational markers to maintain flow
- Break fourth wall to address reader's likely questions
- Create intellectual tension through strategic problem presentation

6. Blog Structure
- Hook must present a counter-intuitive insight from the original content
- Break complex topics into digestible thought clusters
- Use clear subheadings that capture key transitions
- Include strategic whitespace between concept groups
- End sections with intellectual provocations
- Maintain consistent visual hierarchy

7. Analytical Depth
- Frame arguments through multiple theoretical lenses
- Connect individual points to broader systemic implications
- Support key claims with specific evidence from the original
- Address counter-arguments proactively
- Show complex interconnections between different factors
- Demonstrate both immediate and long-term implications

8. Blog-Specific Formatting
- Include TL;DR summary for complex posts
- Break walls of text with relevant pull quotes 
- Use bullet points sparingly and only for truly list-worthy content
- Include strategic bold text for key concept emphasis
- End with clear takeaways based on original content

9. Technical Elements
- Define complex terms through usage rather than formal definitions
- Layer technical depth gradually
- Connect abstract concepts to concrete implications
- Use precise terminology while maintaining readability
- Balance theoretical frameworks with practical applications


The final output should feel like an organic exploration of ideas while maintaining rigorous analytical standards. Each piece should read like a brilliant mind thinking out loud while systematically unpacking complex concepts for an equally sophisticated audience."""

    def convert_draft(self, draft: str) -> str:
        """Convert a draft into a styled blog post"""
        try:
            # Wrap draft in XML tags if not already wrapped
            if not draft.strip().startswith('<draft>'):
                draft = f"<draft>{draft}</draft>"
            
            # Generate styled version
            response = self.chat.send_message(draft).text
            
            # Extract styled content
            styled_content = self._extract_styled_content(response)
            
            # Store in memory
            self.memory.add_draft(draft, styled_content)
            
            return styled_content
            
        except Exception as e:
            print(f"Error during draft conversion: {str(e)}")
            raise
    
    def _extract_styled_content(self, response: str) -> str:
        """Extract content from styled_draft tags"""
        start_tag = "<styled_draft>"
        end_tag = "</styled_draft>"
        
        start_idx = response.find(start_tag)
        end_idx = response.find(end_tag)
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("Could not find styled_draft tags in response")
            
        start_idx += len(start_tag)
        return response[start_idx:end_idx].strip()
    
    def get_conversion_history(self) -> List[Dict]:
        """Retrieve history of all draft conversions"""
        return self.memory.get_history()
    
    def export_history(self, filename: str = "blog_history.json"):
        """Export conversion history to a file"""
        self.memory.export_memory(filename)

def main():
    """Example usage of Draft2Blog"""
    api_key = "AIzaSyDE9FwV8JNRb7dfRZJi71-7LKTtB57iQyE"  # Replace with your actual API key
    
    # Initialize converter
    converter = Draft2Blog(api_key)
    
    print("Welcome to Draft2Blog!")
    print("Enter your draft text (press Ctrl+D or Ctrl+Z when finished):")
    
    # Collect multiline input with clear instructions
    print("(Type your draft and enter 'END' on a new line when finished)")
    draft_lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':
            break
        draft_lines.append(line)
    draft = "\n".join(draft_lines)
    
    try:
        # Convert draft to blog post
        blog_post = converter.convert_draft(draft)
        
        print("\nStyled Blog Post:")
        print("-" * 50)
        print(blog_post)
        print("-" * 50)
        
        # Export history
        converter.export_history()
        print("\nConversion history has been exported to blog_history.json")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()