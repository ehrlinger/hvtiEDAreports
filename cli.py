"""
cli.py — eda-report command-line entry point.

Wraps ``quarto render eda_report.qmd`` with parameter injection.
Usable standalone or called from the Web UI launcher.

Install as console script via pyproject.toml:
  [project.scripts]
  eda-report = "cli:main"

Usage
-----
  eda-report --data path/to/delivery.xpt
  eda-report --data delivery.xpt --x-axis procdt --title "CABG 2025 Q1" --open
  eda-report --help
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import webbrowser

import click

from eda import __version__


def _find_quarto() -> str:
    """Return the path to the quarto executable.

    In a PyInstaller bundle, quarto is bundled under sys._MEIPASS/quarto/.
    In a developer install, quarto must be on PATH.

    Raises
    ------
    click.ClickException
        If quarto cannot be found.
    """
    # PyInstaller bundle
    if hasattr(sys, "_MEIPASS"):
        bundled = pathlib.Path(sys._MEIPASS) / "quarto" / "bin" / "quarto"
        if bundled.exists():
            return str(bundled)

    # Developer / conda install — require quarto on PATH
    import shutil
    quarto = shutil.which("quarto")
    if quarto:
        return quarto

    raise click.ClickException(
        "quarto not found.  Install from https://quarto.org/docs/get-started/ "
        "and ensure it is on your PATH."
    )


@click.command()
@click.version_option(version=__version__, prog_name="eda-report")
@click.option(
    "--data", "-d",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    help="Path to input data file (.xpt, .sas7bdat, .csv, .pkl).",
)
@click.option(
    "--x-axis",
    default=None,
    show_default=True,
    help="Column name for x-axis on continuous plots. Auto-detected if omitted.",
)
@click.option(
    "--title",
    default=None,
    help="Report title shown in the HTML header. Defaults to the filename stem.",
)
@click.option(
    "--output-dir", "-o",
    default=None,
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    help="Directory to write output files. Defaults to the same directory as --data.",
)
@click.option(
    "--cat-max",
    default=10,
    show_default=True,
    help="Unique-value threshold for categorical classification.",
)
@click.option(
    "--suppress-above",
    default=20,
    show_default=True,
    help="Categorical columns with more levels than this are suppressed from panel figures.",
)
@click.option(
    "--no-manifest",
    is_flag=True,
    default=False,
    help="Skip manifest and checksum generation.",
)
@click.option(
    "--manifest-format",
    default="both",
    type=click.Choice(["json", "md", "both"], case_sensitive=False),
    show_default=True,
    help="Format for the delivery manifest.",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    default=False,
    help="Open the rendered report in the default browser after rendering.",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    default=False,
    help="Suppress progress output.",
)
def main(
    data: pathlib.Path,
    x_axis: str | None,
    title: str | None,
    output_dir: pathlib.Path | None,
    cat_max: int,
    suppress_above: int,
    no_manifest: bool,
    manifest_format: str,
    open_browser: bool,
    quiet: bool,
) -> None:
    """Generate a self-contained HTML EDA report for a delivered dataset.

    Produces the report plus (by default) a delivery manifest and
    SHA-256 checksum in OUTPUT_DIR.
    """
    # Resolve defaults
    output_dir = output_dir or data.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    report_title = title or data.stem
    report_stem = data.stem
    report_path = output_dir / f"{report_stem}_eda.html"

    quarto = _find_quarto()

    # Locate eda_report.qmd relative to this file (works for both dev and bundle)
    qmd_path = pathlib.Path(__file__).parent / "eda_report.qmd"
    if not qmd_path.exists():
        raise click.ClickException(f"eda_report.qmd not found at {qmd_path}")

    # Build quarto render command
    # TODO: confirm quarto 1.5+ param syntax — use embed-resources not self-contained
    cmd = [
        quarto, "render", str(qmd_path),
        "--output", str(report_path),
        "-P", f"data_file:{data}",
        "-P", f"report_title:{report_title}",
        "-P", f"cat_unique_max:{cat_max}",
        "-P", f"suppress_levels_above:{suppress_above}",
        "-P", f"output_dir:{output_dir}",
    ]
    if x_axis:
        cmd += ["-P", f"x_axis_var:{x_axis}"]

    if not quiet:
        click.echo(f"eda-report v{__version__}")
        click.echo(f"  Data:   {data}")
        click.echo(f"  Output: {report_path}")
        click.echo("  Rendering...")

    result = subprocess.run(cmd, capture_output=quiet)

    if result.returncode != 0:
        if quiet:
            click.echo(result.stderr.decode(), err=True)
        raise click.ClickException("Quarto render failed. See output above.")

    if not quiet:
        click.echo("  Done.")

    # Delivery package
    if not no_manifest:
        from eda.delivery import generate_delivery_package
        from eda.loader import load_dataset
        from eda.classify import classify_dataset

        if not quiet:
            click.echo("  Generating manifest and checksum...")

        df, col_labels = load_dataset(data)
        classified = classify_dataset(df, column_labels=col_labels, x_axis_var=x_axis)
        params = {
            "x_axis_var": x_axis or classified.x_axis_var,
            "cat_unique_max": cat_max,
            "suppress_levels_above": suppress_above,
            "report_title": report_title,
        }
        generate_delivery_package(
            data_path=data,
            report_path=report_path,
            classified=classified,
            output_dir=output_dir,
            parameters=params,
            manifest_format=manifest_format,
        )

    if open_browser:
        webbrowser.open(report_path.as_uri())

    if not quiet:
        click.echo(f"\nReport: {report_path}")
        if not no_manifest:
            click.echo(f"Manifest: {output_dir / f'{report_stem}_manifest.json'}")
            click.echo(f"Checksum: {output_dir / f'{report_stem}.sha256'}")

    sys.exit(0)


if __name__ == "__main__":
    main()
