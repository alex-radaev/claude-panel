from rich.text import Text
import random

# Matrix rain - one cycle
chars = "abcdefghijklmnopqrstuvwxyz0123456789@#$%&*(){}[]<>?!~"
columns = [random.randint(-height, 0) for _ in range(width)]
speeds = [random.choice([1, 1, 1, 2, 2, 3]) for _ in range(width)]

for frame in range(height * 2):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    styles = [["dim green"] * width for _ in range(height)]

    for col in range(width):
        head = columns[col]
        trail_len = random.randint(5, height // 2)

        for t in range(trail_len + 1):
            row = head - t
            if 0 <= row < height:
                if t == 0:
                    buf[row][col] = random.choice(chars)
                    styles[row][col] = "bold bright_white"
                elif t == 1:
                    buf[row][col] = random.choice(chars)
                    styles[row][col] = "bold bright_green"
                elif t < trail_len // 2:
                    buf[row][col] = random.choice(chars)
                    styles[row][col] = "green"
                else:
                    buf[row][col] = random.choice(chars)
                    styles[row][col] = "dim green"

        columns[col] += speeds[col]
        if columns[col] - trail_len > height:
            columns[col] = random.randint(-10, -1)
            speeds[col] = random.choice([1, 1, 1, 2, 2, 3])

    for row in range(height):
        line = Text()
        for col in range(width):
            line.append(buf[row][col], style=styles[row][col])
        canvas.write(line)

    await sleep(0.06)
