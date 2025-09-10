"""
Prompt loader utility for code-first extraction pipeline
Loads and formats prompts from template files
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Paradigm-specific role modifiers
PARADIGM_MODIFIERS = {
    "expert_qualitative_coder": "You are an expert qualitative researcher",
    "phenomenological": "You are an expert qualitative researcher trained in phenomenological approaches, focusing on lived experiences, meaning-making, and subjective interpretations",
    "critical_theory": "You are an expert qualitative researcher trained in critical theory approaches, examining power structures, inequalities, and systemic issues",
    "constructivist": "You are an expert qualitative researcher trained in constructivist approaches, focusing on how participants construct reality and social meanings",
    "feminist": "You are an expert qualitative researcher trained in feminist approaches, examining gender dynamics, power relations, and marginalized voices",
    "postmodern": "You are an expert qualitative researcher trained in postmodern approaches, questioning dominant narratives and exploring multiple perspectives"
}

class PromptLoader:
    """Load and format prompts from template files"""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize prompt loader
        
        Args:
            prompts_dir: Path to prompts directory (defaults to src/qc/prompts)
        """
        if prompts_dir is None:
            # Default to prompts directory relative to this file
            self.prompts_dir = Path(__file__).parent
        else:
            self.prompts_dir = Path(prompts_dir)
        
        if not self.prompts_dir.exists():
            raise ValueError(f"Prompts directory not found: {self.prompts_dir}")
        
        logger.info(f"PromptLoader initialized with directory: {self.prompts_dir}")
        
        # Cache loaded templates
        self._template_cache: Dict[str, str] = {}
    
    def load_template(self, phase: str, template_name: str) -> str:
        """
        Load a prompt template from file
        
        Args:
            phase: Phase directory (phase1, phase2, phase3, phase4)
            template_name: Template filename without extension
        
        Returns:
            Template string
        """
        cache_key = f"{phase}/{template_name}"
        
        # Check cache first
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        # Load from file
        template_path = self.prompts_dir / phase / f"{template_name}.txt"
        
        if not template_path.exists():
            raise ValueError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Cache for future use
        self._template_cache[cache_key] = template
        logger.debug(f"Loaded template: {cache_key}")
        
        return template
    
    def format_prompt(self, phase: str, template_name: str, **kwargs) -> str:
        """
        Load and format a prompt template with variables
        
        Args:
            phase: Phase directory
            template_name: Template filename without extension
            **kwargs: Variables to substitute in template
        
        Returns:
            Formatted prompt string
        """
        template = self.load_template(phase, template_name)
        
        # Apply paradigm modifier if paradigm is provided
        paradigm = kwargs.get('paradigm', 'expert_qualitative_coder')
        if paradigm in PARADIGM_MODIFIERS:
            paradigm_role = PARADIGM_MODIFIERS[paradigm]
            # Replace the default "You are analyzing" with paradigm-specific role
            if template.startswith("You are analyzing"):
                template = template.replace("You are analyzing", f"{paradigm_role}, analyzing", 1)
            elif template.startswith("You are"):
                template = template.replace("You are", paradigm_role, 1)
            else:
                # Prepend paradigm role if no existing role statement
                template = f"{paradigm_role}. {template}"
        
        try:
            # Use format with kwargs for substitution
            formatted = template.format(**kwargs)
            return formatted
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            logger.error(f"Available variables: {list(kwargs.keys())}")
            raise ValueError(f"Template variable missing: {e}")
    
    def generate_code_examples(self, codes: list, max_examples: int = 3) -> str:
        """
        Generate example code applications from actual taxonomy
        
        Args:
            codes: List of HierarchicalCode objects
            max_examples: Maximum number of examples to generate
        
        Returns:
            Formatted examples string
        """
        if not codes:
            return "No codes available for examples"
        
        examples = []
        
        # Create examples using actual code IDs
        example_scenarios = [
            {
                "quote": "We use AI for transcribing our interviews and it saves a lot of time",
                "relevant_codes": lambda c: "transcri" in c.name.lower() or "data collection" in c.name.lower()
            },
            {
                "quote": "I worry about the accuracy and hallucinations in AI-generated analysis",
                "relevant_codes": lambda c: "risk" in c.name.lower() or "challenge" in c.name.lower() or "limitation" in c.name.lower()
            },
            {
                "quote": "Our organization is struggling with how to adopt AI tools responsibly",
                "relevant_codes": lambda c: "adoption" in c.name.lower() or "organization" in c.name.lower() or "strateg" in c.name.lower()
            }
        ]
        
        for i, scenario in enumerate(example_scenarios[:max_examples]):
            # Find matching codes from actual taxonomy
            matching_codes = [
                code.id for code in codes 
                if scenario["relevant_codes"](code)
            ][:2]  # Limit to 2 codes per example
            
            if matching_codes:
                examples.append(
                    f'   Quote: "{scenario["quote"]}"\n'
                    f'   Correct code_ids: {matching_codes}'
                )
        
        if not examples:
            # Fallback: just use first few codes as generic example
            code_ids = [code.id for code in codes[:3]]
            examples.append(
                f'   Quote: "This is an example quote about the research topic"\n'
                f'   Correct code_ids: {code_ids[:2]}'
            )
        
        return "\n\n".join(examples)
    
    def reload_templates(self):
        """Clear template cache to force reload from disk"""
        self._template_cache.clear()
        logger.info("Template cache cleared - will reload from disk")


# Singleton instance for convenience
_default_loader = None

def get_prompt_loader(prompts_dir: Optional[Path] = None) -> PromptLoader:
    """
    Get or create the default prompt loader
    
    Args:
        prompts_dir: Optional prompts directory path
    
    Returns:
        PromptLoader instance
    """
    global _default_loader
    
    if _default_loader is None or prompts_dir is not None:
        _default_loader = PromptLoader(prompts_dir)
    
    return _default_loader