"""Avatar transport preserves claim configuration and separates output media."""
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from live_demo.live_tools import build_live_config
from live_demo import server


class AvatarConfigTests(unittest.TestCase):
    def test_avatar_changes_only_output_and_appearance(self):
        voice = build_live_config(camera_enabled=True).model_dump(exclude_none=True)
        avatar = build_live_config(camera_enabled=True, avatar_name='Ben').model_dump(exclude_none=True)
        self.assertEqual([str(m.value) for m in avatar.pop('response_modalities')], ['VIDEO'])
        self.assertEqual(avatar.pop('avatar_config')['avatar_name'], 'Ben')
        voice.pop('response_modalities')
        # Each build stamps the current reference clock; preserve the rest verbatim.
        self.assertEqual(voice.pop('system_instruction').split('Reference clock:')[0], avatar.pop('system_instruction').split('Reference clock:')[0])
        self.assertEqual(voice, avatar)

    def test_voice_retains_existing_client(self):
        with patch.object(server, '_client', return_value='existing') as client:
            self.assertEqual(server._live_client(False), 'existing')
            client.assert_called_once()

    def test_avatar_client_is_separate_and_uses_adc(self):
        with patch.dict(os.environ, {'FNOL_AVATAR_PROJECT': 'test-project', 'FNOL_AVATAR_LOCATION': 'us-central1'}), patch.object(server, 'AVATAR_CLIENT', None), patch('google.genai.Client') as client, patch.object(server, '_client') as voice:
            server._live_client(True)
            client.assert_called_once_with(vertexai=True, project='test-project', location='us-central1')
            voice.assert_not_called()

    def test_health_does_not_advertise_partial_configuration(self):
        with patch.dict(os.environ, {'FNOL_AVATAR_PROJECT': '', 'FNOL_AVATAR_NAME': 'Ben'}):
            self.assertFalse(server.health()['avatar']['enabled'])

    def test_custom_portrait_and_matched_voice_are_sent(self):
        config = build_live_config(avatar_name='Ben', avatar_image=b'portrait', avatar_voice='Charon')
        self.assertIsNone(config.avatar_config.avatar_name)
        self.assertEqual(config.avatar_config.customized_avatar.image_data, b'portrait')
        self.assertEqual(config.speech_config.voice_config.prebuilt_voice_config.voice_name, 'Charon')

    def test_video_cannot_reach_pcm_playback(self):
        for mime, kind in [('video/mp4', 'avatar_video'), ('audio/pcm;rate=24000', 'audio')]:
            message = server.live_media_message(SimpleNamespace(data=b'test', mime_type=mime))
            self.assertEqual(message['type'], kind)
            self.assertEqual(message['mime_type'], mime)
        self.assertIsNone(server.live_media_message(SimpleNamespace(data=b'test', mime_type='image/jpeg')))

    def test_custom_reference_is_loaded_from_configured_path(self):
        # A generated RGB PNG keeps this test independent of any demo portrait.
        def chunk(kind, data):
            return (struct.pack('>I', len(data)) + kind + data
                    + struct.pack('>I', zlib.crc32(kind + data)))

        width, height = 704, 1280
        png = b'\x89PNG\r\n\x1a\n'
        png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
        png += chunk(b'IDAT', zlib.compress(bytes((width * 3 + 1) * height)))
        png += chunk(b'IEND', b'')
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / 'reference.png'
            reference.write_bytes(png)
            with patch.dict(os.environ, {'FNOL_AVATAR_IMAGE': str(reference)}):
                path, data = server.avatar_reference()
            self.assertEqual(path, reference.resolve())
            self.assertEqual(data, png)


if __name__ == '__main__':
    unittest.main()
