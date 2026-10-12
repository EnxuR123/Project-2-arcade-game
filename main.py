import pygame
import random
import math
import asyncio

async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    class Boss:
        def __init__ (self):
            self.health = 100
            self.position = (400, 300)
            self.spiral_angle = 0

        def take_damage(self, attack):
            self.health -= attack.damage

        def skill_1(self, player):
            boss_pos = pygame.Vector2(self.position)
            player_pos = pygame.Vector2(player.position)
            direction = (player_pos - boss_pos).normalize()
            for offset in [-30, -10, 10, 30]:
                perpendicular = pygame.Vector2(-direction.y, direction.x)
                spawn_pos = (
                    boss_pos
                    + direction * 35
                    + perpendicular * offset
                )

            self.bullets.append({
                "position": spawn_pos,
                "direction": direction.copy(),
                "speed": 3,
                "radius": 8,
                "health": 1,
                "damage": 10
            })

        def skill_2(self):
            now = pygame.time.get_ticks()
            elapsed = now - self.laser_start

            if elapsed < 2000:
                color = (255, 255, 0)  
                width = 3             
            elif elapsed < 2500:
                color = (255, 0, 0)   
                width = 10           
            else:
                self.laser_start = now
                self.laser_y = random.choice([150, 450])
                return

            pygame.draw.line(                
                color,                  
                (0, self.laser_y),      
                (800, self.laser_y),    
                width                   
            )

        def skill_3(self):
            angle = math.radians(self.spiral_angle)

            direction = pygame.Vector2(
                math.cos(angle),
                math.sin(angle)
            )

            self.bullets.append({
                "position": pygame.Vector2(self.position),
                "direction": direction,
                "speed": 3,
                "radius": 8,
                "health": 1,
                "damage": 10
            })

            self.spiral_angle += 10
            if self.spiral_angle >= 360:
                self.spiral_angle = 0

