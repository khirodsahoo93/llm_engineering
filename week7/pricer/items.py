from pydantic import BaseModel
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


PREFIX = "Price is $"
QUESTION = "What does this cost to the nearest dollar?"


class Item(BaseModel):
    """
    An Item is a data-point of a Product with a Price
    """

    title: str
    category: str
    price: float
    full: Optional[str] = None
    weight: Optional[float] = None
    summary: Optional[str] = None
    prompt: Optional[str] = None
    completion: Optional[str] = None
    id: Optional[int] = None

    def make_prompt(self, text: str):
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{round(self.price)}.00"

    def test_prompt(self) -> str:
        return self.prompt.split(PREFIX)[0] + PREFIX

    def __repr__(self) -> str:
        return f"<{self.title} = ${self.price}>"

    @staticmethod
    def push_to_hub(dataset_name: str, train: list[Self], val: list[Self], test: list[Self]):
        """Push Item lists to HuggingFace Hub"""
        DatasetDict(
            {
                "train": Dataset.from_list([item.model_dump() for item in train]),
                "validation": Dataset.from_list([item.model_dump() for item in val]),
                "test": Dataset.from_list([item.model_dump() for item in test]),
            }
        ).push_to_hub(dataset_name)

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        """Load from HuggingFace Hub and reconstruct Items.
        Handles both full Item datasets and prompt-only datasets."""
        ds = load_dataset(dataset_name)
        
        # Check if this is a prompt-only dataset (only has prompt and completion)
        sample_row = ds["train"][0] if len(ds["train"]) > 0 else None
        is_prompt_only = sample_row and set(sample_row.keys()) == {"prompt", "completion"}
        
        # Handle validation split key (push_prompts_to_hub uses "val", push_to_hub uses "validation")
        val_key = "val" if "val" in ds else "validation"
        
        if is_prompt_only:
            # Create minimal Item objects from prompt/completion pairs
            def create_item_from_prompt(row):
                # Extract price from completion (e.g., "64.00" -> 64.0, "64" -> 64.0)
                completion = row["completion"]
                try:
                    # Try to parse as float directly
                    price = float(completion)
                except (ValueError, AttributeError):
                    # If that fails, try removing ".00" suffix
                    try:
                        price = float(completion.replace(".00", ""))
                    except (ValueError, AttributeError):
                        price = 0.0
                
                return cls(
                    title="Unknown",  # Placeholder - not available in prompt-only format
                    category="Unknown",  # Placeholder - not available in prompt-only format
                    price=price,
                    prompt=row["prompt"],
                    completion=row["completion"]
                )
            
            return (
                [create_item_from_prompt(row) for row in ds["train"]],
                [create_item_from_prompt(row) for row in ds[val_key]] if val_key in ds else [],
                [create_item_from_prompt(row) for row in ds["test"]],
            )
        else:
            # Full Item dataset
            return (
                [cls.model_validate(row) for row in ds["train"]],
                [cls.model_validate(row) for row in ds[val_key]] if val_key in ds else [cls.model_validate(row) for row in ds["validation"]],
                [cls.model_validate(row) for row in ds["test"]],
            )

    def count_tokens(self, tokenizer):
        """Count tokens in the summary"""
        return len(tokenizer.encode(self.summary, add_special_tokens=False))

    def make_prompts(self, tokenizer, max_tokens, do_round):
        """Make prompts and completions"""
        tokens = tokenizer.encode(self.summary, add_special_tokens=False)
        if len(tokens) > max_tokens:
            summary = tokenizer.decode(tokens[:max_tokens]).rstrip()
        else:
            summary = self.summary
        self.prompt = f"{QUESTION}\n\n{summary}\n\n{PREFIX}"
        self.completion = f"{round(self.price)}.00" if do_round else str(self.price)

    def count_prompt_tokens(self, tokenizer):
        """Count tokens in the prompt"""
        full = self.prompt + self.completion
        tokens = tokenizer.encode(full, add_special_tokens=False)
        return len(tokens)

    def to_datapoint(self) -> dict:
        return {"prompt": self.prompt, "completion": self.completion}

    @staticmethod
    def push_prompts_to_hub(
        dataset_name: str, train: list[Self], val: list[Self], test: list[Self]
    ):
        """Push Item lists to HuggingFace Hub in prompt-completion format for SFT training."""
        DatasetDict(
            {
                "train": Dataset.from_list([item.to_datapoint() for item in train]),
                "val": Dataset.from_list([item.to_datapoint() for item in val]),
                "test": Dataset.from_list([item.to_datapoint() for item in test]),
            }
        ).push_to_hub(dataset_name)
