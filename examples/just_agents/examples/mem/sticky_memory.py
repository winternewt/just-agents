import re
from abc import ABC
from typing import List, Dict, Optional, Callable, Union, Tuple
from collections import defaultdict
from functools import cached_property, singledispatchmethod
from pydantic import BaseModel, Field, PrivateAttr, model_validator
from just_agents.interfaces.memory import IMemory  # Your IMemory from memory.py
from litellm import token_counter

HandlerType = Callable[['StickyNote'], None]


class StickyNote(BaseModel):
    """
    Single kanban-style sticky note:
      - name: Up to 16 chars, uppercase, replacing invalid chars with '_'
      - pinned: boolean flag
      - token_weight: integer weight
      - content: text content
      - model: used for token counting, default = "gpt-4o"
    """

    name: str = Field(default="UNTITLED")
    pinned: bool = Field(False)
    token_weight: int = Field(1, ge=1)
    content: str = Field("")
    model: str = Field(default="gpt-4o")

    @staticmethod
    def sanitize_name(raw_name :str) -> str:
        """
        Ensure 'name' is valid, uppercase, truncated, etc.
        Replace all non [A-Z0-9_- ] with '_'.
        If blank/invalid, become "UNTITLED".
        """
        if not raw_name or not isinstance(raw_name, str) or not raw_name.strip():
            raw_name = "UNTITLED"
        raw_name = raw_name.upper()  # Uppercase
        # Replace all non [A-Z0-9_- ] with '_'
        raw_name = re.sub(r"[^A-Z0-9_\- ]", "_", raw_name)
        raw_name = raw_name.strip()
        # If empty after, fallback
        if not raw_name:
            raw_name = "UNTITLED"
        else:
            raw_name = raw_name[:16]  # Truncate to 16 chars
        return raw_name

    @classmethod
    @model_validator(mode="before")
    def fixup_fields(cls, values: Dict) -> Dict:
        raw_name = values.get("name", "")
        values["name"] = cls.sanitize_name(raw_name)
        return values

    @classmethod
    def from_key_value(cls, data: tuple) -> 'StickyNote':
        """
        Construct a StickyNote from a simple pair of name and value
        """
        (name,content) = data
        return cls(name=name,content=content)

    @classmethod
    def from_dict(cls, data: dict) -> 'StickyNote':
        """
        Construct a StickyNote from a simple dictionary of fields,
        e.g. {"messages": [...], ...}.
        """
        return cls(**data) #TODO more robust instantiation

    # TODO: serialization, cache invalidation, computed_property etc
    @cached_property
    def token_count(self) -> int:
        """
        Lazy evaluation of token count using litellm's token_counter.
        """
        messages = [{"role": "assistant", "content": self.content}]
        return token_counter(model=self.model, messages=messages)

    @cached_property
    def tiktoken_estimate(self) -> int:
        """
        Estimate the token count using the tiktoken library.
        Falls back to a worst-case estimate if tiktoken is unavailable or an error occurs.
        """
        worst_case_estimate = len(self.content)
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            tokens = encoding.encode(self.content)
            return len(tokens)
        except (ImportError, KeyError):
            # Handle import errors or unrecognized model keys by falling back to a default encoding
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                tokens = encoding.encode(self.content)
                return len(tokens)
            except Exception:
                pass  # If this also fails, fallback to the worst-case estimate
        except Exception:
            pass  # Catch all other unexpected errors and use the worst-case estimate
        return worst_case_estimate

class StickyNotesMemory(BaseModel, IMemory[str, StickyNote], ABC):
    """
    Concrete Pydantic class implementing IMemory for "sticky-notes."
    Stores 'StickyNote' objects in chronological order.
    """

    # Chronological list of StickyNote messages
    messages: List[StickyNote] = Field(default_factory=list)

    # Dictionary { note_name -> [handlers] }
    _on_message: Dict[str, List[HandlerType]] = PrivateAttr(default_factory=lambda: defaultdict(list))

    # A private field for the memory's "model" that can be synced to each StickyNote
    _model: str = PrivateAttr(default="gpt-4o")

    @property
    def model(self) -> str:
        """
        Get the current model name used for token counting.
        """
        return self._model

    @model.setter
    def model(self, new_model: str) -> None:
        """
        Change the memory-wide model and update all existing notes accordingly.
        """
        self._model = new_model
        for note in self.messages:
            note.model = new_model

    #
    # Required abstract property from IMemory
    #
    @property
    def last_message_str(self) -> Optional[str]:
        """
        Returns the 'content' of the last StickyNote, if any.
        """
        if not self.messages:
            return None
        return self.messages[-1].content

    #
    # Required abstract methods from IMemory
    #
    def handle_message(self, message: StickyNote) -> None:
        """
        Invoke all handlers attached to this note's name.
        """
        note_name = message.name
        for handler in self._on_message[note_name]:
            handler(message)

    def deepcopy(self) -> 'StickyNotesMemory':
        """
        Returns a deep copy of this memory instance.
        """
        return self.model_copy(deep=True)

    def add_pinned_message(self, message: Union[Dict,Tuple,StickyNote]) -> None:
        """
        Overrides the abstract method and provides dispatching to specific handlers.
        """
        self.add_message(message)
        self.last_message.pinned = True

    @singledispatchmethod
    def add_message(self, message: Union[List,Dict,Tuple,StickyNote]) -> None:
        """
        Overrides the abstract method and provides dispatching to specific handlers.
        """
        raise TypeError(f"Unsupported message format: {type(message)}")

    @add_message.register
    def _add_message_sticky(self, message: StickyNote) -> None:
        """
        Appends a StickyNote chronologically. If a note with the same name exists,
        remove it so we can treat the memory like an ordered dict.
        """
        self.messages = [m for m in self.messages if m.name != message.name]
        self.messages.append(message)
        self.handle_message(message)

    @add_message.register
    def _add_message_dict(self, message: tuple) -> None:
        """
        Accepts a dictionary, converts to StickyNote, appends chronologically,
        and handles it (calling any relevant handlers).
        """
        note = StickyNote.from_key_value(message)
        self.add_message(note)


    @add_message.register
    def _add_message_dict(self, message: dict[str, str]) -> None:
        """
        Accepts a dictionary, converts to StickyNote, appends chronologically,
        and handles it (calling any relevant handlers).
        """
        note = StickyNote(**message)
        self.add_message(note)

    @add_message.register
    def _add_message_list(self, messages: list) -> None:
        """
        Handles lists of messages.
        """
        self.add_messages(messages)

    #
    # Additional convenience methods
    #

    def get_cards_by_name(self, name: str) -> List[StickyNote]:
        """
        Retrieve chronologically ordered cards matching 'name' (case-insensitive).
        """
        key = StickyNote.sanitize_name(name)
        return [note for note in self.messages if note.name == key]

    #
    # New convenience methods
    #
    def get_card_by_name(self, name: str) -> Optional[StickyNote]:
        """
        Returns the last (most recent) StickyNote with this name, or None if not found.
        """
        matches = self.get_cards_by_name(name)
        if matches:
            return matches[-1]
        return None

    def pin_card_by_name(self, name: str) -> None:
        """
        Pins the last (most recent) StickyNote with this name, if found.
        """
        card = self.get_card_by_name(name)
        if card:
            card.pinned = True

    def previous_card_by_name(self, name: str) -> Optional[StickyNote]:
        """
        Returns the second-to-last StickyNote with this name, or None if it doesn't exist.
        """
        matches = self.get_cards_by_name(name)
        if len(matches) > 1:
            return matches[-2]
        return None

    def revert_card_by_name(self, name: str) -> bool:
        """
        Removes the last (most recent) StickyNote with this name, only if there is
        a previous one. Returns True if successful, False otherwise.
        """
        key = StickyNote.sanitize_name(name)
        # Gather indices of all notes matching this name
        matching_indices = [i for i, note in enumerate(self.messages) if note.name == key]

        # We can only revert if there's more than one
        if len(matching_indices) > 1:
            # Remove the last index
            last_index = matching_indices[-1]
            self.messages.pop(last_index)
            return True
        return False

    #
    # Handlers management
    #
    def add_on_message(self, handler: HandlerType) -> None:
        """
        Attach a single handler for *all existing note names* in memory.
        """
        unique_names = {note.name for note in self.messages}
        for name in unique_names:
            self.add_on_message_handler(name, handler)

    def add_on_message_handler(self, selector: str, handler: HandlerType) -> None:
        """
        Attach a handler for a specific uppercase 'selector' name.
        """
        key = StickyNote.sanitize_name(selector)
        self._on_message[key].append(handler)

    def remove_on_message(self, handler: HandlerType) -> None:
        """
        Remove a handler from all note names where it is present.
        """
        for name_handlers in self._on_message.values():
            if handler in name_handlers:
                name_handlers.remove(handler)

    def remove_on_message_handler(self, selector: str, handler: HandlerType) -> None:
        """
        Remove a handler from one specific note name, if present.
        """
        key = StickyNote.sanitize_name(selector)
        if handler in self._on_message[key]:
            self._on_message[key].remove(handler)




