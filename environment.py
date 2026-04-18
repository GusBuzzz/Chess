import chess
import numpy as np
import torch

class ChessEnv:
    def __init__(self):
        self.board = chess.Board()

    def reset(self):
        self.board.reset()
        return self.get_state()

    def get_state(self):
        """Converts the board into a 12x8x8 PyTorch tensor."""
        state = np.zeros((12, 8, 8), dtype=np.float32)
        piece_map = self.board.piece_map()
        
        for square, piece in piece_map.items():
            row = chess.square_rank(square)
            col = chess.square_file(square)
            # 0-5 for White (P, N, B, R, Q, K), 6-11 for Black
            channel = piece.piece_type - 1
            if not piece.color:  # Black
                channel += 6
            state[channel][row][col] = 1.0
            
        return torch.tensor(state).unsqueeze(0) # Add batch dimension

    def step(self, move):
        """Executes a move, returns next state, reward, and done flag."""
        self.board.push(move)
        done = self.board.is_game_over()
        reward = self.get_reward()
        return self.get_state(), reward, done

    def get_reward(self):
        """Calculates material advantage or checkmate reward."""
        if self.board.is_checkmate():
            return 1000 if not self.board.turn else -1000 # If it's black's turn and checkmate, white won
        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0
            
        # Basic material evaluation
        piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
        reward = 0
        for square, piece in self.board.piece_map().items():
            val = piece_values[piece.piece_type]
            reward += val if piece.color == chess.WHITE else -val
            
        return reward