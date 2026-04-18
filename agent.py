import torch
import torch.nn as nn
import torch.optim as optim
import random
import json
import os
import chess
from environment import ChessEnv

class DQN(nn.Module):
    def __init__(self):
        super(DQN, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(12, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Flatten()
        )
        self.fc = nn.Sequential(
            nn.Linear(128 * 8 * 8, 512),
            nn.ReLU(),
            nn.Linear(512, 1) # Outputs a single value for the board state
        )

    def forward(self, x):
        return self.fc(self.conv(x))

class ChessAgent:
    def __init__(self, color=chess.BLACK):
        self.color = color
        self.model = DQN()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        self.epsilon = 0.3 # Exploration rate
        self.gamma = 0.99
        self.memory = []
        self.load_model()

    def choose_action(self, board, env):
        legal_moves = list(board.legal_moves)
        if random.random() < self.epsilon:
            return random.choice(legal_moves)

        best_move = None
        best_value = -float('inf') if self.color == chess.WHITE else float('inf')

        # Evaluate post-move states
        for move in legal_moves:
            board.push(move)
            state_tensor = env.get_state()
            with torch.no_grad():
                value = self.model(state_tensor).item()
            board.pop()

            if self.color == chess.WHITE and value > best_value:
                best_value = value
                best_move = move
            elif self.color == chess.BLACK and value < best_value: # Black wants negative value
                best_value = value
                best_move = move

        return best_move if best_move else random.choice(legal_moves)

    def save_experience(self, fen, move_uci, reward, next_fen, done):
        self.memory.append({
            "fen": fen, "move": move_uci, "reward": reward, 
            "next_fen": next_fen, "done": done
        })

    def save_buffer_to_disk(self):
        with open('replay_buffer.json', 'w') as f:
            json.dump(self.memory, f)

    def load_buffer_from_disk(self):
        if os.path.exists('replay_buffer.json'):
            with open('replay_buffer.json', 'r') as f:
                self.memory = json.load(f)

    def offline_train(self, batch_size=32):
        self.load_buffer_from_disk()
        if len(self.memory) < batch_size: return

        batch = random.sample(self.memory, batch_size)
        env = ChessEnv()
        
        for exp in batch:
            env.board.set_fen(exp['fen'])
            state = env.get_state()
            env.board.set_fen(exp['next_fen'])
            next_state = env.get_state()

            target = exp['reward']
            if not exp['done']:
                with torch.no_grad():
                    target += self.gamma * self.model(next_state).item()

            prediction = self.model(state)
            loss = self.criterion(prediction, torch.tensor([[target]], dtype=torch.float32))

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        self.save_model()

    def save_model(self):
        torch.save(self.model.state_dict(), 'dqn_model.pth')

    def load_model(self):
        if os.path.exists('dqn_model.pth'):
            self.model.load_state_dict(torch.load('dqn_model.pth'))