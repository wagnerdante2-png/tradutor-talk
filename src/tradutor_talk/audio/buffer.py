from collections import deque


class AudioRingBuffer:
    def __init__(self, max_chunks: int = 25) -> None:
        if max_chunks < 1:
            raise ValueError("max_chunks must be >= 1")
        self._chunks: deque[bytes] = deque(maxlen=max_chunks)

    def push(self, chunk: bytes) -> None:
        if chunk:
            self._chunks.append(bytes(chunk))

    def snapshot(self) -> bytes:
        return b"".join(self._chunks)

    def clear(self) -> None:
        self._chunks.clear()

    def __len__(self) -> int:
        return len(self._chunks)
