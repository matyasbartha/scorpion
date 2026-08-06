from collections import defaultdict
import itertools
import logging
import math
import os
import re

from downward.reports import PlanningReport
from downward.reports.scatter_matplotlib import ScatterMatplotlib
from downward.reports.scatter_pgfplots import ScatterPgfplots
from lab import tools


class ScatterMultiPlotReport(PlanningReport):
    """
    Generate a scatter plot for an attribute.
    """

    def __init__(
        self,
        relative=False,
        show_missing=True,
        get_category=None,
        title=None,
        scale=None,
        xlabel="",
        ylabel="",
        matplotlib_options=None,
        **kwargs,
    ):
        kwargs.setdefault("format", "png")

        # Backwards compatibility.
        xscale = kwargs.pop("xscale", None)
        yscale = kwargs.pop("yscale", None)
        if xscale or yscale:
            logging.warning('Use "scale" parameter instead of "xscale" and "yscale".')
        scale = scale or xscale or yscale

        PlanningReport.__init__(self, **kwargs)
        self.relative = relative
        if len(self.attributes) != 1:
            logging.critical("ScatterPlotReport needs exactly one attribute")
        self.attribute = self.attributes[0]
        # By default all values are in the same category "None".
        self.get_category = get_category or (lambda run1, run2: None)
        self.show_missing = show_missing
        if self.output_format == "tex":
            self.writer = ScatterPgfplots
        else:
            self.writer = ScatterMatplotlib
        self.title = title if title is not None else (self.attribute or "")
        self._set_scales(scale)
        self.xlabel = xlabel
        self.ylabel = ylabel
        # If the size has not been set explicitly, make it a square.
        self.matplotlib_options = matplotlib_options or {"figure.figsize": [8, 8]}
        if "legend.loc" in self.matplotlib_options:
            logging.warning('The "legend.loc" parameter is ignored.')

    def _set_scales(self, scale):
        self.xscale = scale or self.attribute.scale or "log"
        self.yscale = "log" if self.relative else self.xscale
        scales = ["linear", "log", "symlog"]
        for scale in [self.xscale, self.yscale]:
            if scale not in scales:
                logging.critical(f"Scale {scale} not in {scales}")

    def has_multiple_categories(self):
        return any(key is not None for key in self.categories.keys())

    def _fill_categories(self):
        """Map category names to coordinate lists."""
        categories = defaultdict(list)
        for runs in self.problem_runs.values():
            if len(runs) < 2:
                logging.critical(
                    "Multi scatter plot needs more than one runs for {domain}:{problem}. "
                    "Instead of filtering a whole run, try setting only some of its "
                    "attribute values to None in a filter.".format(**runs[0])
                )
            for i in range(1,len(runs)):
                category = self.get_category(runs[0], runs[i])
                coord = (runs[0].get(self.attribute), runs[i].get(self.attribute))
                if self.show_missing or None not in coord:
                    categories[category].append(coord)
        return categories

    def _turn_into_relative_coords(self, categories):
        assert self.relative
        y_rel_max = 0
        for coords in categories.values():
            for x, y in coords:
                if (x is not None and x <= 0) or (y is not None and y <= 0):
                    logging.critical("Relative scatter plots need values > 0.")
                if x is not None and y is not None:
                    y_rel_max = max(y_rel_max, y / float(x))
        y_rel_missing = y_rel_max * 1.5 if y_rel_max != 0 else None
        x_missing = self._compute_missing_value(categories, 0, self.xscale)
        self.x_upper = x_missing
        self.y_upper = y_rel_missing

        new_categories = {}
        for category, coords in categories.items():
            new_coords = []
            for coord in coords:
                x, y = coord
                if x is None and y is None:
                    x, y = x_missing, y_rel_missing
                elif x is None and y is not None:
                    x, y = x_missing, 1
                elif x is not None and y is None:
                    x, y = x, y_rel_missing
                elif x is not None and y is not None:
                    x, y = x, y / float(x)
                new_coords.append((x, y))
            if new_coords:
                new_categories[category] = new_coords
        return new_categories

    def _compute_missing_value(self, categories, axis, scale):
        if not self.show_missing:
            return None
        values = [coord[axis] for coords in categories.values() for coord in coords]
        real_values = [value for value in values if value is not None]
        if len(real_values) == len(values):
            # The list doesn't contain None values.
            return None
        if not real_values:
            return 1
        max_value = max(real_values)
        if scale == "linear":
            return max_value * 1.1
        return int(10 ** math.ceil(math.log10(max_value)))

    def _handle_non_positive_values(self, categories):
        """Plot integer 0 values at 0.1 in log plots and abort if any value is < 0."""
        assert not self.relative
        assert self.xscale == self.yscale == "log"
        new_categories = {}
        for category, coords in categories.items():
            new_coords = []
            for x, y in coords:
                if x == 0 and isinstance(x, int):
                    x = 0.1
                if y == 0 and isinstance(y, int):
                    y = 0.1

                if (x is not None and x <= 0) or (y is not None and y <= 0):
                    logging.critical(
                        "Logarithmic axes can only show positive values. "
                        "Use a symlog or linear scale instead."
                    )
                else:
                    new_coords.append((x, y))
            new_categories[category] = new_coords
        return new_categories

    def _handle_missing_values(self, categories):
        assert not self.relative
        x_missing = self._compute_missing_value(categories, 0, self.xscale)
        y_missing = self._compute_missing_value(categories, 1, self.yscale)
        if x_missing is None:
            missing_value = y_missing
        elif y_missing is None:
            missing_value = x_missing
        else:
            missing_value = max(x_missing, y_missing)
        self.x_upper = missing_value
        self.y_upper = missing_value

        if not self.show_missing:
            # Coords with None values have already been filtered.
            return categories

        new_categories = {}
        for category, coords in categories.items():
            coords = [
                (
                    x if x is not None else missing_value,
                    y if y is not None else missing_value,
                )
                for x, y in coords
            ]
            if coords:
                new_categories[category] = coords
        return new_categories

    def _compute_num_tasks_on_sides_of_line(self, categories):
        min_wins = self.attribute.min_wins
        x_wins = 0
        y_wins = 0
        for coords in categories.values():
            for x, y in coords:
                if x is None or y is None:
                    continue
                if x > y:
                    if min_wins:
                        y_wins += 1
                    else:
                        x_wins += 1
                elif x < y:
                    if min_wins:
                        x_wins += 1
                    else:
                        y_wins += 1
        return x_wins, y_wins

    def _get_category_styles(self, categories):
        """
        Assign fixed marker shapes and colors to algorithms.
        """
        marker_map = {
            "master-cegar": "^",
            "original-cegar": "o",
            "random-optimal-path": "s",
        }

        color_map = {
            "master-cegar": "C0",
            "original-cegar": "C1",
            "random-optimal-path": "C2",
        }

        category_styles = {}

        for category in sorted(categories):
            category_styles[category] = {
                "marker": marker_map.get(category, "o"),
                "c": color_map.get(category, "C0"),
            }

        return category_styles

    def _add_tex_transparency(self):
        """
        Add marker transparency to the generated PGFPlots file.
        """
        if self.output_format != "tex":
            return

        with open(self.outfile, encoding="utf-8") as file:
            tex = file.read()

        # Handles commands such as:
        # \addplot+[only marks,mark=...] coordinates {
        tex = re.sub(
            r"(\\addplot\+\[)([^\]]*)\]",
            lambda match: (
                match.group(1)
                + match.group(2).rstrip(", ")
                + ", fill opacity=0.4, draw opacity=0.8]"
            ),
            tex,
        )

        with open(self.outfile, "w", encoding="utf-8") as file:
            file.write(tex)

    def _get_axis_label(self, label, algo, num_wins):
        if label:
            return label
        if self.attribute.min_wins is None:
            return algo
        comp = "lower" if self.attribute.min_wins else "higher"
        return f"{algo} ({comp} for {num_wins} tasks)"

    def _write_plot(self, runs, filename):
        # Map category names to coord tuples.
        self.categories = self._fill_categories()
        x_wins, y_wins = self._compute_num_tasks_on_sides_of_line(self.categories)
        if self.relative:
            self.plot_diagonal_line = False
            self.plot_horizontal_line = True
            self.categories = self._turn_into_relative_coords(self.categories)
        else:
            self.plot_diagonal_line = True
            self.plot_horizontal_line = False
            if self.xscale == "log":
                assert self.yscale == "log"
                self.categories = self._handle_non_positive_values(self.categories)
            self.categories = self._handle_missing_values(self.categories)
        if not self.categories:
            logging.critical("Plot contains no points.")

        self.xlabel = self._get_axis_label(self.xlabel, self.algorithms[0], x_wins)
        if len(self.algorithms) == 2:
            self.ylabel = self._get_axis_label(self.ylabel, self.algorithms[1], y_wins)
        else:
            self.ylabel = self._get_axis_label(self.ylabel, "see legend", y_wins)

        self.styles = self._get_category_styles(self.categories)
        self.writer.write(self, filename)

    def write(self):
        if len(self.algorithms) < 2:
            logging.critical(
                f"Multi scatter plots need more than 1 algorithm: {self.algorithms}"
            )
        suffix = "." + self.output_format
        if not self.outfile.endswith(suffix):
            self.outfile += suffix
        tools.makedirs(os.path.dirname(self.outfile))
        self._write_plot(self.runs.values(), self.outfile)
        self._add_tex_transparency()
