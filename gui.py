import pygame
import chess
import os

# Layout Constants
LEFT_PANEL_W, BOARD_W, RIGHT_PANEL_W = 200, 600, 250
SQ_SIZE = BOARD_W // 8
WIDTH = LEFT_PANEL_W + BOARD_W + RIGHT_PANEL_W
HEIGHT = 600

# Colors
COLORS = {
    "light": (240, 217, 181), "dark": (181, 136, 99),
    "bg": (40, 40, 40), "text": (255, 255, 255), "highlight": (205, 210, 106, 150)
}

# Mapping chess piece symbols to your new asset names
PIECE_NAMES = {
    "P": "pawn", "N": "knight", "B": "bishop", 
    "R": "rook", "Q": "queen", "K": "king"
}

class ChessGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RL Chess Engine")
        self.font = pygame.font.SysFont("Consolas", 18)
        self.pieces = self.load_assets()
        
        # Drag and Drop State
        self.dragging = False
        self.selected_square = None
        self.mouse_pos = (0, 0)
        self.last_move = None

    def load_assets(self):
        pieces = {}
        names = [
            "black-pawn",
            "black-knight",
            "black-bishop",
            "black-rook",
            "black-queen",
            "black-king",
            "white-pawn",
            "white-knight",
            "white-bishop",
            "white-rook",
            "white-queen",
            "white-king"
        ]
        for name in names:
            try:
                img = pygame.image.load(os.path.join('assets', f'{name}.png'))
                pieces[name] = pygame.transform.scale(img, (SQ_SIZE, SQ_SIZE))
            except:
                pass # Fail silently if no assets, will draw empty board
        return pieces

    def get_piece_key(self, piece):
        """Helper to convert python-chess piece to your asset dictionary key."""
        color_str = "white" if piece.color == chess.WHITE else "black"
        type_str = PIECE_NAMES[piece.symbol().upper()]
        return f"{color_str}-{type_str}"

    def draw_board(self, board):
        for r in range(8):
            for c in range(8):
                color = COLORS["light"] if (r + c) % 2 == 0 else COLORS["dark"]
                rect = pygame.Rect(LEFT_PANEL_W + c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                pygame.draw.rect(self.screen, color, rect)

                # Highlight last move
                sq = chess.square(c, 7 - r)
                if self.last_move and (sq == self.last_move.from_square or sq == self.last_move.to_square):
                    s = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                    s.fill(COLORS["highlight"])
                    self.screen.blit(s, rect)

                # Draw Piece (skip if dragging)
                if self.selected_square != sq:
                    piece = board.piece_at(sq)
                    if piece and self.pieces:
                        p_name = self.get_piece_key(piece)
                        if p_name in self.pieces:
                            self.screen.blit(self.pieces[p_name], rect)

    def draw_panels(self, board, move_history):
        # Backgrounds
        pygame.draw.rect(self.screen, COLORS["bg"], (0, 0, LEFT_PANEL_W, HEIGHT))
        pygame.draw.rect(self.screen, COLORS["bg"], (LEFT_PANEL_W + BOARD_W, 0, RIGHT_PANEL_W, HEIGHT))
        
        # Left Panel (Captured - Simplified placeholder logic)
        cap_text = self.font.render("Captured:", True, COLORS["text"])
        self.screen.blit(cap_text, (10, 10))
        
        # Right Panel (History)
        hist_text = self.font.render("Move History:", True, COLORS["text"])
        self.screen.blit(hist_text, (LEFT_PANEL_W + BOARD_W + 10, 10))
        
        y_offset = 40
        for i, move in enumerate(move_history[-20:]): # Show last 20 half-moves
            m_text = self.font.render(f"{i//2 + 1}. {move}" if i%2==0 else move, True, COLORS["text"])
            self.screen.blit(m_text, (LEFT_PANEL_W + BOARD_W + 10 + (80 if i%2!=0 else 0), y_offset))
            if i % 2 != 0: y_offset += 25

    def draw_drag(self, board):
        if self.dragging and self.selected_square is not None:
            piece = board.piece_at(self.selected_square)
            if piece and self.pieces:
                p_name = self.get_piece_key(piece)
                if p_name in self.pieces:
                    x, y = self.mouse_pos
                    self.screen.blit(self.pieces[p_name], (x - SQ_SIZE//2, y - SQ_SIZE//2))

    def update(self, board, move_history):
        self.screen.fill((0, 0, 0))
        self.draw_panels(board, move_history)
        self.draw_board(board)
        self.draw_drag(board)
        pygame.display.flip()