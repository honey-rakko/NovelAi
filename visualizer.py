"""CharacterNetwork Visualizer - Backward compatibility wrapper"""

from visualizer import WebStoryGraphVisualizer, run_visualizer

__all__ = ["WebStoryGraphVisualizer", "run_visualizer"]


if __name__ == "__main__":
    run_visualizer()
