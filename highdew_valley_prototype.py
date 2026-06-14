#!/usr/bin/env python3
"""
Highdew Valley - Basic Playable Prototype
Stardew Valley inspired cannabis farming game prototype.
Run with: python3 highdew_valley_prototype.py
Requires: pygame (already installed in this env)

Controls:
- Arrow keys or WASD: Move player
- SPACE or ENTER: Interact with plot under player (till/water/harvest depending on tool)
- 1-4: Switch tools (1: Hoe/Till, 2: Water, 3: Plant, 4: Harvest)
- P: Open/Close Shop (buy seeds)
- T: Talk to nearby NPC (simple dialogue)
- N: Advance to next day (growth happens, plants watered status resets)
- ESC: Quit
- Mouse: Alternative for some interactions (click plots)

Core loop implemented: Farming (till, plant different strains, water, grow over days, harvest), basic economy, one NPC interaction, day cycle.
This is a foundation prototype. Expand with Godot/Unity for full mobile game with all features from GDD.
"""

import pygame
import sys
import random
from collections import defaultdict

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 48
GRID_COLS = 8
GRID_ROWS = 6
FPS = 60

# Colors (earthy, green theme)
GREEN_DARK = (34, 85, 51)
GREEN_LIGHT = (76, 153, 76)
BROWN_SOIL = (139, 90, 43)
BROWN_TILLED = (160, 110, 60)
WATER_BLUE = (100, 149, 237)
SKY = (135, 206, 235)
UI_BG = (40, 60, 40)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
PLANT_COLORS = {
    'seedling': (144, 238, 144),
    'veg': (34, 139, 34),
    'flower': (186, 85, 211),  # Purple for buds
    'ready': (75, 0, 130)     # Indigo ready
}

# Strains data (simplified from GDD)
STRAINS = [
    {"name": "Blue Dream", "grow_days": 5, "yield": 3, "price": 80, "season": "Spring/Summer", "effect": "Balanced, creative"},
    {"name": "Sour Diesel", "grow_days": 4, "yield": 2, "price": 95, "season": "Spring", "effect": "Energizing, focus"},
    {"name": "OG Kush", "grow_days": 6, "yield": 4, "price": 110, "season": "Summer/Fall", "effect": "Deep relaxation"},
    {"name": "Northern Lights", "grow_days": 5, "yield": 3, "price": 85, "season": "Fall", "effect": "Classic relaxing"},
]

class Plant:
    def __init__(self, strain_idx):
        self.strain_idx = strain_idx
        self.strain = STRAINS[strain_idx]
        self.stage = 0  # 0: seedling, 1: veg, 2: flower, 3: ready
        self.days_grown = 0
        self.watered = False
        self.max_stage = 3

    def grow(self):
        if self.watered and self.stage < self.max_stage:
            self.days_grown += 1
            if self.days_grown >= self.strain["grow_days"] // (self.max_stage + 1):
                self.stage += 1
                self.days_grown = 0
        self.watered = False  # Reset daily

    def get_color(self):
        if self.stage == 0:
            return PLANT_COLORS['seedling']
        elif self.stage == 1:
            return PLANT_COLORS['veg']
        elif self.stage == 2:
            return PLANT_COLORS['flower']
        else:
            return PLANT_COLORS['ready']

    def is_ready(self):
        return self.stage == self.max_stage

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Highdew Valley - Prototype")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18)
        self.big_font = pygame.font.SysFont("arial", 24)
        self.small_font = pygame.font.SysFont("arial", 14)

        # Farm grid: None or Plant instance
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        
        # Player position (tile coords)
        self.player_x = 3
        self.player_y = 3
        
        # Current tool: 0=Hoe, 1=Water, 2=Plant, 3=Harvest
        self.current_tool = 0
        self.tool_names = ["Hoe (Till)", "Watering Can", "Plant Strain", "Harvest"]
        
        # Selected strain for planting (index in STRAINS)
        self.selected_strain = 0
        
        # Resources
        self.gold = 500
        self.day = 1
        self.season = "Spring"
        
        # Inventory: harvested buds {strain_name: count}
        self.inventory = defaultdict(int)
        
        # Simple NPC position and dialogue
        self.npc_x = 6
        self.npc_y = 1
        self.npc_name = "Flora Bloom"
        self.npc_dialogues = [
            "Welcome to Highdew Valley! Your uncle was a legend here.",
            "Plant some Blue Dream in spring for balanced vibes.",
            "Remember to water daily and watch those stages!",
            "Come talk to me at the Strain Sanctuary for seeds and advice.",
            "The community is excited to see what you grow."
        ]
        self.current_dialogue = 0
        self.show_dialogue = False
        
        # Shop open flag
        self.shop_open = False
        
        # Messages
        self.message = ""
        self.message_timer = 0

    def draw_grid(self):
        start_x = 50
        start_y = 80
        
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = start_x + col * TILE_SIZE
                y = start_y + row * TILE_SIZE
                
                # Soil base
                pygame.draw.rect(self.screen, BROWN_SOIL, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(self.screen, GREEN_DARK, (x, y, TILE_SIZE, TILE_SIZE), 2)
                
                # Tilled or plant
                plant = self.grid[row][col]
                if plant:
                    # Draw plant stages as simple shapes
                    color = plant.get_color()
                    center_x = x + TILE_SIZE // 2
                    center_y = y + TILE_SIZE // 2
                    
                    if plant.stage == 0:  # Seedling - small circle
                        pygame.draw.circle(self.screen, color, (center_x, center_y), 8)
                    elif plant.stage == 1:  # Veg - bigger green
                        pygame.draw.rect(self.screen, color, (center_x-12, center_y-8, 24, 16))
                    elif plant.stage == 2:  # Flower - purple-ish
                        pygame.draw.polygon(self.screen, color, [
                            (center_x, center_y-12), (center_x-10, center_y+8), (center_x+10, center_y+8)
                        ])
                    else:  # Ready - full bud
                        pygame.draw.circle(self.screen, color, (center_x, center_y), 14)
                        pygame.draw.circle(self.screen, (255, 255, 200), (center_x, center_y), 6)  # "trichomes"
                    
                    # Watered indicator
                    if plant.watered:
                        pygame.draw.circle(self.screen, WATER_BLUE, (x + TILE_SIZE - 8, y + 8), 5)
                else:
                    # Untilled looks drier
                    pass

    def draw_player(self):
        start_x = 50
        start_y = 80
        px = start_x + self.player_x * TILE_SIZE + TILE_SIZE // 2
        py = start_y + self.player_y * TILE_SIZE + TILE_SIZE // 2
        
        # Simple player sprite (green shirt, brown pants)
        pygame.draw.rect(self.screen, (70, 130, 70), (px - 12, py - 20, 24, 30))  # Body
        pygame.draw.circle(self.screen, (255, 220, 185), (px, py - 28), 10)  # Head
        pygame.draw.rect(self.screen, (101, 67, 33), (px - 10, py + 10, 20, 15))  # Pants

    def draw_npc(self):
        start_x = 50
        start_y = 80
        nx = start_x + self.npc_x * TILE_SIZE + TILE_SIZE // 2
        ny = start_y + self.npc_y * TILE_SIZE + TILE_SIZE // 2
        
        # Simple NPC (green hair vibe for Flora)
        pygame.draw.rect(self.screen, (50, 120, 50), (nx - 10, ny - 18, 20, 28))  # Body green
        pygame.draw.circle(self.screen, (255, 220, 185), (nx, ny - 26), 9)  # Head
        # Green hair hint
        pygame.draw.arc(self.screen, (34, 139, 34), (nx-10, ny-38, 20, 16), 0, 3.14, 3)

    def draw_ui(self):
        # Top bar
        pygame.draw.rect(self.screen, UI_BG, (0, 0, SCREEN_WIDTH, 70))
        
        # Day/Season/Gold
        day_text = self.font.render(f"Day {self.day} - {self.season}", True, WHITE)
        self.screen.blit(day_text, (20, 10))
        
        gold_text = self.font.render(f"Gold: ${self.gold}", True, GOLD)
        self.screen.blit(gold_text, (20, 35))
        
        # Tool
        tool_text = self.font.render(f"Tool: {self.tool_names[self.current_tool]}", True, WHITE)
        self.screen.blit(tool_text, (250, 10))
        
        if self.current_tool == 2:  # Planting
            strain_text = self.small_font.render(f"Strain: {STRAINS[self.selected_strain]['name']}", True, (200, 255, 200))
            self.screen.blit(strain_text, (250, 35))
        
        # Inventory summary
        inv_text = self.small_font.render("Inventory: " + " | ".join([f"{k[:8]}: {v}" for k,v in list(self.inventory.items())[:3]]), True, WHITE)
        self.screen.blit(inv_text, (450, 10))
        
        # Message
        if self.message and self.message_timer > 0:
            msg_surf = self.font.render(self.message, True, (255, 255, 150))
            self.screen.blit(msg_surf, (20, 55))
        
        # Bottom help
        help_text = self.small_font.render("1-4:Tools | SPACE:Interact | N:Next Day | P:Shop | T:Talk to Flora | ESC:Quit", True, (180, 200, 180))
        self.screen.blit(help_text, (20, SCREEN_HEIGHT - 25))

    def draw_shop(self):
        if not self.shop_open:
            return
        
        # Shop overlay
        shop_rect = pygame.Rect(150, 100, 500, 350)
        pygame.draw.rect(self.screen, (30, 50, 30), shop_rect)
        pygame.draw.rect(self.screen, GREEN_LIGHT, shop_rect, 3)
        
        title = self.big_font.render("Strain Sanctuary - Buy Seeds", True, WHITE)
        self.screen.blit(title, (170, 115))
        
        y_pos = 160
        for i, strain in enumerate(STRAINS):
            price = strain["price"] // 2  # Seed price cheaper
            text = f"{i+1}. {strain['name']} ({strain['season']}) - ${price} | Yield: {strain['yield']} | {strain['effect']}"
            color = (255, 255, 255) if i == self.selected_strain else (200, 220, 200)
            surf = self.small_font.render(text, True, color)
            self.screen.blit(surf, (170, y_pos))
            y_pos += 28
        
        instr = self.small_font.render("Press 1-4 to select strain | ENTER to buy 5 seeds | P to close", True, (255, 220, 150))
        self.screen.blit(instr, (170, 400))

    def draw_dialogue(self):
        if not self.show_dialogue:
            return
        
        # Dialogue box
        box_rect = pygame.Rect(50, 420, 700, 120)
        pygame.draw.rect(self.screen, (20, 40, 20), box_rect)
        pygame.draw.rect(self.screen, GREEN_LIGHT, box_rect, 2)
        
        name_surf = self.font.render(self.npc_name, True, (255, 220, 100))
        self.screen.blit(name_surf, (70, 435))
        
        dialogue = self.npc_dialogues[self.current_dialogue % len(self.npc_dialogues)]
        # Word wrap simple
        words = dialogue.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self.font.size(test_line)[0] < 660:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        y = 460
        for line in lines[:4]:
            surf = self.small_font.render(line, True, WHITE)
            self.screen.blit(surf, (70, y))
            y += 20

    def set_message(self, msg, duration=120):
        self.message = msg
        self.message_timer = duration

    def interact(self):
        row, col = self.player_y, self.player_x
        plant = self.grid[row][col]
        
        if self.current_tool == 0:  # Hoe - Till
            if plant is None:
                # Till does nothing special in this simple version, but marks it ready
                self.set_message("Soil tilled. Ready for planting!")
            else:
                self.set_message("Already has a plant. Harvest first or use harvest tool.")
        
        elif self.current_tool == 1:  # Water
            if plant:
                if not plant.watered:
                    plant.watered = True
                    self.set_message(f"Watered the {plant.strain['name']}. ")
                else:
                    self.set_message("Already watered today.")
            else:
                self.set_message("Nothing to water here. Plant something first!")
        
        elif self.current_tool == 2:  # Plant
            if plant is None:
                cost = STRAINS[self.selected_strain]["price"] // 4  # Seed cost
                if self.gold >= cost:
                    self.gold -= cost
                    self.grid[row][col] = Plant(self.selected_strain)
                    self.set_message(f"Planted {STRAINS[self.selected_strain]['name']}! ")
                else:
                    self.set_message("Not enough gold for seeds!")
            else:
                self.set_message("Plot occupied. Harvest or clear first.")
        
        elif self.current_tool == 3:  # Harvest
            if plant and plant.is_ready():
                strain_name = plant.strain["name"]
                yield_amt = plant.strain["yield"]
                self.inventory[strain_name] += yield_amt
                sell_value = plant.strain["price"] * yield_amt
                self.gold += sell_value
                self.grid[row][col] = None
                self.set_message(f"Harvested {yield_amt}x {strain_name}! Sold for ${sell_value}.")
            elif plant:
                self.set_message(f"Not ready yet. Stage {plant.stage}/3. Needs more days/water.")
            else:
                self.set_message("Nothing to harvest here.")

    def advance_day(self):
        self.day += 1
        if self.day > 28:
            self.day = 1
            # Simple season cycle
            seasons = ["Spring", "Summer", "Fall", "Winter"]
            idx = seasons.index(self.season)
            self.season = seasons[(idx + 1) % 4]
        
        # Grow all plants
        for row in self.grid:
            for plant in row:
                if plant:
                    plant.grow()
        
        self.set_message(f"Day {self.day} begins! Plants have grown.")
        
        # Random event chance (simple)
        if random.random() < 0.15:
            self.set_message("A gentle rain helped the valley today!")

    def buy_seeds(self, strain_idx):
        strain = STRAINS[strain_idx]
        cost = strain["price"] // 2 * 5  # 5 seeds
        if self.gold >= cost:
            self.gold -= cost
            # In this prototype, buying just selects and gives "seeds" implicitly (unlimited plant attempts for demo)
            self.selected_strain = strain_idx
            self.set_message(f"Bought 5 {strain['name']} seeds! Now use Plant tool.")
        else:
            self.set_message("Not enough gold!")

    def talk_to_npc(self):
        # Check proximity (simple Manhattan distance)
        dist = abs(self.player_x - self.npc_x) + abs(self.player_y - self.npc_y)
        if dist <= 2:
            self.show_dialogue = not self.show_dialogue
            if self.show_dialogue:
                self.current_dialogue = (self.current_dialogue + 1) % len(self.npc_dialogues)
        else:
            self.set_message("Get closer to Flora to talk!")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                # Movement
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.player_x = max(0, self.player_x - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.player_x = min(GRID_COLS - 1, self.player_x + 1)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.player_y = max(0, self.player_y - 1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.player_y = min(GRID_ROWS - 1, self.player_y + 1)
                
                # Tools
                elif event.key == pygame.K_1:
                    self.current_tool = 0
                elif event.key == pygame.K_2:
                    self.current_tool = 1
                elif event.key == pygame.K_3:
                    self.current_tool = 2
                elif event.key == pygame.K_4:
                    self.current_tool = 3
                
                # Cycle strains with Q/E when planting tool selected
                elif event.key == pygame.K_q and self.current_tool == 2:
                    self.selected_strain = (self.selected_strain - 1) % len(STRAINS)
                elif event.key == pygame.K_e and self.current_tool == 2:
                    self.selected_strain = (self.selected_strain + 1) % len(STRAINS)
                
                # Interact
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.shop_open:
                        self.buy_seeds(self.selected_strain)
                    elif self.show_dialogue:
                        self.show_dialogue = False
                    else:
                        self.interact()
                
                # Advance day
                elif event.key == pygame.K_n:
                    self.advance_day()
                    self.show_dialogue = False
                
                # Shop
                elif event.key == pygame.K_p:
                    self.shop_open = not self.shop_open
                    self.show_dialogue = False
                
                # Talk
                elif event.key == pygame.K_t:
                    self.talk_to_npc()
            
            # Mouse support for clicking plots (simple)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                start_x, start_y = 50, 80
                if start_x <= mx < start_x + GRID_COLS * TILE_SIZE and start_y <= my < start_y + GRID_ROWS * TILE_SIZE:
                    col = (mx - start_x) // TILE_SIZE
                    row = (my - start_y) // TILE_SIZE
                    self.player_x = col
                    self.player_y = row
                    self.interact()  # Auto interact on click
        
        return True

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
        else:
            self.message = ""

    def draw(self):
        self.screen.fill(SKY)
        
        # Simple background grass hint
        pygame.draw.rect(self.screen, GREEN_DARK, (40, 70, GRID_COLS * TILE_SIZE + 20, GRID_ROWS * TILE_SIZE + 20))
        
        self.draw_grid()
        self.draw_player()
        self.draw_npc()
        self.draw_ui()
        self.draw_shop()
        self.draw_dialogue()
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        print("Thanks for playing the Highdew Valley prototype!")
        print("This demonstrates the core farming loop. Expand it into a full game using the GDD!")

if __name__ == "__main__":
    game = Game()
    game.run()