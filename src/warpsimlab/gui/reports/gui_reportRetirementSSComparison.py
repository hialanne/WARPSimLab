# gui_reportRetirementSSComparison.py

import copy
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class RetirementSSComparisonReportFrame(ScalableFrameMixin, ttk.Frame):

    DEFAULT_OPTIONS = {
        "retirement_ages": [62, 64, 66, 68, 70],
        "social_security_ages": [62, 64, 66, 68, 70],
        "output": {
            "generate_html": True,
            "open_report_in_browser": False,
        },
    }


    def __init__(
        self,
        parent,
        report_options,
        parent_gui,
        title="Retirement & Social Security Comparison Report",
    ):
        super().__init__(parent, padding=10)

        self.options = report_options
        self.parent_gui = parent_gui
        self.working_options = self._normalize_options(report_options)

        self.show_wife = bool(self.parent_gui.simulation_controls.get("second_person_enabled", False))
        self.current_retirement_age = self._compute_household_retirement_age()
        self.current_ss_age = self._compute_household_ss_age()

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._title_font = tkfont.Font(root=self, family="Arial", size=14, weight="bold")
        self._text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._text_bold_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._text_italic_font = tkfont.Font(root=self, family="Arial", size=11, slant="italic")
        self._section_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")

        self._age_entries = []

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._title_font)
        self._register_scalable_font(self._text_font)
        self._register_scalable_font(self._text_bold_font)
        self._register_scalable_font(self._text_italic_font)
        self._register_scalable_font(self._section_font)
        self._apply_gui_scale()

        self._build_header(title)
        self._build_current_timing()
        self._build_retirement_ages()
        self._build_social_security_ages()
        self._build_output_options()
        self._build_buttons()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("RetirementSS.TEntry", font=self._body_font)
        style.configure("RetirementSS.TCheckbutton", font=self._body_font)
        style.configure("RetirementSS.TButton", font=self._body_font)

        for entry in self._age_entries:
            entry.configure(width=7)


    def _build_header(self, title):
        ttk.Label(self, text=title, font=self._title_font).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        ttk.Label(
            self,
            text=(
                "Compare how different retirement and Social Security claiming ages affect modeled "
                "financial outcomes."
            ),
            font=self._text_font,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        note_frame = ttk.Frame(self)
        note_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            note_frame,
            text="NOTE: Retirement & Social Security Reports are written to: ",
            font=self._text_italic_font,
        ).pack(side="left")

        ttk.Label(
            note_frame,
            text="Desktop \\ WARPSimLab \\ Reports",
            font=self._text_bold_font,
        ).pack(side="left")


    def _build_current_timing(self):
        ttk.Label(self, text="Current Household Timing", font=self._section_font).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 6)
        )

        current_frame = ttk.Frame(self)
        current_frame.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(
            current_frame,
            text=f"Household Retirement Age: {self.current_retirement_age}",
            font=self._text_bold_font,
        ).pack(side="left", padx=(0, 28))

        ttk.Label(
            current_frame,
            text=f"Household Social Security Age: {self.current_ss_age}",
            font=self._text_bold_font,
        ).pack(side="left")

        person_frame = ttk.Frame(self)
        person_frame.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 12))

        husband = self.parent_gui.husband

        ttk.Label(
            person_frame,
            text=(
                f"Husband: Current Age {int(husband.age)}, Retirement {int(husband.retire_age)}, "
                f"Social Security {int(husband.ss_age)}"
            ),
            font=self._text_font,
        ).pack(anchor="w")

        if self.show_wife:
            wife = self.parent_gui.wife

            ttk.Label(
                person_frame,
                text=(
                    f"Wife: Current Age {int(wife.age)}, Retirement {int(wife.retire_age)}, "
                    f"Social Security {int(wife.ss_age)}"
                ),
                font=self._text_font,
            ).pack(anchor="w", pady=(2, 0))


    def _build_retirement_ages(self):
        ttk.Label(self, text="Retirement Ages", font=self._section_font).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(4, 4)
        )

        ttk.Label(
            self,
            text=(
                "Enter household retirement ages to compare. The current household retirement timing "
                "is included automatically."
            ),
            font=self._text_font,
            wraplength=900,
            justify="left",
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 6))

        retirement_frame = ttk.Frame(self)
        retirement_frame.grid(row=8, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self.retirement_age_vars = []
        retirement_ages = self.working_options["retirement_ages"]

        for index in range(5):
            value = ""

            if index < len(retirement_ages):
                value = retirement_ages[index]

            text = ""

            if value != "":
                text = str(value)

            var = tk.StringVar(value=text)
            self.retirement_age_vars.append(var)

            entry = ttk.Entry(
                retirement_frame,
                textvariable=var,
                width=7,
                justify="right",
                font=self._body_font,
                style="RetirementSS.TEntry",
            )
            entry.grid(row=0, column=index, padx=(0, 10))
            self._age_entries.append(entry)


    def _build_social_security_ages(self):
        ttk.Label(self, text="Social Security Ages", font=self._section_font).grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(4, 4)
        )

        ttk.Label(
            self,
            text=(
                "Enter household Social Security claiming ages to compare. The current household "
                "Social Security timing is included automatically."
            ),
            font=self._text_font,
            wraplength=900,
            justify="left",
        ).grid(row=10, column=0, columnspan=2, sticky="w", pady=(0, 6))

        ss_frame = ttk.Frame(self)
        ss_frame.grid(row=11, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self.social_security_age_vars = []
        social_security_ages = self.working_options["social_security_ages"]

        for index in range(5):
            value = ""

            if index < len(social_security_ages):
                value = social_security_ages[index]

            text = ""

            if value != "":
                text = str(value)

            var = tk.StringVar(value=text)
            self.social_security_age_vars.append(var)

            entry = ttk.Entry(
                ss_frame,
                textvariable=var,
                width=7,
                justify="right",
                font=self._body_font,
                style="RetirementSS.TEntry",
            )
            entry.grid(row=0, column=index, padx=(0, 10))
            self._age_entries.append(entry)

        self._after_age_rows = 12

        if self.show_wife:
            ttk.Label(
                self,
                text=(
                    "For couples, WARPSimLab shifts both spouses' retirement and Social Security timing "
                    "together while preserving the household's existing timing relationship."
                ),
                font=self._text_font,
                wraplength=900,
                justify="left",
            ).grid(row=self._after_age_rows, column=0, columnspan=2, sticky="w", pady=(2, 12))

            self._after_age_rows += 1


    def _build_output_options(self):
        self.open_browser_var = tk.BooleanVar(
            value=self.working_options["output"].get("open_report_in_browser", False)
        )

        ttk.Checkbutton(
            self,
            text="Open HTML report in web browser when complete",
            variable=self.open_browser_var,
            style="RetirementSS.TCheckbutton",
        ).grid(row=self._after_age_rows, column=0, columnspan=2, sticky="w", pady=2)

        self._button_row = self._after_age_rows + 1


    def _build_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.grid(row=self._button_row, column=0, columnspan=2, sticky="w", pady=(18, 0))

        ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_changes,
            style="RetirementSS.TButton",
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_changes,
            style="RetirementSS.TButton",
        ).pack(side="left")


    def _normalize_options(self, report_options):
        normalized = copy.deepcopy(self.DEFAULT_OPTIONS)

        if not isinstance(report_options, dict):
            return normalized

        retirement_ages = report_options.get("retirement_ages")

        if isinstance(retirement_ages, list):
            normalized["retirement_ages"] = list(retirement_ages)

        social_security_ages = report_options.get("social_security_ages")

        if isinstance(social_security_ages, list):
            normalized["social_security_ages"] = list(social_security_ages)

        output = report_options.get("output")

        if isinstance(output, dict):
            normalized["output"].update(output)

        return normalized


    def _years_until(self, current_age, event_age):
        return int(event_age) - int(current_age)


    def _compute_household_retirement_age(self):
        husband = self.parent_gui.husband

        if not self.show_wife:
            return int(husband.retire_age)

        wife = self.parent_gui.wife

        husband_years = self._years_until(husband.age, husband.retire_age)
        wife_years = self._years_until(wife.age, wife.retire_age)

        if husband_years > wife_years:
            return int(husband.retire_age)

        if wife_years > husband_years:
            return int(wife.retire_age)

        return max(int(husband.retire_age), int(wife.retire_age))


    def _compute_household_ss_age(self):
        husband = self.parent_gui.husband

        if not self.show_wife:
            return int(husband.ss_age)

        wife = self.parent_gui.wife

        husband_years = self._years_until(husband.age, husband.ss_age)
        wife_years = self._years_until(wife.age, wife.ss_age)

        if husband_years > wife_years:
            return int(husband.ss_age)

        if wife_years > husband_years:
            return int(wife.ss_age)

        return max(int(husband.ss_age), int(wife.ss_age))


    def _parse_age_values(self, variables, label, minimum_age, maximum_age):
        values = []

        for var in variables:
            text = var.get().strip()

            if text == "":
                continue

            try:
                value = int(text)
            except ValueError as exc:
                raise ValueError(f"'{text}' is not a valid {label.lower()} age.") from exc

            if value < minimum_age or value > maximum_age:
                raise ValueError(f"{label} ages must be between {minimum_age} and {maximum_age}.")

            values.append(value)

        if len(values) < 2:
            raise ValueError(f"Enter at least two {label.lower()} ages.")

        if len(set(values)) != len(values):
            raise ValueError(f"Duplicate {label.lower()} ages are not allowed.")

        values.sort()
        return values


    def apply_changes(self):
        try:
            retirement_ages = self._parse_age_values(self.retirement_age_vars, "Retirement", 0, 100)
            social_security_ages = self._parse_age_values(
                self.social_security_age_vars, "Social Security", 62, 70
            )
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Retirement & Social Security Comparison",
                str(exc),
                parent=self,
            )
            return

        self.working_options["retirement_ages"] = retirement_ages
        self.working_options["social_security_ages"] = social_security_ages
        self.working_options["output"]["open_report_in_browser"] = self.open_browser_var.get()

        self.options.clear()
        self.options.update(copy.deepcopy(self.working_options))

        self.parent_gui.edit_blank()
        self.parent_gui.run_simulation_from_gui(sim_type="retirement_ss_comparison_report")


    def cancel_changes(self):
        self.working_options = self._normalize_options(self.options)
        self.parent_gui.edit_blank()