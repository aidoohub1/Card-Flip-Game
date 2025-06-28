import flet as ft
import random
import time
import asyncio

class CardFlipGame:
    def __init__(self, difficulty="Medium"):
        self.difficulty = difficulty
        self.settings = self.configure_settings(difficulty)
        self.cards = []
        self.card_buttons = []
        self.flipped_cards = []
        self.matched_pairs = 0
        self.moves = 0
        self.game_started = False
        self.game_over = False
        self.page = None
        self.moves_text = None
        self.status_text = None
        self.timer_text = None
        self.start_time = None
        self.timer_running = False

    def configure_settings(self, difficulty):
        # Define settings based on difficulty
        return {
            "Easy": {"level": 1, "speed": 1.0, "grid_size": 4, "pairs": 8, "preview_time": 3.0},
            "Medium": {"level": 2, "speed": 1.5, "grid_size": 4, "pairs": 8, "preview_time": 2.0},
            "Hard": {"level": 3, "speed": 2.0, "grid_size": 6, "pairs": 18, "preview_time": 1.0}
        }.get(difficulty, {"level": 2, "speed": 1.5, "grid_size": 4, "pairs": 8, "preview_time": 2.0})

    def build_game_ui(self, page: ft.Page):
        self.page = page
        page.title = "Card Flip Memory Game"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        
        # Game title
        title = ft.Text(
            "Card Flip Memory Game",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.PURPLE_700
        )
        
        # Difficulty display
        difficulty_info = ft.Text(
            f"Difficulty: {self.difficulty} | Grid: {self.settings['grid_size']}x{self.settings['grid_size']} | Pairs: {self.settings['pairs']}",
            size=16,
            color=ft.colors.GREY_700
        )
        
        # Game stats
        self.moves_text = ft.Text(
            "Moves: 0",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_700
        )
        
        self.timer_text = ft.Text(
            "Time: 00:00",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREEN_700
        )
        
        # Status text
        self.status_text = ft.Text(
            "Click 'Start Game' to begin!",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.ORANGE_700
        )
        
        # Game controls
        start_button = ft.ElevatedButton(
            "Start Game",
            on_click=self.start_game,
            bgcolor=ft.colors.GREEN_100,
            width=150
        )
        
        reset_button = ft.ElevatedButton(
            "Reset Game",
            on_click=self.reset_game,
            bgcolor=ft.colors.RED_100,
            width=150
        )
        
        # Create game board
        self.create_cards()
        self.create_board()
        
        # Layout
        stats_row = ft.Row([
            self.moves_text,
            self.timer_text
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        controls_row = ft.Row([
            start_button,
            reset_button
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        page.add(
            ft.Column([
                title,
                difficulty_info,
                stats_row,
                self.status_text,
                controls_row,
                ft.Container(
                    content=ft.Column(self.card_buttons),
                    bgcolor=ft.colors.BLUE_50,
                    padding=20,
                    border_radius=10,
                    alignment=ft.alignment.center
                )
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def create_cards(self):
        # Create pairs of cards with emojis
        card_symbols = ["🎯", "🎮", "🎪", "🎨", "🎭", "🎸", "🎺", "🎷", "🎹", "🎤", 
                       "🎧", "🎬", "🎥", "📷", "📺", "📻", "📱", "💻", "⌚", "🎲",
                       "♠️", "♥️", "♦️", "♣️", "🃏", "🎰", "🎳", "⚽", "🏀", "🏈"]
        
        # Select symbols based on number of pairs needed
        selected_symbols = card_symbols[:self.settings['pairs']]
        
        # Create pairs and shuffle
        self.cards = selected_symbols * 2
        random.shuffle(self.cards)

    def create_board(self):
        self.card_buttons = []
        grid_size = self.settings['grid_size']
        
        for row in range(grid_size):
            button_row = []
            for col in range(grid_size):
                if row * grid_size + col < len(self.cards):
                    button = ft.ElevatedButton(
                        "?",
                        width=80,
                        height=80,
                        bgcolor=ft.colors.BLUE_200,
                        color=ft.colors.WHITE,
                        style=ft.ButtonStyle(
                            text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)
                        ),
                        on_click=lambda e, r=row, c=col: self.flip_card(r, c),
                        disabled=True
                    )
                    button.data = {"row": row, "col": col, "flipped": False, "matched": False}
                    button_row.append(button)
                else:
                    # Empty space for non-square grids
                    button_row.append(ft.Container(width=80, height=80))
            
            self.card_buttons.append(ft.Row(button_row, alignment=ft.MainAxisAlignment.CENTER))

    async def start_game(self, e):
        if self.game_started:
            return
            
        self.game_started = True
        self.game_over = False
        self.matched_pairs = 0
        self.moves = 0
        self.flipped_cards = []
        
        # Enable all buttons
        for row in self.card_buttons:
            for button in row.controls:
                if hasattr(button, 'disabled'):
                    button.disabled = False
                    button.data["flipped"] = False
                    button.data["matched"] = False
        
        # Show preview of all cards
        self.status_text.value = f"Memorize the cards! ({self.settings['preview_time']} seconds)"
        self.status_text.color = ft.colors.ORANGE_700
        
        # Show all cards during preview
        self.show_all_cards()
        self.page.update()
        
        # Wait for preview time
        await asyncio.sleep(self.settings['preview_time'])
        
        # Hide all cards
        self.hide_all_cards()
        
        # Start the game
        self.status_text.value = "Find matching pairs!"
        self.status_text.color = ft.colors.BLUE_700
        self.start_timer()
        self.page.update()

    def show_all_cards(self):
        grid_size = self.settings['grid_size']
        for row in range(grid_size):
            for col in range(grid_size):
                if row * grid_size + col < len(self.cards):
                    button = self.card_buttons[row].controls[col]
                    card_index = row * grid_size + col
                    button.text = self.cards[card_index]
                    button.bgcolor = ft.colors.WHITE

    def hide_all_cards(self):
        grid_size = self.settings['grid_size']
        for row in range(grid_size):
            for col in range(grid_size):
                if row * grid_size + col < len(self.cards):
                    button = self.card_buttons[row].controls[col]
                    if not button.data["matched"]:
                        button.text = "?"
                        button.bgcolor = ft.colors.BLUE_200
                        button.data["flipped"] = False

    async def flip_card(self, row, col):
        if not self.game_started or self.game_over:
            return
            
        button = self.card_buttons[row].controls[col]
        
        # Can't flip if already flipped or matched
        if button.data["flipped"] or button.data["matched"]:
            return
            
        # Can't flip more than 2 cards at once
        if len(self.flipped_cards) >= 2:
            return
        
        # Flip the card
        card_index = row * self.settings['grid_size'] + col
        button.text = self.cards[card_index]
        button.bgcolor = ft.colors.WHITE
        button.data["flipped"] = True
        
        self.flipped_cards.append({"row": row, "col": col, "symbol": self.cards[card_index]})
        self.page.update()
        
        # Check if two cards are flipped
        if len(self.flipped_cards) == 2:
            self.moves += 1
            self.moves_text.value = f"Moves: {self.moves}"
            
            await asyncio.sleep(1.0)  # Show cards for a moment
            
            # Check for match
            if self.flipped_cards[0]["symbol"] == self.flipped_cards[1]["symbol"]:
                # Match found!
                self.handle_match()
            else:
                # No match - flip cards back
                self.handle_no_match()
            
            self.flipped_cards = []
            self.page.update()
            
            # Check if game is complete
            if self.matched_pairs == self.settings['pairs']:
                self.end_game()

    def handle_match(self):
        # Mark cards as matched
        for card_info in self.flipped_cards:
            button = self.card_buttons[card_info["row"]].controls[card_info["col"]]
            button.data["matched"] = True
            button.bgcolor = ft.colors.GREEN_200
            button.disabled = True
        
        self.matched_pairs += 1
        self.status_text.value = f"Match found! Pairs: {self.matched_pairs}/{self.settings['pairs']}"
        self.status_text.color = ft.colors.GREEN_700

    def handle_no_match(self):
        # Flip cards back
        for card_info in self.flipped_cards:
            button = self.card_buttons[card_info["row"]].controls[card_info["col"]]
            button.text = "?"
            button.bgcolor = ft.colors.BLUE_200
            button.data["flipped"] = False
        
        self.status_text.value = "No match. Try again!"
        self.status_text.color = ft.colors.RED_700

    def start_timer(self):
        self.start_time = time.time()
        self.timer_running = True
        asyncio.create_task(self.update_timer())

    async def update_timer(self):
        while self.timer_running and not self.game_over:
            if self.start_time:
                elapsed = int(time.time() - self.start_time)
                minutes = elapsed // 60
                seconds = elapsed % 60
                self.timer_text.value = f"Time: {minutes:02d}:{seconds:02d}"
                self.page.update()
            await asyncio.sleep(1)

    def end_game(self):
        self.game_over = True
        self.timer_running = False
        
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        minutes = elapsed // 60
        seconds = elapsed % 60
        
        self.status_text.value = f"🎉 Congratulations! Game completed in {self.moves} moves and {minutes:02d}:{seconds:02d}!"
        self.status_text.color = ft.colors.PURPLE_700
        
        # Calculate score based on difficulty, moves, and time
        base_score = 1000
        move_penalty = self.moves * 10
        time_penalty = elapsed * 2
        difficulty_bonus = self.settings['level'] * 100
        
        final_score = max(0, base_score - move_penalty - time_penalty + difficulty_bonus)
        
        # Add score display
        score_text = ft.Text(
            f"Final Score: {final_score}",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GOLD
        )
        
        # Insert score after status text
        column = self.page.controls[0]
        for i, control in enumerate(column.controls):
            if control == self.status_text:
                column.controls.insert(i + 1, score_text)
                break
        
        self.page.update()

    def reset_game(self, e):
        self.game_started = False
        self.game_over = False
        self.timer_running = False
        self.matched_pairs = 0
        self.moves = 0
        self.flipped_cards = []
        self.start_time = None
        
        # Reset UI
        self.moves_text.value = "Moves: 0"
        self.timer_text.value = "Time: 00:00"
        self.status_text.value = "Click 'Start Game' to begin!"
        self.status_text.color = ft.colors.ORANGE_700
        
        # Remove score text if it exists
        column = self.page.controls[0]
        column.controls = [c for c in column.controls if not (hasattr(c, 'value') and 'Final Score' in str(c.value))]
        
        # Create new cards and board
        self.create_cards()
        
        # Reset all buttons
        grid_size = self.settings['grid_size']
        for row in range(grid_size):
            for col in range(grid_size):
                if row * grid_size + col < len(self.cards):
                    button = self.card_buttons[row].controls[col]
                    button.text = "?"
                    button.bgcolor = ft.colors.BLUE_200
                    button.disabled = True
                    button.data = {"row": row, "col": col, "flipped": False, "matched": False}
        
        self.page.update()


def main(page: ft.Page, difficulty="Medium"):
    game = CardFlipGame(difficulty)
    game.build_game_ui(page)


# For testing purposes
if __name__ == "__main__":
    ft.app(target=main)