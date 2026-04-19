import os
from src.decode.isaac64 import Isaac64
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VideoDecoder:
    def __init__(self):
        self.isaac64 = Isaac64()

    def decrypt(self, encrypted_path, decode_key, output_path):
        logger.info(f"Decrypting video: {encrypted_path}")
        keystream = self.isaac64.generate_keystream(int(decode_key))
        logger.info(f"Generated keystream: {len(keystream)} bytes")
        with open(encrypted_path, 'rb') as f:
            data = f.read()
        logger.info(f"Read encrypted file: {len(data)} bytes")
        decrypted_data = bytearray(data)
        decrypt_len = min(131072, len(data))
        for i in range(decrypt_len):
            decrypted_data[i] = data[i] ^ keystream[i]
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        self._verify_decryption(output_path)
        logger.info(f"Decryption completed: {output_path}")
        return output_path

    def _verify_decryption(self, file_path):
        with open(file_path, 'rb') as f:
            header = f.read(32)
        if b'ftyp' in header:
            logger.info("Decryption verified: ftyp signature found")
        else:
            logger.warning("Warning: ftyp signature not found, decryption may have failed")
