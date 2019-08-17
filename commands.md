

## List of Commands

### plot
---

Plotting data from file to current subfigure.

Usage:

    plot (filename1) (xcol:)(ycol1) (style=val), (filename2) (xcol2:)(ycol2) (style=val), ...

Example:

    plot a.txt 1:2 lw=2, lc=red, 3 lc=blue, ($4+1) lc=green


Args:

- filename: If `filename1` is not set, the plotting source is the last opened file. Exception will arise if filename is empty.
- xcol, ycol: Column selections. Can be One of plain number, column title or expression.
    - If the selection is in bracket, it is parsed as an expression.
    - If the first character is not `$`, it is parsed as column title or column index;
    - If the first character is `$`, it is also parsed as an expression, which ends at the next `:`, `,` or word before `=`, whichever comes first.
    - By default, number is parsed as indices. Using `col()` to select number by title.
    - If a column selection is not present, by default all columns in the file are added into current figure ($0:$1 if only one column, $1:$2,... if multiple columns). A file will be selected first if its name coincide with column name. Use '$' to select column to avoid such conflict, or set *--force-column-selection=true*.
- style, val: See [Style name and value](#list-of-valid-style-and-names).
    - If a style is [broadcastable](#broadcasity), it will be applied to other data in this command, unless set explicitly.

Expression:

Expression is parsed by python `eval()`, with data treated as numpy array. Variables in expression must start with `$`. For exmaple, `$a` is parsed as column with title "a". By default, `$1` is parsed as column with index 1. To use number as column titles, use `col()` function to select column.

`$0` is a special column with integer sequence starting from 0.

Avaiable functions are #available functions.

Related options:

- --force-column-selection=true/false: If true, column selection must be present after a file. This may reduced the time of identifying whether a string is column title or new file. (Default: false).

- --ignore-data-comment=true/false: If true, ignore lines starting with `#`. (Default: true)

- --identify-data=true/false: Analyze file automatically to select plottable data. (Default: false).

- --data-delimiter=(delimiter)/white/auto: Set the data delimiter. 'white' means both tab and space. 'auto' means automatically identifing. (Default: auto).

- --data-title=true/false/auto. Do/don't Treat the first row of data as title. (Default: auto).


### append
---

Append data to current subfigure.

Usage:

    append (filename1) (xcol:)(ycol1) (style=val), (filename2) (xcol2:)(ycol2) (style=val), ...

Argument is same as `plot`.

### remove
---

Remove objects in current subfigure. Can only remove datas, lines and texts.

Usage:

    remove element1 element2 ... style=val ...

Args:

- element: Element (data line/draw line/text) name. Input will be asked if a column corresponds to multiple selection.
- style, val: Remove all lines with certain style.

Line indices will change if there are lines removed. Use `show line label` to see the indices.

Related options:

- --prompt-multi-removal: Prompt before removing multiple line by style filter. (Default: true)
- --remove-element-by-style: Remove other graphic elements by style. If false, only remove data lines with certain style. (Default: false)

### group
---

Assigning group to lines in current subfigure.

Usage:

    group AABBC0
    group 1122...0
    group ABCABC...
    group clear

Group identifier can be set either before or after plotting. The same character will represent same style series#link.

The "..." will be expanded by the last repeating unit before it.

    ABCABC... -> ABCABCABC
    ABCCC... -> ABCCCCC
    ABCC...D -> ABCCCCCCD

Identifier "0" represent the base style#link in style series.

"group clear" will clear group in current subfigure.

### set
---

Set style parameters.

Usage:

    set (default) (element1,element2,...) style1=val1 style2=val2 ...
    set (default) (element1,element2,...) clear
    set palette (palettename)
    set option opt=arg

- element: [Name of element](#list-of-element-name-and-applicable-styles) in current context.
    - In-figure elements (like lines, texts, axes) are searched in current figure and subfigure only.
    - To select data line, use `line@label` or `line`+number like `line1`. To select draw line, use `line`+number. A prompt will appear when multiple lines have same label.
    - To select text, use `text@label` or `text`+number. The label of text is text itself. A prompt will appear when multiple texts have same label.
    - If no element is set, the style is first applied to current subfigure (and broadcasted to lines, if possible), then current figure.
- `set palette` changes palette for current subfigure.
- `set option` changes default options, e.g. `set option ignore-data-comment=true`.

Related options:

- --set-skip-invalid-selection=true/false: Skip invalid selection of element. (Default: true)
- --set-future-line-style=true/false: Apply line styles to future lines. (Default: true)

### show
---

Show style parameters and options.

Usage:

    show [element] (stylename)
    show currentfile
    show option [optionname]

Args:
- element: [Name of element](#list-of-element-name-and-applicable-styles) in current context. If element is a general selection like "line", style of all lines will be shown.
    - In-figure elements (like lines, texts, axes) are searched in current figure and subfigure only. `line`+number or `text`+number also applies here.
- stylename: [Name of style](#list-of-valid-style-values). All styles parameters will be shown if not given.
- `show currentfile` shows current open and save filename;
- `show option` shows current global option.
    

### line, hline, vline
---

Draw line on current subfigure.

Usage:

    line x1,y1 x2,y2 (style=val ...)
    hline x1 (style=val ...)
    vline y1 (style=val ...)

- x1,x2,y1,y2: Coordinate in data coordinates.
- style, val: Line styles.


### text
---

Display text in current figure.

Usage:

    text string pos (style=val ...)

Args:

- pos: Either position descriptor ('left-top', 'left-bottom', ... ), or positions 'x,y', with pixel as unit **inside** axis (--text-inside-axis=true)
- style,val: Style parameters.


### split, hsplit, vsplit
---

Create subfigures.

Usage:

    split hnum,vnum
    hsplit hnum
    vsplit vnum

Args:

- hnum,vnum: Numbers of subfigures in horizontal/vertical direction. If it is less than current number, additional subfigures will be removed.

### figure, subfigure
---

Select figure or subfigure.

Usage:

    figure (title)
    subfigure index

The behavior of `figure` is similar with matlab's figure. It will create new figure if no figure has proper title.
The index of subfigure is an integer, starting from left to right and top to bottom.

### save
---

Save current figure to file.

Usage:

    save (filename)

If filename is not present, save will prompt for a new filename. It will also prompt for a new filename (or overwrite) if file exists.

Related options:

- --prompt-overwrite=true/false: Prompt before overwritting a file. (Default: true).

### clear
---

Clear current subfigure but keeps style.

Usage:

    clear

Use `set gca visible=false` to completely hide current subfigure.

### replot
---

Refresh the current subfigure or figure (if "all" is present).

Usage:

    replot
    replot all


### print
---

Print a string.

Usage:

    print 'Hello world'


### input
---

Switch to input mode. This is extermely useful in line input and script input.

Usage:

    input

To function properly, `input` must be the last command of one line.

### display

Display the current figure. Only works in non-interactive mode.

Usage:

    display


### load

Load an external script.

Usage:

    load filename


### quit
---

Quit the program.

Usage:

    quit

Related options:
- --prompt-save-when-quit=true/false: Prompt to save current figure when quitting. (Default: false).
- --display-when-quit=true/false: Display figure when quitting in non-interactive mode. (Default: false).


## Style Names and Element Names

### Element Inheritance

- figure
    - subfigure
        - xaxis, yaxis, raxis, taxis
            - xlabel, ylabel, rlabel, tlabel
            - xtick, ytick, rtick, ttick
            - xgrid, ygrid
        - datalines
        - drawlines
        - texts
        - legend

### List of Element Name and Applicable Styles

 Element Name | Style 
 --- | --- | ---
 figure | size, margin, (h/v)spacing, dpi | 
 subfigure | rsize, rpos, palette, padding, title  | 
 subfigure (redirect) | xlabel, ylabel, xrange, yrange, xtick, ytick
 axis | linewidth, color, range, visible, zindex |
 label | font, fontfamily, fontsize, text |
 tick | orient, color, font, fontfamily, fontsize, format, visible |
 grid | linewidth, color, linetype, visible |
 dataline | linewidth, linecolor, linetype, pointsize, pointtype, edgewidth, edgecolor, fillcolor, color, skippoint, visible, zindex
 drawline | linewidth, linecolor, linetype, pointsize, pointtype, edgewidth, edgecolor, fillcolor, color, startpos, endpos, coord, visible, zindex
 text | font, fontfamily, fontsize, color, pos, coord, text, visible, zindex
 legend | linewidth, linecolor, linetype, alpha, fontfamily, fontsize, color, pos, visible, zindex
 option | (set option flags)

### List of Valid Style Values

Style Name | Value Description
--- | ---
alpha | float
bgcolor | 'r'/'g'/'red'/'dark-red'... or 70707F ...
color |  'r'/'g'/'red'/'dark-red'... or 70707F...
coord | 'data'/'axis'/'figure'
dpi | int
edgecolor | 'r'/'g'/'red'/'dark-red'... or 70707F...
edgewidth | int
fillcolor | 'r'/'g'/'red'/'dark-red'... or 70707F...
font | string,int (font name, size) or string (font name)
fontfamily | string (font name)
fontsize | float
format | string (indicator like '%f')
hspacing | float
label | string
linecolor | 'r'/'g'/'red'/'dark-red'... or 70707F...
linetype | '-'/'--'/'-.'/':'/'solid'/'dash'/'dot'/'dashdot'
linewidth | float
margin | float,float,float,float (bottom,left,right,top)
orient | 'in/out'
padding | float,float,float,float (bottom,left,right,top)
palette | string
pointsize | float
pointtype | '.'/'x'/'o'/'d'/'s'/'^'/'v'
pos | float,float or 'topleft'/'topright'/'topcenter'/'bottomleft'/...
rsize | float,float (x,y)
range | float:float:float float:float
size | int,int (x,y)
skippoint | int
spacing | float,float
title | string
tick | string
text | string
visible | 'true'/'false'
vspacing | float
zindex | int


### Broadcasting

Styles appear in the first plotting data will be broadcasted to all the remaining data if it's broadcastale.

By default, styles except `linecolor`, `edgecolor`, `skippoint` and `zindex` in drawline and dataline are broadcastable. This can be set by *--add-boardcast-style=(stylename)* and *--remove-broadcast-style=(stylename)*.

### Style Fallback

Line itself keeps a global default style sheet, which can be changed by `set default` or `.linerc` file. When a figure is created, its style and default subfigure style is copied from global style.

Each subfigure keeps a template of line styles, which is created from global default style and default palette. The template is updated by group specification each time `plot` is called. When a new line is plotted, its style is looked up from line template style. The template style is also updated if style is set in `plot` command.

