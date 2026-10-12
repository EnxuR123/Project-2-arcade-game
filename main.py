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
            self.bullets = []
            self.spiral_bullets= []
            self.laser_start = pygame.time.get_ticks()
            self.laser_y = random.choice([150, 450])

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

        def skill_2(self,screen):
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
                screen,               
                color,                  
                (0, self.laser_y),      
                (800, self.laser_y),    
                width                   
            )

        
        def skill_3(self):
            if not self.spiral_bullets:
                self.spiral_bullets.append({
                    "center": pygame.Vector2(self.position),
                    "angle": 0,
                    "distance": 0,
                    "radius": 8,
                    "damage": 10,
                    "position": pygame.Vector2(self.position)
                })

            bullet = self.spiral_bullets[0]

            bullet["angle"] += 0.05
            bullet["distance"] += 1

            bullet["position"] = (
                bullet["center"]
                + pygame.Vector2(
                    math.cos(bullet["angle"]),
                    math.sin(bullet["angle"])
                ) * bullet["distance"]
            )


        def draw(self, screen):
            pygame.draw.circle(screen, (255, 0, 0), self.position, 30)
            health_bar_width = 100
            health_bar_height = 10
            health_percentage = self.health / 100
            health_bar_color = (0, 255, 0) if health_percentage > 0.5 else (255, 255, 0) if health_percentage > 0.2 else (255, 0, 0)
            pygame.draw.rect(screen, (255, 255, 255), (self.position[0] - health_bar_width // 2, self.position[1] - 50, health_bar_width, health_bar_height))
            pygame.draw.rect(screen, health_bar_color, (self.position[0] - health_bar_width // 2, self.position[1] - 50, int(health_bar_width * health_percentage), health_bar_height))

        def draw_skill_1(self, screen):
            for bullet in self.bullets:
                pygame.draw.circle(screen, (0, 0, 255), bullet["position"], bullet["radius"])

        def draw_skill_3(self, screen):
            for bullet in self.spiral_bullets:
                pygame.draw.circle(
                    screen,
                    (255, 0, 255),
                    (int(bullet["position"].x),
                    int(bullet["position"].y)),
                    bullet["radius"]
                )



    running = True
    boss = Boss()
    current_skill = random.randint(1, 3)
    skill_start = pygame.time.get_ticks()
    last_skill_1 = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        now = pygame.time.get_ticks()
        if now - skill_start >= 3000:
            previous_skill = current_skill
            current_skill = random.randint(1, 3)
            skill_start = now

            if previous_skill == 3 and current_skill != 3:
                boss.spiral_bullets.clear()


        if current_skill == 1:
            if now - last_skill_1 >= 1000:
                boss.skill_1(player)
                last_skill_1 = now
            for bullet in boss.bullets:
                bullet["position"] += (
                    bullet["direction"] * bullet["speed"]
                )
        elif current_skill == 2:
            pass
        elif current_skill == 3:
            boss.skill_3()


        screen.fill((0, 0, 0))
        if current_skill == 2:
            boss.skill_2(screen)
        boss.draw(screen)
        boss.draw_skill_1(screen)
        boss.draw_skill_3(screen)

        pygame.display.flip()
        clock.tick(60)
