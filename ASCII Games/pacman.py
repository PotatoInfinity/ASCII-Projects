import curses
import subprocess
import signal
import sys
import os

def run_game(stdscr):
    curses.def_prog_mode()
    curses.endwin()
    
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    exe_name = "pacman.exe" if sys.platform == "win32" else "pacman"
    executable = os.path.join(base_dir, "pa2-pacman-master", "build", exe_name)
    
    if os.path.exists(executable):
        try:
            cwd = os.path.join(base_dir, "pa2-pacman-master")
            proc = subprocess.Popen([executable, "maps/1.pacmap"], cwd=cwd)
            try:
                proc.wait()
            except KeyboardInterrupt:
                proc.send_signal(signal.SIGINT)
                proc.wait()
        except Exception:
            pass
            
    curses.reset_prog_mode()
    stdscr.clear()
    stdscr.refresh()
