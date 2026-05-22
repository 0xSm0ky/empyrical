import matplotlib

import matplotlib.pyplot as plt


def show_or_save(fig, out_png=None):
    if out_png:
        fig.savefig(out_png, dpi=150, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


def use_headless_if_saving(out_png):
    """Switch to the non-interactive Agg backend when only saving (no window needed)."""
    if out_png:
        matplotlib.use("Agg", force=True)
