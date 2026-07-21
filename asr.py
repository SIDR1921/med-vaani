import logging

logger = logging.getLogger(__name__)

class ASREngine:
    """Interface: turn an audio file into text."""

    def transcribe(self, audio_path:str) -> str:
        raise NotImplementedError
    
class WhisperEngine(ASREngine):
    def __init__(self, model_name: str, language: str | None = None):
        import whisper
        self.model = whisper.load_model("base")
        logger.info("Loading Whisper model %r...", model_name)
        self.language = language

    def transcribe(self, audio_path: str) -> str:
        options = {}
        if self.language:
            options["language"] = self.language

        result = self.model.transcribe(audio_path, **options)
        return result["text"].strip()