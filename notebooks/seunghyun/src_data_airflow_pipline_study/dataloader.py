import math

import numpy as np


class SimpleDataLoader:
    """
    배치 단위로 데이터를 반복 처리하기 위한 클래스
    """

    def __init__(self, features, labels, batch_size=32, shuffle=True):
        self.features = np.array(features)
        self.labels = np.array(labels)
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_samples = len(self.features)
        self.indices = np.arange(self.num_samples)

    def __iter__(self):
        if self.shuffle:
            np.random.shuffle(self.indices)
        self.current_idx = 0
        return self

    def __next__(self):
        if self.current_idx >= self.num_samples:
            raise StopIteration

        start_idx = self.current_idx
        end_idx = start_idx + self.batch_size
        self.current_idx = end_idx

        batch_indices = self.indices[start_idx:end_idx]
        return self.features[batch_indices], self.labels[batch_indices]

    def __len__(self):
        return math.ceil(self.num_samples / self.batch_size)


# 테스트용 코드
if __name__ == "__main__":
    # 샘플 데이터 생성
    X = np.arange(100).reshape((50, 2))  # 50개 샘플, 2차원 feature
    y = np.arange(50)  # 50개 라벨

    loader = SimpleDataLoader(X, y, batch_size=10)

    print(f"총 배치 수: {len(loader)}")
    for batch_x, batch_y in loader:
        print("▶️ X:", batch_x)
        print("✅ y:", batch_y)
        break
