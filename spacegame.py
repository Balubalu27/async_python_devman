import curses
import asyncio
import itertools
import os
import time
import random
from typing import Coroutine

from curses_tools import draw_frame, read_controls, get_frame_size


def draw(canvas):
    canvas.border()
    curses.curs_set(0)
    canvas.nodelay(True)

    rocket_frames = get_rocket_frames()
    height, width = canvas.getmaxyx()

    fire_coroutine = get_fire_coroutine(canvas, height, width)
    spaceship_coroutine = get_spaceship_coroutine(canvas, height, width, rocket_frames)
    blinks_coroutine = get_blinks_coroutine(canvas, height, width, stars_count=150)

    coroutines = []
    coroutines.extend(blinks_coroutine)
    coroutines.append(fire_coroutine)
    coroutines.append(spaceship_coroutine)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(0.1)


def get_blinks_coroutine(canvas, height, width, stars_count=10, symbols='*+.:'):
    distance_from_border = 2

    min_row_coordinate = 1
    max_row_coordinate = height - distance_from_border

    min_column_number = 1
    max_column_number = width - distance_from_border

    offset_tics = random.randint(1, 10)

    return [
        blink(
            canvas,
            row=random.randint(min_row_coordinate, max_row_coordinate),
            column=random.randint(min_column_number, max_column_number),
            symbol=random.choice(symbols),
            offset_tics=offset_tics
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


def get_spaceship_coroutine(canvas, height, width, rocket_frames) -> Coroutine:
    return animate_spaceship(
        canvas,
        row=height // 2,
        column=width // 2,
        rocket_frames=rocket_frames
    )


def get_rocket_frames() -> list:
    frames = []
    for rocket_frame in os.listdir('frames/'):
        if not rocket_frame.endswith('rocket_frame.txt'):
            continue
        with open(f'frames/{rocket_frame}', 'r') as file_1:
            frames.append(file_1.read())
    return frames


def get_new_spaceship_coordinates(canvas, row, column, frame_size_rows,
                                  frame_size_columns, max_height, max_width) -> tuple:
    row_direction, column_direction, space = read_controls(canvas)

    new_row_coordinate = max(row + row_direction, 0)
    max_row_coordinate = max_height - frame_size_rows
    row = min(new_row_coordinate, max_row_coordinate)

    new_column_coordinate = max(column + column_direction, 0)
    max_column_coordinate = max_width - frame_size_columns
    column = min(new_column_coordinate, max_column_coordinate)

    return row, column


async def animate_spaceship(canvas, row, column, rocket_frames):
    max_height, max_width = canvas.getmaxyx()

    for rocket_frame in itertools.cycle(rocket_frames):
        frame_size_rows, frame_size_columns = get_frame_size(rocket_frame)

        row, column = get_new_spaceship_coordinates(
            canvas, row, column, frame_size_rows,
            frame_size_columns, max_height, max_width
        )

        draw_frame(canvas, row, column, rocket_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, rocket_frame, negative=True)


async def blink(canvas, row, column, symbol='*', offset_tics=5):
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

        for _ in range(offset_tics):
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
