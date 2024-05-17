import random

with open('terrain.txt', 'w') as file:
  file.write("# Each line contains x, y coordinates defining the terrain contour\n")
  x = -50
  y = 100
  file.write(f"{x}, {y}, 0\n")
  for _ in range(200):
    c = random.randint(0, 4)
    x += random.randint(20, 300)
    yInc = random.randint(-100, 100)
    y += yInc
    if y < 5:
      y = 5
    if y > 500:
      y = 500
    file.write(f"{x}, {y}, {c}\n")

  for _ in range(50):
    x += random.randint(10, 50)
    file.write(f"{x}, {y}, 4\n")
    y+=25
    if y > 700:
      break
