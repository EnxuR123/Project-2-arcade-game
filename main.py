import pygame
import random
import math
import asyncio
import os

async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Goblet Cranium")
    clock = pygame.time.Clock()
    GRAVITY = 0.65

    def load_image(filename, size):
        path = os.path.join("assets", filename)

        try:
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(image, size)
        except (FileNotFoundError, pygame.error):
            return None

    player_images = {
        "idle_right": load_image("player_idle_right.png", (50, 65)),
        "idle_left": load_image("player_idle_left.png", (50, 65)),
        "run_right": load_image("player_run_right.png", (50, 65)),
        "run_left": load_image("player_run_left.png", (50, 65)),
        "shoot_right": load_image("player_shoot_right.png", (50, 65)),
        "shoot_left": load_image("player_shoot_left.png", (50, 65))
    }

    boss_image = load_image("arcade_boss.png", (240, 300))
    bullet_image = load_image("bullet.png", (18, 18))

    class Platform:
        def __init__(self, x, y, w, h):
            self.rect = pygame.Rect(x, y, w, h)
            self.image = load_image("arcade_platform.png", (w, h))

        def draw(self):
            if self.image:
                screen.blit(self.image, self.rect)
            else:
                pygame.draw.rect(screen, (90, 100, 120), self.rect)

    class Background:
        def __init__(self):
            self.image = load_image("arcade_game_background.png", (800, 600))
            self.platforms = [
                Platform(20, 470, 110, 20),
                Platform(175, 470, 110, 20),
                Platform(330, 470, 110, 20)
            ]

        def draw(self):
            if self.image:
                screen.blit(self.image, (0, 0))
            else:
                screen.fill((30, 35, 52))

            for platform in self.platforms:
                platform.draw()

    class Player:
        def __init__(self):
            self.pos = pygame.Vector2(75, 470)
            self.velocity = pygame.Vector2()
            self.rect = pygame.Rect(0, 0, 35, 55)
            self.rect.midbottom = self.pos
            self.health = 100
            self.on_ground = True
            self.invincible = 0
            self.shoot_cooldown = 0
            self.shoot_animation = 0
            self.facing = 1
            self.bullet = []

        def update(self, keys, platforms):
            acceleration = 0

            if keys[pygame.K_a]:
                acceleration -= 0.8
                self.facing = -1

            if keys[pygame.K_d]:
                acceleration += 0.8
                self.facing = 1

            self.velocity.x += acceleration
            self.velocity.x *= 0.9
            self.velocity.x = max(-5, min(5, self.velocity.x))

            if keys[pygame.K_SPACE] and self.on_ground:
                self.velocity.y = -12
                self.on_ground = False

            self.velocity.y = min(self.velocity.y + GRAVITY, 15)

            old_bottom = self.rect.bottom

            self.pos.x += self.velocity.x
            self.rect.midbottom = (round(self.pos.x), round(self.pos.y))

            self.pos.x = max(18, min(782, self.pos.x))
            self.rect.midbottom = (round(self.pos.x), round(self.pos.y))

            self.pos.y += self.velocity.y
            self.rect.midbottom = (round(self.pos.x), round(self.pos.y))

            self.on_ground = False

            for platform in platforms:
                if (
                    self.velocity.y >= 0
                    and old_bottom <= platform.rect.top
                    and self.rect.bottom >= platform.rect.top
                    and self.rect.right > platform.rect.left
                    and self.rect.left < platform.rect.right
                ):
                    self.rect.bottom = platform.rect.top
                    self.pos.y = self.rect.bottom
                    self.velocity.y = 0
                    self.on_ground = True

            if self.rect.top > 600:
                self.pos = pygame.Vector2(75, 470)
                self.velocity = pygame.Vector2()
                self.rect.midbottom = self.pos
                self.on_ground = True

    class Boss:
        def __init__(self):
            self.health = 100
            self.position = pygame.Vector2(675, 320)
            self.image = boss_image
            self.rect = pygame.Rect(0, 0, 240, 300)
            self.rect.center = self.position
            self.spiral_angle = 0
            self.bullets = []
            self.spiral_bullets = []
            self.laser_timer = 0
            self.skill_1_cooldown = 0
            self.phase = 1
            self.damage_multiplier = 1.0
            self.attack_speed = 1.0

        def take_damage(self, attack):
            self.health -= attack.damage

        def update_phase(self):
            if self.health <= 50:
                self.phase = 2
                self.damage_multiplier = 1.5
                self.attack_speed = 1.5

        def skill_1(self, player):
            if current_skill == 1 and self.skill_1_cooldown <= 0:
                direction = pygame.Vector2(player.pos) - self.position

                if direction.length_squared() > 0:
                    direction = direction.normalize()

                for angle in [-0.3, -0.1, 0.1, 0.3]:
                    self.bullets.append({
                        "pos": pygame.Vector2(self.position),
                        "vel": direction.rotate_rad(angle) * 2.5,
                        "radius": 8,
                        "color": (0, 0, 255)
                    })

                self.skill_1_cooldown = 90

            self.skill_1_cooldown -= 1

            for bullet in self.bullets[:]:
                to_player = pygame.Vector2(player.pos) - bullet["pos"]

                if to_player.length_squared() > 0:
                    current = bullet["vel"].normalize()
                    target = to_player.normalize()
                    dot = current.dot(target)
                    cross = current.x * target.y - current.y * target.x

                    if dot < 0.999:
                        turn = 0.035

                        if cross > 0:
                            current = current.rotate_rad(turn)
                        elif cross < 0:
                            current = current.rotate_rad(-turn)

                        bullet["vel"] = current * 2.5

                bullet["pos"] += bullet["vel"]

                for player_bullet in player.bullet[:]:
                    if bullet["pos"].distance_to(player_bullet["pos"]) < 13:
                        self.bullets.remove(bullet)
                        player.bullet.remove(player_bullet)
                        break

                if bullet in self.bullets and not pygame.Rect(0, 0, 800, 600).collidepoint(bullet["pos"]):
                    self.bullets.remove(bullet)

        def skill_2(self, screen):
            self.laser_timer += 1 / 60

            if self.laser_timer < 2:
                color = (255, 255, 0)
                width = 5
            else:
                color = (255, 0, 0)
                width = 12

            pygame.draw.line(
                screen,
                color,
                (0, int(self.laser_y)),
                (800, int(self.laser_y)),
                width
            )

            if self.laser_timer >= 2.5:
                self.laser_timer = 0


        def skill_3(self):
            if not self.spiral_bullets:
                self.spiral_bullets.append({
                    "pos": pygame.Vector2(self.position),
                    "angle": math.pi,
                    "radius": 10
                })

            for bullet in self.spiral_bullets[:]:
                bullet["angle"] += 0.08
                bullet["radius"] += 2

                bullet["pos"].x = (
                    self.position.x
                    + math.cos(bullet["angle"]) * bullet["radius"]
                )
                bullet["pos"].y = (
                    self.position.y
                    + math.sin(bullet["angle"]) * bullet["radius"]
                )

                if bullet["radius"] > 850:
                    self.spiral_bullets.remove(bullet)

        def draw(self, screen):
            if self.image:
                screen.blit(self.image, self.rect.topleft)
            else:
                pygame.draw.circle(
                    screen,
                    (255, 0, 0),
                    (int(self.position.x), int(self.position.y)),
                    30
                )

            health_bar_width = 100
            health_bar_height = 10
            health_percentage = max(0, min(1, self.health / 100))

            health_bar_color = (
                (0, 255, 0) if health_percentage > 0.5
                else (255, 255, 0) if health_percentage > 0.2
                else (255, 0, 0)
            )

            health_rect = (
                self.position.x - health_bar_width // 2,
                self.position.y - 50,
                health_bar_width,
                health_bar_height
            )

            pygame.draw.rect(screen, (255, 255, 255), health_rect)
            pygame.draw.rect(
                screen,
                health_bar_color,
                (
                    health_rect[0],
                    health_rect[1],
                    int(health_bar_width * health_percentage),
                    health_bar_height
                )
            )

        def draw_skill_1(self, screen):
            for bullet in self.bullets:
                pygame.draw.circle(
                    screen,
                    bullet["color"],
                    (int(bullet["pos"].x), int(bullet["pos"].y)),
                    bullet["radius"]
                )

        def draw_skill_3(self, screen):
            for bullet in self.spiral_bullets:
                pygame.draw.circle(
                    screen,
                    (255, 0, 255),
                    (int(bullet["pos"].x), int(bullet["pos"].y)),
                    6
                )

    running = True
    boss = Boss()
    player = Player()
    background = Background()

    current_skill = random.randint(1, 3)
    skill_start = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        player.update(keys, background.platforms)

        if now - skill_start >= 3000:
            previous_skill = current_skill
            current_skill = random.choice(
                [skill for skill in (1, 2, 3) if skill != previous_skill]
            )
            skill_start = now

            if current_skill == 2:
                boss.laser_timer = 0
                boss.laser_y = random.choice([150, 450])

        boss.skill_1(player)

        boss.skill_3()

        background.draw()

        if current_skill == 2:
            boss.skill_2(screen)

        boss.draw(screen)
        boss.draw_skill_1(screen)
        boss.draw_skill_3(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())
