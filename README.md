# LINE

Creating nice line and scatter plot with least typing.

![](doc/plot1.png)

## Installation

Prerequesties:

- Python >= 3.5 (Necessary)
- Matplotlib >= 3.0 (Necessary)
- Numpy >= 1.13 (Necessary)
- Pandas >= 0.22 (Necessary)
- PyQt5 (Optional, for Qt backend)
- Seaborn (Optional, for its palettes)

The package is pure-python and is directly executable. To install it into python library:

    pip install -e line

## Tutorial

The full documentation can be found [here](doc/doc.md), which includes [command-line options](doc/doc.md#command-line-options), [command reference](doc/doc.md#command-reference) and [styles](doc/doc.md#styles).

To get started, type

    line

which will enter interactive mode. To run a script, type

    line [scriptname]

The basic plotting logic of Line is similar as gnuplot, with a slightly looser grammar. No quote is required (unless necessary) for filename and column identifier is also not required. Filename could also be wildcard string.
To plot a figure from file:

    line> plot test-data.txt 2 t='second column'  # plot second column as y, data index as x
    line> plot test-data.txt $0:2 lw=2 lc=red     # plot second column as y, data index as x
    line> plot test-data.txt 1:2 rx-        # plot second column as y, first column as x
    line> plot test-data.txt 1:2,3      # plot second and third column as y, first column as x
    line> plot test-data.txt        # plot all columns (using first column as x)

The data delimiter and existence of head is automatically determined, but can be specified by *data-delimiter* and *data-title* options.
Append data to existing figure:

    line> add test-data.txt 3       # add the third column

Adjust ranges and grids:

    line> set xrange 0:2
    line> set grid on
    line> set grid lt=dash lc=grey

Command "set" contains all adjustments to style and non-style paramters. The global options can be also be changed here. The figure is refreshed if necessary, so `replot` is not necessary here.

    line> set tick format='%.3f'
    line> set label fontfamily=Arial
    line> set lw=2  # set all data lines
    line> set line0 lw=2    # only set line0
    line> set option auto-adjust-range=false
    line> set palette mpl.OrRd

Its counterparts, "show" command, displays all style parameters.

    line> show line0

In script mode, Line will not draw the plot unless necessary. To display figure, type

    display

To modify figure in script mode, add

    input

which will interrupt script running and switch to interactive mode.


## Configuration

Line reads `.linerc` in user's home directory. You can also use `load` command to specify configurations.
