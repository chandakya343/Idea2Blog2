import google.generativeai as genai
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import sys

@dataclass
class MemoryObject:
    interactions: list = field(default_factory=list)
    
    def add_interaction(self, response: str):
        timestamp = datetime.now().isoformat()
        k = len(self.interactions) + 1
        interaction = f"""
<interaction timestamp="{timestamp}">
    <response{k}>
    {response}
    </response{k}>
</interaction>
"""
        self.interactions.append(interaction)
    
    def get_memory_string(self) -> str:
        return "\n".join(self.interactions)

class ThoughtProcessor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")
        self.memory = MemoryObject()
        self.current_narrative = ""
        self.current_growth_points = ""

    def _get_processing_prompt(self, brain_dump: str) -> str:
        base_prompt = """You are an expert analyst who specializes in strengthening and expanding arguments. Your task is to take a brain dump of ideas and:
1. Identify the core arguments
2. Steelman each argument to its strongest form
3. Add supporting evidence and reasoning
4. Expand the implications
5. Find growth directions

Additional Guideline:
1. Do not say anything like "as mentioned in the brain dump" or anything like that.

Brain dump to analyze:
<brain_dump>
{brain_dump}
</brain_dump>

Provide your analysis in these sections:

<connected_narrative>
Build the strongest possible case for the ideas presented:
- Take each core argument and strengthen it
- Add any supporting evidence and examples that might not be mentioned in the original
- Connect ideas in ways that reinforce the main thesis
- Anticipate and address potential counterarguments
- Explore implications that strengthen the overall case
- Use clear reasoning chains to show how conclusions follow
- Structure the narrative to build a compelling case
</connected_narrative>

<growth_points>
Identify promising directions to expand the idea:
- What adjacent areas could this thesis apply to?
- What bigger implications haven't been explored?
- What industries/domains could be impacted?
- What second-order effects might emerge?
- What research areas could strengthen the case?
- What real-world applications could test these ideas?
- What related theses could be developed?

For each growth point:
1. Explain why it's promising
2. Outline initial evidence/reasoning
3. Suggest concrete next steps
4. Note potential impact
</growth_points>

<ai_contributions>
Explain how you built upon the original ideas:
- What evidence/examples did you add?
- What connections did you draw?
- What implications did you identify?
- What counterarguments did you address?
- What reasoning chains did you construct?
- What growth areas did you spot?

Be specific about your contributions so they can be evaluated and built upon.
</ai_contributions>
Be SUPER-CAREFUL about putting the different sections clearly into their own XML tags

"""
        
        return base_prompt.format(brain_dump=brain_dump)

    def _get_refinement_prompt(self, current_narrative: str, refinement_request: str) -> str:
        return f"""You are an expert writer and analyst continuing to develop a narrative about an important idea. Your task is to evolve the current narrative by incorporating new insights or addressing specific aspects while maintaining a cohesive, standalone piece.

Current narrative state:
<current_narrative>
{current_narrative}
</current_narrative>

Focus area to develop:
<refinement_focus>
{refinement_request}
</refinement_focus>

Approach this as an organic development of the ideas. The narrative should:
- Flow as a single, cohesive piece
- Naturally incorporate the requested developments
- Stand on its own as a complete narrative
- Build upon existing points without referencing them as "previous" or "earlier"
- Weave new insights seamlessly into the existing argument structure

<connected_narrative>
[Evolved narrative that naturally incorporates the refinements]
</connected_narrative>

<growth_points>
[Updated opportunities for development based on this evolution:]
- New areas opened by these developments
- Deepened aspects that invite further exploration
- Emerging connections to investigate
</growth_points>

<ai_contributions>
[How the narrative evolved:]
- Deepened aspects
- New connections drawn
- Strengthened arguments
- Added context and support
</ai_contributions>
Be SUPER-CAREFUL about putting the different sections clearly into their own XML tags
"""

    def process_brain_dump(self, brain_dump: str) -> Dict[str, str]:
        """Process initial brain dump"""
        response = self.model.generate_content(
            self._get_processing_prompt(brain_dump)
        ).text
        
        self.memory.add_interaction(response)
        parsed_response = self._parse_response(response)
        self.current_narrative = parsed_response["connected_narrative"]
        self.current_growth_points = parsed_response["growth_points"]
        
        return parsed_response

    def refine_narrative(self, refinement_request: str) -> Dict[str, str]:
        """Handle refinement with natural evolution"""
        response = self.model.generate_content(
            self._get_refinement_prompt(self.current_narrative, refinement_request)
        ).text
        
        self.memory.add_interaction(response)
        parsed_response = self._parse_response(response)
        self.current_narrative = parsed_response["connected_narrative"]
        self.current_growth_points = parsed_response["growth_points"]
        
        return parsed_response

    def export_final_narrative(self, filename: str = "final_narrative.json"):
        """Export the final narrative to a JSON file"""
        output = {
            "connected_narrative": self.current_narrative,
            "growth_points": self.current_growth_points,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        return filename

    def _parse_response(self, response: str) -> Dict[str, str]:
        """Helper to extract content from XML tags"""
        def extract_tag_content(tag: str) -> str:
            start_tag = f"<{tag}>"
            end_tag = f"</{tag}>"
            start_idx = response.find(start_tag) + len(start_tag)
            end_idx = response.find(end_tag)
            return response[start_idx:end_idx].strip()

        return {
            "connected_narrative": extract_tag_content("connected_narrative"),
            "growth_points": extract_tag_content("growth_points"),
            "ai_contributions": extract_tag_content("ai_contributions")
        }

def main():
    processor = ThoughtProcessor("AIzaSyDE9FwV8JNRb7dfRZJi71-7LKTtB57iQyE")
    
    print("Welcome to the Thought Processor!")
    brain_dump = input("Please enter your initial brain dump:\n")
    
    result = processor.process_brain_dump(brain_dump)
    
    print("\nConnected Narrative:")
    print(result["connected_narrative"])
    print("\nGrowth Points:")
    print(result["growth_points"])
    
    while True:
        print("\nOptions:")
        print("1: Suggest a refinement")
        print("2: Export and finish")
        choice = input("Choose an option (1 or 2): ")
        
        if choice == "1":
            refinement = input("Enter your refinement request:\n")
            result = processor.refine_narrative(refinement)
            
            print("\nRefined Narrative:")
            print(result["connected_narrative"])
            print("\nUpdated Growth Points:")
            print(result["growth_points"])
            
        elif choice == "2":
            filename = processor.export_final_narrative()
            print(f"\nFinal narrative exported to {filename}")
            break
        else:
            print("Invalid choice. Please choose 1 or 2.")

if __name__ == "__main__":
    main()