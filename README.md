# ASCII Retro Games & Real-time Filters

This repository is a collection of projects centered around ASCII art. It consists of two major components: a retro arcade games console featuring 12 terminal games, and a native macOS real-time screen-to-ASCII filter application.

---

## Repository Structure

The repository is organized into two primary subdirectories:

```
root/
├── ASCII Games/        # Python Curses retro games suite & C++ Pacman
│   ├── main.py            # Main interactive arcade launcher (Python)
│   ├── pa2-pacman-master/ # Pacman game
│   └── *.py               # Core game files (Doom, Tetris, Mario, etc.)
│
└── ASCII filter/       # Real-time macOS screen-to-ASCII filter app
    ├── build.sh           # Shell compilation script
    └── *.swift            # Native Swift and Metal Shader sources
```
Pacman game by [Vojtech Cahlik](https://github.com/vcahlik/pa2-pacman)

---

## Projects Overview

### 1. ASCII Arcade Suite
An interactive retro arcade cabinet that runs directly inside your command-line terminal. It includes 12 classic retro games using ASCII graphics.

To launch the Python Arcade:
> ```bash
> cd "ASCII Games"
> python3 main.py
> ```

---

### 2. ASCII-Lens (ASCII filter)
A native Swift macOS application designed to transform your entire screen—or any target window—into real-time, interactive ASCII art.
Uses Apple's `ScreenCaptureKit` API for ultra-low latency desktop capturing, `CoreVideo`/`CoreMedia` pipelines, and a customized **Metal-accelerated fragment shader** that translates pixel luminance values into dynamic ASCII glyph selections. Features a customizable controller panel to modify scale, contrast, and color modes in real-time.

To compile and run the macOS ASCII Filter:
> ```bash
> cd "ASCII filter"
> chmod +x build.sh
> ./build.sh
> open ASCII-Lens.app
> ```
* Requires macOS 13.0 (Ventura) or later.

---

## Global Requirements
`Swift Compiler (`swiftc`), CMake, C++ Compiler, and Python 3.`