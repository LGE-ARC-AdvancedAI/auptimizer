import torch.nn as nn
import torch.nn.functional as F


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, 3)  # 222*222*16
        self.conv2 = nn.Conv2d(16, 64, 3)  # 42*42*64
        self.fc = nn.Linear(42 * 42 * 64, 10)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.conv1(x)), 5)
        x = F.relu(self.conv2(x))
        x = x.view(-1, 42 * 42 * 64)
        x = F.softmax(self.fc(x), dim=1)
        return x

