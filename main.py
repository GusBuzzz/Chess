import pygame
import sys
import json
import os
import chess
from environment import ChessEnv
from agent import ChessAgent
from gui import ChessGUI, LEFT_PANEL_W, BOARD_W, SQ_SIZE

class GameManager:
    def __init__(self):
        self.gui = ChessGUI()
        self.env = ChessEnv()
        self.agent = ChessAgent(color=chess.BLACK)
        self.mode = "PvC" # "PvP" or "PvC"
        self.move_history = []
        self.clock = pygame.time.Clock()

    def save_game(self):
        data = {
            "fen": self.env.board.fen(),
            "mode": self.mode,
            "history": self.move_history
        }
        with open('savegame.json', 'w') as f:
            json.dump(data, f)
        print("Game Saved.")

    def load_game(self):
        if os.path.exists('savegame.json'):
            with open('savegame.json', 'r') as f:
                data = json.load(f)
                self.env.board.set_fen(data["fen"])
                self.mode = data["mode"]
                self.move_history = data["history"]
            print("Game Loaded.")
        else:
            print("No save game found.")

    def menu(self):
        font = pygame.font.SysFont("Consolas", 30)
        while True:
            self.gui.screen.fill((40, 40, 40))
            opts = ["1. Player vs Player", "2. Player vs Computer", "3. Load Game", "4. Offline Train AI"]
            for i, opt in enumerate(opts):
                txt = font.render(opt, True, (255, 255, 255))
                self.gui.screen.blit(txt, (200, 150 + i * 50))
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.mode = "PvP"
                        self.play()
                    elif event.key == pygame.K_2:
                        self.mode = "PvC"
                        self.play()
                    elif event.key == pygame.K_3:
                        self.load_game()
                        self.play()
                    elif event.key == pygame.K_4:
                        print("Training offline on past experiences...")
                        self.agent.offline_train(batch_size=64)
                        print("Training complete. Model saved.")

    def get_square_from_mouse(self, pos):
        x, y = pos
        if LEFT_PANEL_W <= x <= LEFT_PANEL_W + BOARD_W:
            col = (x - LEFT_PANEL_W) // SQ_SIZE
            row = y // SQ_SIZE
            return chess.square(col, 7 - row)
        return None

    def play(self):
        running = True
        while running and not self.env.board.is_game_over():
            self.gui.update(self.env.board, self.move_history)
            self.gui.mouse_pos = pygame.mouse.get_pos()

            # AI Turn handling
            if self.mode == "PvC" and self.env.board.turn == self.agent.color:
                pre_fen = self.env.board.fen()
                action = self.agent.choose_action(self.env.board, self.env)
                san_move = self.env.board.san(action)
                
                # Execute and gather reward
                next_state, reward, done = self.env.step(action)
                self.move_history.append(san_move)
                self.gui.last_move = action
                
                # Save to experience replay
                self.agent.save_experience(pre_fen, action.uci(), reward, self.env.board.fen(), done)

            # Event Handling (Human turns & Commands)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.agent.save_buffer_to_disk() # Save buffer on exit
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        self.save_game()
                    if event.key == pygame.K_ESCAPE:
                        running = False # Return to menu

                # Drag and Drop Logic
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        sq = self.get_square_from_mouse(event.pos)
                        if sq is not None and self.env.board.piece_at(sq):
                            if self.env.board.color_at(sq) == self.env.board.turn:
                                self.gui.selected_square = sq
                                self.gui.dragging = True

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.gui.dragging:
                        target_sq = self.get_square_from_mouse(event.pos)
                        if target_sq is not None:
                            # Auto-promote to Queen for simplicity in this GUI
                            move = chess.Move(self.gui.selected_square, target_sq)
                            if move not in self.env.board.legal_moves:
                                move = chess.Move(self.gui.selected_square, target_sq, promotion=chess.QUEEN)
                            
                            if move in self.env.board.legal_moves:
                                san_move = self.env.board.san(move)
                                self.env.board.push(move)
                                self.move_history.append(san_move)
                                self.gui.last_move = move

                        self.gui.dragging = False
                        self.gui.selected_square = None

            self.clock.tick(60)
        
        # End of Game Wrap-up
        if self.env.board.is_game_over():
            self.agent.save_buffer_to_disk()
            print("Game Over:", self.env.board.result())

if __name__ == "__main__":
    game = GameManager()
    game.menu()