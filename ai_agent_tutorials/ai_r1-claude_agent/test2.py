
import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Set up the window
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Bouncing Rectangle")

# Rectangle properties
rect_width = 50
rect_height = 30
x = screen_width // 2 - rect_width // 2  # Start in the center
y = screen_height // 2 - rect_height // 2
dx = 5  # Speed in x direction
dy = 5  # Speed in y direction

# Initial color (white)
color = (255, 255, 255)

# Clock to control frame rate
clock = pygame.time.Clock()

# Main loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update position
    x += dx
    y += dy

    # Create rect for collision detection
    rect = pygame.Rect(x, y, rect_width, rect_height)

    # Check for collisions with left/right boundaries
    if rect.left <= 0 or rect.right >= screen_width:
        dx = -dx  # Reverse direction
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # Check for collisions with top/bottom boundaries
    if rect.top <= 0 or rect.bottom >= screen_height:
        dy = -dy  # Reverse direction
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # Draw everything
    screen.fill((0, 0, 0))  # Clear screen with black
    pygame.draw.rect(screen, color, rect)
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()
sys.exit()