import curses
import asyncio
import time
import random
from typing import Coroutine

from curses_tools import draw_frame, read_controls, get_frame_size


def draw(canvas):
    canvas.border()
    curses.curs_set(0)
    canvas.nodelay(True)

    rocket_frame_1, rocket_frame_2 = get_rocket_frames()
    height, width = canvas.getmaxyx()

    fire_1 = get_fire_coroutine(canvas, height, width)
    spaceship = get_spaceship_coroutine(canvas, height, width, rocket_frame_1, rocket_frame_2)
    blinks = get_blinks_coroutine(canvas, height, width, stars_count=150)

    coroutines = []
    coroutines.extend(blinks)
    coroutines.append(fire_1)
    coroutines.append(spaceship)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(0.1)


def get_blinks_coroutine(canvas, height, width, stars_count=10, symbols=('*', '+', '.', ':')):
    return [
        blink(
            canvas,
            row=random.randint(1, height - 2),
            column=random.randint(1, width - 2),
            symbol=random.choice(symbols)
        )
        for _ in range(stars_count)
    ]


def get_fire_coroutine(canvas, height, width) -> Coroutine:
    return fire(
        canvas,
        start_row=height // 2,
        start_column=width // 2,
        columns_speed=1
    )


def get_spaceship_coroutine(canvas, height, width, rocket_frame_1, rocket_frame_2) -> Coroutine:
    return animate_spaceship(
        canvas,
        row=height // 2,
        column=width // 2,
        rocket_frame_1=rocket_frame_1,
        rocket_frame_2=rocket_frame_2
    )


def get_rocket_frames() -> tuple:
    with open('frames/rocket_frame_1.txt', 'r') as file_1:
        frame_1 = file_1.read()

    with open('frames/rocket_frame_2.txt', 'r') as file_2:
        frame_2 = file_2.read()

    return frame_1, frame_2


def get_new_spaceship_coordinates(canvas, row, column, frame_size_rows,
                                  frame_size_columns, max_height, max_width) -> tuple:
    row_d, column_d, space = read_controls(canvas)
    row = max_height - frame_size_rows if row + row_d > max_height - frame_size_rows else row + row_d
    if row < 0:
        row = 0

    column = max_width - frame_size_columns if column + column_d > max_width - frame_size_columns else column + column_d
    if column < 0:
        column = 0
    return row, column


async def animate_spaceship(canvas, row, column, rocket_frame_1, rocket_frame_2):
    max_height, max_width = canvas.getmaxyx()
    frame_size_rows, frame_size_columns = get_frame_size(rocket_frame_1)
    while True:
        row, column = get_new_spaceship_coordinates(
            canvas, row, column, frame_size_rows,
            frame_size_columns, max_height, max_width
        )
        draw_frame(canvas, row, column, rocket_frame_1)
        canvas.refresh()
        for _ in range(2):
            await asyncio.sleep(0)
        draw_frame(canvas, row, column, rocket_frame_1, negative=True)
        draw_frame(canvas, row, column, rocket_frame_2)
        canvas.refresh()
        for _ in range(2):
            await asyncio.sleep(0)
        draw_frame(canvas, row, column, rocket_frame_2, negative=True)


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(10):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        for _ in range(random.randint(1, 10)):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
