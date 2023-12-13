from whisper_mic import WhisperMic
import threading
import sys

class EnhancedWhisperMic(WhisperMic):
    def __init__(self):
        super().__init__()
        # Additional initialization for EnhancedWhisperMic, if needed

    def listen_loop(self, dictate: bool = False, phrase_time_limit=None) -> None:
        self.recorder.listen_in_background(self.source, self._WhisperMic__record_load, phrase_time_limit=phrase_time_limit)
        self.logger.info("Listening...")
        threading.Thread(target=self._WhisperMic__transcribe_forever, daemon=True).start()
        
        while True:
            try:
                result = self.result_queue.get()
                print(result, flush=True)
                sys.stdout.flush()
            except:
                pass
                
mic = EnhancedWhisperMic()
mic.listen_loop(False,2.8)