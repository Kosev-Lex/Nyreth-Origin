import os
import json
from typing import List

class MorphInterpolator:
    def __init__(self, output_dir: str = "morph_sequences"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save_sequence(self, start_tensor: List[float], end_tensor: List[float], steps: int = 10):
        filename = f"{self.tensor_id(start_tensor)}_TO_{self.tensor_id(end_tensor)}.json"
        path = os.path.join(self.output_dir, filename)

        sequence = self.interpolate(start_tensor, end_tensor, steps)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(sequence, f, indent=4)
        return path

    def batch_save(self, tensor_pairs: List[tuple], steps: int = 10):
        for start, end in tensor_pairs:
            self.save_sequence(start, end, steps)

    def interpolate(self, start: List[float], end: List[float], steps: int) -> List[List[float]]:
        sequence = []
        for i in range(steps):
            interpolated = [
                start[j] + (end[j] - start[j]) * (i / (steps - 1)) for j in range(len(start))
            ]
            sequence.append([round(val, 6) for val in interpolated])
        return sequence

    def tensor_id(self, tensor: List[float]) -> str:
        return "_".join([f"{x:.2f}" for x in tensor])
