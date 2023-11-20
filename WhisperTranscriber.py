import time

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


class WhisperTranscriber:
    """Hugging Face code for streaming audio URLs into transcriptions"""
    def __init__(self):
        start = time.time()
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # model_id = "openai/whisper-large-v3"
        model_id = "./model"

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(device)

        processor = AutoProcessor.from_pretrained(model_id)

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )
        print('init ran for ', time.time()-start, 'seconds')
        
    def transcribe(self, audio_source):
        """Transcribe an audio file (wav, mp3) referenced by a URL or filename into text
        
        Parameters:
        audio_source (string): URL or local filename
        
        Returns:
        string: JSON string containing transcription and audio alignment time points"""
        start_time = time.time()
        result = self.pipe(audio_source)
        result['elapsed_seconds'] = time.time() - start_time
        return result

if __name__ == '__main__':
    whisper = WhisperTranscriber()
    # sample = 'https://media.dharmaseed.org/recordings/sample.mp3'
    sample = 'audio/sample_fr.mp3'
    final_result = whisper.transcribe(sample)
    print(final_result)
    