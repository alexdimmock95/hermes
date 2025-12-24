import os

# This **must happen before importing** anything from phonemizer
os.environ["PHONEMIZER_ESPEAK_PATH"] = "/opt/homebrew/bin/espeak"
os.environ["PHONEMIZER_ESPEAK_DATA"] = "/opt/homebrew/Cellar/espeak-ng/1.52.0/share/espeak-ng-data"

from phonemizer.backend import EspeakBackend

backend = EspeakBackend(
    language="en-us",
    with_stress=False,
    preserve_punctuation=False,
    language_switch="remove-utterance"
)

text = "Hello, how are you today?"
ipa = backend.phonemize([text], strip=True)[0]
print("IPA:", ipa)