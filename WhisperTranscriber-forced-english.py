import time

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from transformers import WhisperForConditionalGeneration
from transformers import WhisperFeatureExtractor
from transformers import WhisperTokenizer
from transformers import pipeline

# This version attempts to do transcription only (no translation) -- however it does not work:

# init ran for  20.47254967689514 seconds
# Traceback (most recent call last):
#   File "/app/main.py", line 32, in <module>
# main()
#   File "/app/main.py", line 22, in main
# result = transcriber.transcribe(url)
#   File "/app/WhisperTranscriber.py", line 60, in transcribe
#     result = self.pipe(audio_source)
#   File "/app/WhisperTranscriber.py", line 49, in pipe
# return self.pipe_function(audio_source, generate_kwargs={"forced_decoder_ids": self.forced_decoder_ids})
#   File "/opt/conda/lib/python3.10/site-packages/transformers/pipelines/automatic_speech_recognition.py", line 357, in __call__
# return super().__call__(inputs, **kwargs)
#   File "/opt/conda/lib/python3.10/site-packages/transformers/pipelines/base.py", line 1132, in __call__
# return next(
#   File "/opt/conda/lib/python3.10/site-packages/transformers/pipelines/pt_utils.py", line 124, in __next__
#     item = next(self.iterator)
#   File "/opt/conda/lib/python3.10/site-packages/transformers/pipelines/pt_utils.py", line 266, in __next__
# processed = self.infer(next(self.iterator), **self.params)
#   File "/opt/conda/lib/python3.10/site-packages/transformers/pipelines/base.py", line 1046, in forward
# model_outputs = self._forward(model_inputs, **forward_params)
#   File "/opt/conda/lib/python3.10/site-packages/transformers/pipelines/automatic_speech_recognition.py", line 555, in _forward
# encoder_outputs=encoder(inputs, attention_mask=attention_mask),
#   File "/opt/conda/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1501, in _call_impl
# return forward_call(*args, **kwargs)
#   File "/opt/conda/lib/python3.10/site-packages/transformers/models/whisper/modeling_whisper.py", line 1119, in forward
# inputs_embeds = nn.functional.gelu(self.conv1(input_features))
#   File "/opt/conda/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1501, in _call_impl
# return forward_call(*args, **kwargs)
#   File "/opt/conda/lib/python3.10/site-packages/torch/nn/modules/conv.py", line 313, in forward
# return self._conv_forward(input, self.weight, self.bias)
#   File "/opt/conda/lib/python3.10/site-packages/torch/nn/modules/conv.py", line 309, in _conv_forward
# return F.conv1d(input, weight, bias, self.stride,
# RuntimeError: Input type (torch.cuda.HalfTensor) and weight type (torch.cuda.FloatTensor) should be the same

class WhisperTranscriber:
    """Hugging Face code for streaming audio URLs into transcriptions"""
    def __init__(self):
        start = time.time()
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # model_id = "openai/whisper-large-v3"
        model_id = "./model"

        # model = AutoModelForSpeechSeq2Seq.from_pretrained(
        #     model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        # )

        # processor = AutoProcessor.from_pretrained(model_id)
        
        feature_extractor = WhisperFeatureExtractor.from_pretrained(model_id)
        tokenizer = WhisperTokenizer.from_pretrained(model_id, language="english", task="transcribe")
        self.forced_decoder_ids = tokenizer.get_decoder_prompt_ids(language="english", task="transcribe")

        model = WhisperForConditionalGeneration.from_pretrained(model_id)

        model.to(device)

        self.pipe_function = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=tokenizer,
            feature_extractor=feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device
        )
        print('init ran for ', time.time()-start, 'seconds')

    def pipe(self, audio_source):
        return self.pipe_function(audio_source, generate_kwargs={"forced_decoder_ids": self.forced_decoder_ids})
        
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
    sample = 'sample_fr.mp3'
    final_result = whisper.transcribe(sample)
    print(final_result)
    