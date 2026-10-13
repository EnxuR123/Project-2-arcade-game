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
    asset_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

    def load_image(filename, size):
        path = os.path.join(asset_directory, filename)

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

    boss_image = load_image("aracde_boss.png", (300, 600))
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
            self.reset_platforms()

        def reset_platforms(self):
            self.platforms = [
                Platform(20, 470, 110, 20),
                Platform(97, 370, 110, 20),
                Platform(175, 290, 110, 20),
                Platform(175, 470, 110, 20),
                Platform(252, 370, 110, 20),
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
            self.max_health = 100
            self.health = self.max_health
            self.on_ground = True
            self.invincible_until = 0
            self.shoot_cooldown = 0
            self.shoot_animation = 0
            self.facing = 1
            self.bullet = []
            self.is_firing = False
            self.drop_through_platform = None
            self.drop_key_was_pressed = False

        def take_damage(self, damage):
            now = pygame.time.get_ticks()
            if now < self.invincible_until:
                return

            self.health = max(0, self.health - damage)
            self.invincible_until = now + 2000

        def update(self, keys, platforms):
            self.is_firing = pygame.mouse.get_pressed()[0]
            self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
            drop_key_pressed = keys[pygame.K_s]

            if drop_key_pressed and not self.drop_key_was_pressed and self.on_ground:
                self.drop_through_platform = next(
                    (
                        platform for platform in platforms
                        if self.rect.bottom == platform.rect.top
                        and self.rect.right > platform.rect.left
                        and self.rect.left < platform.rect.right
                    ),
                    None
                )
                if self.drop_through_platform:
                    self.on_ground = False
                    self.velocity.y = 1
            self.drop_key_was_pressed = drop_key_pressed

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
                    platform is not self.drop_through_platform
                    and self.velocity.y >= 0
                    and old_bottom <= platform.rect.top
                    and self.rect.bottom >= platform.rect.top
                    and self.rect.right > platform.rect.left
                    and self.rect.left < platform.rect.right
                ):
                    self.rect.bottom = platform.rect.top
                    self.pos.y = self.rect.bottom
                    self.velocity.y = 0
                    self.on_ground = True

            if (
                self.drop_through_platform
                and self.rect.top >= self.drop_through_platform.rect.bottom
            ):
                self.drop_through_platform = None

            if self.rect.top > 600:
                self.take_damage(20)
                self.pos = pygame.Vector2(75, 470)
                self.velocity = pygame.Vector2()
                self.rect.midbottom = self.pos
                self.on_ground = True
                self.drop_through_platform = None

            if self.is_firing and self.shoot_cooldown == 0:
                bullet_x = self.rect.centerx + self.facing * (self.rect.width // 2 + 4)
                self.bullet.append({
                    "pos": pygame.Vector2(bullet_x, self.rect.centery),
                    "vel": pygame.Vector2(self.facing * 9, 0)
                })
                self.shoot_cooldown = 15

        def update_bullets(self, boss):
            bullet_size = bullet_image.get_size() if bullet_image else (8, 8)
            screen_rect = pygame.Rect(0, 0, 800, 600)

            for bullet in self.bullet[:]:
                bullet["pos"] += bullet["vel"]
                bullet_rect = pygame.Rect(0, 0, *bullet_size)
                bullet_rect.center = bullet["pos"]

                if boss.rect.colliderect(bullet_rect):
                    boss.take_damage(1)
                    self.bullet.remove(bullet)
                elif not screen_rect.colliderect(bullet_rect):
                    self.bullet.remove(bullet)

        def draw(self, screen):
            if self.is_firing:
                image_name = "shoot_right" if self.facing > 0 else "shoot_left"
            elif abs(self.velocity.x) > 0.1:
                image_name = "run_right" if self.facing > 0 else "run_left"
            else:
                image_name = "idle_right" if self.facing > 0 else "idle_left"

            is_blinking = (
                pygame.time.get_ticks() < self.invincible_until
                and (pygame.time.get_ticks() // 100) % 2 == 0
            )
            if not is_blinking:
                image = player_images[image_name]
                if image:
                    image_rect = image.get_rect(midbottom=self.rect.midbottom)
                    screen.blit(image, image_rect)
                else:
                    pygame.draw.rect(screen, (60, 150, 255), self.rect)

            for bullet in self.bullet:
                if bullet_image:
                    image = bullet_image if bullet["vel"].x > 0 else pygame.transform.flip(
                        bullet_image, True, False
                    )
                    screen.blit(image, image.get_rect(center=bullet["pos"]))
                else:
                    pygame.draw.circle(screen, (255, 230, 80), bullet["pos"], 4)

    class Boss:
        def __init__(self):
            self.max_health = 150
            self.health = self.max_health
            self.position = pygame.Vector2(675, 320)
            self.image = boss_image
            self.phase_image = self.image
            self.rect = pygame.Rect(560, 0, 240, 600)
            self.image_rect = (
                self.image.get_rect(midright=(800, 300))
                if self.image
                else self.rect.copy()
            )
            self.spiral_angle = 0
            self.bullets = []
            self.spiral_bullets = []
            self.laser_timer = 0
            self.laser_damaged = False
            self.laser_y = random.choice([150, 450])
            self.platform_attacks_used = set()
            self.platform_projectiles = []
            self.skill_1_cooldown = 0
            self.phase = 1
            self.damage_multiplier = 1.0
            self.attack_speed = 1.0

        def take_damage(self, attack):
            self.health = max(0, self.health - attack)

        def update_phase(self):
            if self.health <= self.max_health * 0.5 and self.phase == 1:
                self.phase = 2
                self.damage_multiplier = 1.5
                self.attack_speed = 1.5
                if self.image:
                    self.phase_image = self.image.copy()
                    self.phase_image.fill((80, 0, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        def skill_1(self, player):
            if current_skill == 1 and self.skill_1_cooldown <= 0:
                projectile_speed = 3.5 if self.phase == 2 else 1.5
                spawn_positions = (
                    (self.position.y,)
                    if self.phase == 2
                    else (self.position.y - 45, self.position.y + 45)
                )
                for spawn_y in spawn_positions:
                    direction = pygame.Vector2(player.pos) - pygame.Vector2(
                        self.position.x, spawn_y
                    )
                    if direction.length_squared() > 0:
                        direction = direction.normalize()
                    self.bullets.append({
                        "pos": pygame.Vector2(self.position.x, spawn_y),
                        "vel": direction * projectile_speed,
                        "speed": projectile_speed,
                        "radius": 8,
                        "color": (0, 0, 255),
                        "created_at": pygame.time.get_ticks(),
                        "lifetime": 4000 if self.phase == 2 else 8000
                    })

                self.skill_1_cooldown = 60 if self.phase == 2 else 120

            self.skill_1_cooldown = max(0, self.skill_1_cooldown - 1)

            for bullet in self.bullets[:]:
                if pygame.time.get_ticks() - bullet["created_at"] >= bullet["lifetime"]:
                    self.bullets.remove(bullet)
                    continue

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

                        bullet["vel"] = current * bullet["speed"]

                bullet["pos"] += bullet["vel"]

                if bullet in self.bullets:
                    bullet_rect = pygame.Rect(
                        int(bullet["pos"].x - bullet["radius"]),
                        int(bullet["pos"].y - bullet["radius"]),
                        bullet["radius"] * 2,
                        bullet["radius"] * 2
                    )
                    if player.rect.colliderect(bullet_rect):
                        player.take_damage(15)
                        self.bullets.remove(bullet)

                if bullet in self.bullets and not pygame.Rect(0, 0, 800, 600).collidepoint(bullet["pos"]):
                    self.bullets.remove(bullet)

        def skill_2(self, screen, player):
            self.laser_timer += 1 / 60
            warning_duration = 1.25 if self.phase == 2 else 2
            active_duration = 0.5

            if self.laser_timer < warning_duration:
                color = (255, 255, 0)
                width = 12
            else:
                color = (255, 0, 0)
                width = 24

                laser_rect = pygame.Rect(
                    0,
                    int(self.laser_y - width / 2),
                    800,
                    width
                )
                if not self.laser_damaged and player.rect.colliderect(laser_rect):
                    player.take_damage(30)
                    self.laser_damaged = True

            pygame.draw.line(
                screen,
                color,
                (0, int(self.laser_y)),
                (800, int(self.laser_y)),
                width
            )

            if self.laser_timer >= warning_duration + active_duration:
                self.laser_timer = 0
                self.laser_damaged = False

        def update_platform_attack(self, platforms):
            if self.phase == 2:
                for threshold, platform_y in ((0.5, 370), (0.25, 470)):
                    if (
                        self.health <= self.max_health * threshold
                        and threshold not in self.platform_attacks_used
                    ):
                        self.platform_attacks_used.add(threshold)
                        eligible_platforms = [
                            platform for platform in platforms
                            if platform.rect.top == platform_y
                        ]
                        if eligible_platforms:
                            target = random.choice(eligible_platforms)
                            position = pygame.Vector2(self.position.x - 120, self.position.y)
                            direction = pygame.Vector2(target.rect.center) - position
                            self.platform_projectiles.append({
                                "pos": position,
                                "vel": direction.normalize() * 4,
                                "target": target
                            })

            for projectile in self.platform_projectiles[:]:
                projectile["pos"] += projectile["vel"]
                target = projectile["target"]
                projectile_rect = pygame.Rect(0, 0, 24, 24)
                projectile_rect.center = projectile["pos"]

                if target in platforms and projectile_rect.colliderect(target.rect):
                    platforms.remove(target)
                    self.platform_projectiles.remove(projectile)
                elif not pygame.Rect(0, 0, 800, 600).collidepoint(projectile["pos"]):
                    self.platform_projectiles.remove(projectile)

        def draw_platform_projectiles(self, screen):
            for projectile in self.platform_projectiles:
                target = projectile["target"]
                if target:
                    marker = platform_warning_font.render("!", True, (255, 50, 50))
                    screen.blit(
                        marker,
                        marker.get_rect(midbottom=(target.rect.centerx, target.rect.top - 6))
                    )
                pygame.draw.circle(
                    screen,
                    (255, 35, 35),
                    (int(projectile["pos"].x), int(projectile["pos"].y)),
                    12
                )


        def skill_3(self, player):
            if not self.spiral_bullets:
                self.spiral_bullets.append({
                    "pos": pygame.Vector2(self.position),
                    "angle": math.pi,
                    "radius": 100
                })

            for bullet in self.spiral_bullets[:]:
                bullet["angle"] += 0.02 * self.attack_speed
                bullet["radius"] += 0.5 * self.attack_speed

                bullet["pos"].x = (
                    self.position.x
                    + math.cos(bullet["angle"]) * bullet["radius"]
                )
                bullet["pos"].y = (
                    self.position.y
                    + math.sin(bullet["angle"]) * bullet["radius"]
                )

                closest_point = pygame.Vector2(
                    max(player.rect.left, min(bullet["pos"].x, player.rect.right)),
                    max(player.rect.top, min(bullet["pos"].y, player.rect.bottom))
                )
                if bullet["pos"].distance_to(closest_point) <= 16:
                    player.take_damage(25)
                    self.spiral_bullets.remove(bullet)
                    continue

                if bullet["radius"] > 1000:
                    self.spiral_bullets.remove(bullet)

        def draw(self, screen):
            if self.phase_image:
                screen.blit(self.phase_image, self.image_rect.topleft)
            else:
                pygame.draw.circle(
                    screen,
                    (255, 0, 0),
                    (int(self.position.x), int(self.position.y)),
                    30
                )

            health_bar_width = 100
            health_bar_height = 10
            health_percentage = max(0, min(1, self.health / self.max_health))

            health_bar_color = (
                (0, 255, 0) if health_percentage > 0.5
                else (255, 255, 0) if health_percentage > 0.25
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
                    16
                )

    running = True
    boss = Boss()
    player = Player()
    background = Background()

    def choose_laser_lane():
        laser_lanes = sorted({
            platform.rect.top - player.rect.height // 2
            for platform in background.platforms
        })
        boss.laser_y = random.choice(laser_lanes)

    game_over = False
    victory = False
    game_started = False

    current_skill = random.randint(1, 3)
    if current_skill == 2:
        choose_laser_lane()
    skill_start = pygame.time.get_ticks()
    game_over_font = pygame.font.Font(None, 72)
    restart_font = pygame.font.Font(None, 36)
    victory_font = pygame.font.Font(None, 72)
    hp_font = pygame.font.Font(None, 32)
    platform_warning_font = pygame.font.Font(None, 48)
    menu_title_font = pygame.font.Font(None, 72)
    menu_font = pygame.font.Font(None, 32)
    menu_button_rect = pygame.Rect(325, 265, 150, 50)
    menu_controls = [
        "A / D - Move",
        "SPACE - Jump",
        "S - Descend through a platform",
        "Left mouse button - Shoot"
    ]

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif not game_started and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_button_rect.collidepoint(event.pos):
                    game_started = True
                    skill_start = pygame.time.get_ticks()
            elif (game_over or victory) and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                boss = Boss()
                player = Player()
                background.reset_platforms()
                current_skill = random.randint(1, 3)
                if current_skill == 2:
                    choose_laser_lane()
                skill_start = pygame.time.get_ticks()
                game_over = False
                victory = False

        if not game_started:
            if background.image:
                screen.blit(background.image, (0, 0))
            else:
                screen.fill((30, 35, 52))
            menu_overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            menu_overlay.fill((0, 0, 0, 100))
            screen.blit(menu_overlay, (0, 0))
            title = menu_title_font.render("Goblet Cranium", True, (255, 255, 255))
            screen.blit(title, title.get_rect(center=(400, 110)))

            mouse_position = pygame.mouse.get_pos()
            button_color = (90, 180, 120) if menu_button_rect.collidepoint(mouse_position) else (60, 140, 95)
            pygame.draw.rect(screen, button_color, menu_button_rect, border_radius=8)
            play_text = menu_font.render("PLAY", True, (255, 255, 255))
            screen.blit(play_text, play_text.get_rect(center=menu_button_rect.center))

            controls_title = menu_font.render("CONTROLS", True, (255, 220, 100))
            screen.blit(controls_title, controls_title.get_rect(center=(400, 365)))
            for index, control in enumerate(menu_controls):
                control_text = menu_font.render(control, True, (230, 230, 230))
                screen.blit(control_text, control_text.get_rect(center=(400, 405 + index * 35)))

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)
            continue

        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        if not game_over and not victory:
            boss.update_phase()
            boss.update_platform_attack(background.platforms)
            player.update(keys, background.platforms)
            player.update_bullets(boss)

            skill_interval = 1500 if boss.phase == 2 else 2000
            if now - skill_start >= skill_interval:
                previous_skill = current_skill
                current_skill = random.choice(
                    [skill for skill in (1, 2, 3) if skill != previous_skill]
                )
                skill_start = now

                if current_skill == 2:
                    boss.laser_timer = 0
                    boss.laser_damaged = False
                    choose_laser_lane()

            if boss.health <= 0:
                victory = True
            else:
                boss.skill_1(player)
                boss.skill_3(player)

            if player.health <= 0:
                game_over = True

        background.draw()

        if not game_over and not victory and current_skill == 2:
            boss.skill_2(screen, player)

        if player.health <= 0:
            game_over = True

        boss.draw(screen)
        player.draw(screen)
        boss.draw_skill_1(screen)
        boss.draw_skill_3(screen)
        boss.draw_platform_projectiles(screen)
        hp_text = hp_font.render(f"HP: {player.health}/{player.max_health}", True, (255, 255, 255))
        screen.blit(hp_text, (16, 560))

        if game_over:
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            game_over_text = game_over_font.render("GAME OVER", True, (255, 255, 255))
            restart_text = restart_font.render("Press R to restart", True, (255, 255, 255))
            screen.blit(game_over_text, game_over_text.get_rect(center=(400, 260)))
            screen.blit(restart_text, restart_text.get_rect(center=(400, 325)))
        elif victory:
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            victory_text = victory_font.render("YOU WIN!", True, (255, 230, 80))
            restart_text = restart_font.render("Press R to retry", True, (255, 255, 255))
            screen.blit(victory_text, victory_text.get_rect(center=(400, 260)))
            screen.blit(restart_text, restart_text.get_rect(center=(400, 325)))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())
