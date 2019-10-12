

# Documentation of Line

## Command Line Options

Entering interactive mode:

    line 

Run script:

    line [scriptname]

Run commands in line:

    line -e 'command1;command2;...'

Plotting file directly:

    line -p [filename1] (col_selection) (styles) ...

The file plotting mode has same grammar as `plot` command.

### Switches

Controls the program behavior. Can be also adjusted by `set option`.

- --auto-adjust-range
- --data-title
- --broadcast-style
- --data-delimiter
- --display-when-quit
- --force-column-selection
- --ignore-data-comment
- --prompt-always
- --prompt-multi-removal
- --prompt-overwrite
- --prompt-save-when-quit
- --remove-element-by-style
- --set-future-line-style
- --set-skip-invalid-selection

## Command Reference

### plot
---

Plotting data from file to current subfigure.

Usage:

    plot (filename1) (xcol:)(ycol1) (style=val) (linespec), (filename2) (xcol2:)(ycol2) (style=val), ...

Example:

    plot a.txt 1:2 lw=2, lc=red, 3 lc=blue, ($4+1) lc=green
    plot a.txt t:x,y b-


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
- linespec: Matlab-style line descriptor, which consists of short abbreviation of various line/point types and colors. See [this link](https://www.mathworks.com/help/matlab/ref/linespec.html) for details.

Expression:

Expression is parsed by python `eval()`, with data treated as numpy array. Variables in expression must start with `$`. For exmaple, `$a` is parsed as column with title "a". By default, `$1` is parsed as column with index 1. To use number as column titles, use `col()` function to select column.

`$0` is a special column with integer sequence starting from 0.

Avaiable functions are #available functions.

Related options:

- --force-column-selection=true/false: If true, column selection must be present after a file. This may reduced the time of identifying whether a string is column title or new file. (Default: false).

- --ignore-data-comment=true/false: If true, ignore lines starting with `#`. (Default: true)

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

    remove selection1,selection2 ... style=val ...

Args:

- element: Selections of elements, see [set](#set) for details.
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

    set (default) (selection1,selection2,...) style1=val1 style2=val2 +class1 -class2 ...
    set (default) (selection1,selection2,...) clear
    set option opt=arg

Example:

    set default figure dpi high
    set line lw=2
    set line +paircross

- selection: Select elements by name, type, class or attributes.

Selector | Selection
- | -
type | [elements with type](#list-of-element-type-and-applicable-styles) 
.class | elements with class
.class type | descedants with type of element with class
style=val | element with certain style value
type:style=val | element with certain type and style value. e.g. line[color=black]
name | element with name, e.g. line1
.class.name | descedants with name of element with class

If no element is set, the style is applied to current subfigure.
- `set palette` changes palette for current subfigure.
- `set option` changes default options, e.g. `set option ignore-data-comment=true`.

Related options:

- --set-skip-invalid-selection=true/false: Skip invalid selection of element. (Default: true)
- --set-future-line-style=true/false: Apply line styles to future lines. (Default: true)

### show
---

Show style parameters and options.

Usage:

    show default [element] (stylename)
    show selection1,selection2, ... (stylename)
    show currentfile
    show pwd
    show option [optionname]

Args:
- selection: Selections of elements, see [set](#set) for details.
- stylename: [Name of style](#list-of-valid-style-values). All styles parameters will be shown if not given.
- `show currentfile` shows current open and save filename;
- `show pwd` shows current directory;
- `show option` shows current global option.
    

### line, hline, vline
---

Draw line on current subfigure. `hline` and `vline` draws horizontally and vertically.

Usage:

    line x1,y1 x2,y2 (style=val ...)
    hline y1 (style=val ...)
    vline x1 (style=val ...)

- x1,x2,y1,y2: Start and end position. By default it's data coordinate. Specify `coord=data/axis` to change it.
- style, val: Line styles.


### text
---

Display text in current figure.

Usage:

    text string pos (style=val ...)

Args:

- pos: Either position descriptor ('topleft', 'topright', ... ), or positions 'x,y'. By default it's axis coordinate. Specify `coord=data/axis` to change it.
- style,val: Style parameters.


### split, hsplit, vsplit
---

Create subfigures.

Usage:

    split hnum,vnum
    hsplit hnum
    vsplit vnum

Args:

- hnum,vnum: Numbers of subfigures in horizontal/vertical direction. If it is less than current number, extra subfigures will be removed.

### figure, subfigure
---

Select figure or subfigure.

Usage:

    figure (title)
    subfigure index

The behavior of `figure` is similar with matlab's figure. It creates new figure and bring it to the front.

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

Switch to interactive mode. This is useful in line input and script input.

Usage:

    input

To function properly, `input` must be the last command of one line.

### display
---
Display the current figure. Only works in non-interactive mode.

Usage:

    display


### load
---
Load an external script.

Usage:

    load filename

### cd
---
Change directory.

Usage:

    cd path

### quit
---

Quit the program.

Usage:

    quit

Related options:
- --prompt-save-when-quit=true/false: Prompt to save current figure when quitting. (Default: false).
- --display-when-quit=true/false: Display figure when quitting in non-interactive mode. (Default: false).


## Styles

In Line, any modifiable properties (colors, linewidths, ranges, ...) are get/set by style APIs, and eventually by set/show commands. Line use a CSS-like style protocol: each element (see figure model below) has a type, name, a set of independent style and style classes.

### Figure Model

![](FigureModel.png)

### Inheritable Style and Element Hierachy

These styles are inheritable:
- fontfamily (up to subfigure level)
- fontsize (up to subfigure level)
- color (up to axis level)
- visible (up to subfigure level)

The hierachy of elements:

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

### List of Element Type and Applicable Styles

 Element Type | Style 
 --- | --- | ---
 figure | size, margin, (h/v)spacing, dpi | 
 subfigure | rsize, rpos, palette, padding, title  | 
 subfigure (redirect) | xlabel, ylabel, xrange, yrange, xtick, ytick
 axis | linewidth, color, range, visible, zindex |
 label | font, fontfamily, fontsize, text |
 tick | orient, color, font, fontfamily, fontsize, format, linewidth, visible |
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
color |  'r'/'g'/'red'/'darkred' ... (CSS4 Colors) or 70707F...
coord | 'data'/'axis'/'figure'
dpi | int / 'high'/'mid'/'low'
edgewidth | int
font | string,int (font name, size) or string (font name)
fontfamily | string (font name)
fontsize | float
format | string (indicator like '%f')
hspacing | float
label | string
linetype | '-'/'--'/'-.'/':'/'solid'/'dash'/'dot'/'dashdot'
linewidth | float
margin | float,float,float,float (bottom,left,right,top)
orient | 'in/out'
padding | float,float,float,float (bottom,left,right,top)
palette | string (name of a palette)
pointsize | float
pointtype | '.'/'x'/'+'/'*'/'o'/'d'/'s'/'^'/'v'/'<'/'>'/'p'/'h'
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

### Set Styles via CSS

You can modify the default behavior by modifying styles/defaults.d.css (modifying defaults.css is also possible, but may cause some weird behavior). You can also change the default style using `set default` or modifying `.linerc` file.

Note that currently Line only supports part of CSS. The style names must be predefined and the maximum hierachy of descendant is 2. The available selectors are:

- ClassNameSelector: `.class #name`: Select element which inside class;
- NameSelector `#name`: Select element which return true by has_name();
- TypeStyleSelector `type[style=val]`: Select type element with style;
- StyleSelector `[style=val]`: Select element with certain style value;
- ClassTypeSelector: `.class type`: Select type element within element with class;
- ClassSelector `.class`: Select element which has name in class_names;
- TypeSelector `type`: Select element with certain element_type attribute;