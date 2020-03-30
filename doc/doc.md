

# Line Documentation

Structure of this documentation:

- [Command Line Options](#command-line-options)
- [Command Reference](#command-reference)
- [Expressions](#expressions)
- [Styles](#styles)

## Command Line Options

Entering interactive mode:

    line 

Run script (in non-interactive mode):

    line [scriptname]

Run commands in line (in non-interactive mode):

    line -e 'command1;command2;...'

Plotting file directly:

    line -p [filename1] (col_selection) (styles) ...

The file plotting mode has same grammar as `plot` command.

### Global Switches

Controls the program behavior. Can be also adjusted by `set option`.

- --auto-adjust-range
- --autoload-file-as-variable
- --data-title
- --data-delimiter
- --display-when-quit
- --ignore-data-comment
- --prompt-always
- --prompt-multi-removal
- --prompt-overwrite
- --prompt-save-when-quit
- --rescale-when-split

## Command Reference

Contents:

- [append](#append)
- [cd](#cd)
- [clear](#clear)
- [display](#display)
- [figure,subfigure](#figure%44-subfigure)
- [fill](#fill)
- [group](#group)
- [hist](#hist)
- [input](#input)
- [load](#load)
- [line,hline,vline](#line%44-hline%44-vline)
- [plot](#plot)
- [print](#print)
- [quit](#quit)
- [remove](#remove)
- [replot](#replot)
- [save](#save)
- [set](#set)
- [split,hsplit,vsplit](#split%44-hsplit%44-vsplit)
- [show](#show)
- [text](#text)

### plot
---

Plotting data from file to current subfigure.

Usage:

    plot (source1) (xexpr:)(yexpr) (style=val) (linespec) ..., (source2) (xexpr2:)(yexpr2) (style=val), ...

Example:

    plot a.txt 1:2 lw=2, lc=red, 3 lc=blue, ($4+1) lc=green
    plot a.txt t:x r-,y b-

Args:

- source: A single variable name (if exists in global variable table) or filename. If source is not given, the previous source in current command is used.
- xexpr, yexpr: Column expression. See [Expressions](#expressions) for details.
    - If the expr only contains digits, it is treated as a column index.
    - If a column selection is not present, by default all columns in the file are added into current figure. If there are multiple columns and the source is a file, the first column is treated as x column.
- style, val: See [Style name and value](#list-of-valid-style-and-names).
- linespec: Matlab-style line descriptor, which consists of short abbreviation of various line/point types and colors. See [this link](https://www.mathworks.com/help/matlab/ref/linespec.html) for details.

Related options:

- --ignore-data-comment=true/false: If true, ignore lines starting with `#`. (Default: true)

- --data-delimiter=(delimiter)/white/auto: Set the data delimiter. 'white' means both tab and space. 'auto' means automatically identifing. (Default: auto).

- --data-title=true/false/auto. Do/don't Treat the first row of data as title. (Default: auto).

### hist
---

Plot histogram from data.

Usage:

    hist (source1) (expr1) (style=val) ..., (source2) (expr2) (style=val), ...

Arguments:
- source, expr: Same as in [plot](#plot).

The bin number of histogram can be set as `bin=[value]`.

### append
---

Append data to current subfigure.

Equivalent to `hold on; plot`. See [plot](#plot) for details.

### remove
---

Remove objects in current subfigure. Can only remove datas, lines and texts.

Usage:

    remove selection1, selection2 ... style=val ...

Args:

- element: Selections of elements, see [Element Selector](#element-selector) for details.
- style, val: Remove all lines with certain style.

Line indices will change if there are lines removed. Use `show line label` to see the indices.

Related options:

- --prompt-multi-removal: Prompt before removing multiple line by style filter. (Default: true)
- --remove-element-by-style: Remove other graphic elements by style. If false, only remove data lines with certain style. (Default: false)

### group
---

Batch change lines' colorid and groupid. See [Palette System](#palette-system) for details.

Usage:

    group AABBC0
    group 1122...0
    group ABCABC...
    group clear

`colorid` is bind to each character according to its first occurence. For example, "AABBC" will set colorid 1,1,2,2,3. "AACCB" will set the same sequence.
`groupid` is set according to the repeated times of a character. For example, "AABBC" will set `groupid` to 1,2,1,2,1. groupid can be useful to change style pairwisely, like `set line +pairdash`.

The "..." will be expanded by the last repeating unit before it.

    ABCABC... -> ABCABCABC
    ABCCC... -> ABCCCCC
    ABCC...D -> ABCCCCCCD

Identifier "0" represent the reference style, which has colorid 0 and groupid 0. It is usually a black solid line.


### set
---

Set style parameters.

Usage:

    set (default) (selection1,selection2,...) style1=val1 style2=val2 +class1 -class2 ...
    set (default) (selection1,selection2,...) clear
    set option opt=arg
    set palette (type) palettename

Example:

    set default figure dpi high
    set line lw=2
    set line +paircross
    set gca hold on

See [Element Selector](#element-selector) for more details about selections. If no element is set, the style is applied to current subfigure.

Additional options for set:
- `set default` modifies default value of styles, same as updating `default.css`.
- `set future` (experimental) modifies the global stylesheet, same as updating `default.d.css`.
- `set palette (type)` changes palette for certain figure elements (one of line (default),bar,polygon,drawline).
- `set option` changes default options, e.g. `set option ignore-data-comment=true`.

#### Abbrevation

If the first parameter of set is one of "grid,hold,legend,palette,x/ylabel,x/yrange,x/yscale,title", then the "set" word can be omitted. Examples:

    hold on # == set gca hold on
    grid on # == set gca grid visible=true
    xlabel "t" # == set gca xlabel "t"
    xrange 0:10 # == set gca xrange 0:10


### show
---

Display element style, options and miscellaneous info.

Usage:

    show default [element] (stylename)
    show selection1,selection2, ... (stylename)
    show currentfile
    show pwd
    show option [optionname]

Args:
- selection: Selections of elements, see [Element Selector](#element-selector) for details.
- stylename: [Name of style](#list-of-valid-style-values). All styles parameters will be shown if not given.
- `show currentfile` shows current save filename;
- `show pwd` shows current directory;
- `show palettes` shows all palettes available;
- `show option` shows current global option.
    

### fill
---

Fill under current line or between lines.

Usage:

    fill line1 line2    # fill the area under line1 and line2, using sequential colors
    fill line1-line2 # fill the area between line1 and line2

Fill will generate polygon objects, available for style customizing.

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

- pos: Positions 'x,y'. By default it's axis coordinate. Specify `coord=data/axis` to change it.
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

Related options:

- --resize-when-split: Resize the figure automatically when spiltting.

### figure, subfigure
---

Select figure or subfigure.

Usage:

    figure (title)
    subfigure index
    subfigure vnum,hnum,index

The behavior of `figure` is similar with matlab's figure. It creates new figure and bring it to the front.

The index of subfigure is an integer, starting from left to right and then top to bottom. If `vnum` and `hnum` are given, figure will be split first.

Both indices start from 1.

### save
---

Save current figure to file.

Usage:

    save (filename)

If filename is not present, save will prompt for a new filename. It will also prompt for a new filename (or overwrite) if file exists.

Related options:

- --prompt-overwrite=true/false: Prompt before overwritting a file. (Default: true). To use this option in non-interactive mode, set --prompt-always to true.

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
Load an external script. Additional arguments may be passed.

Usage:

    load filename [args...]

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

### for
---

Initiate a for loop.

Usage:

    for [variable] = [expression] do (command)
        (commands ...)
    done

Args:
    - variable: string, with or without the dollar mark;
    - expression: An [expression](#expressions) string.
    - command: Any expression except function definition or another for loop (nested loop is not supported now). Indent is not required.

The expression must yield an iterable object (such as list or array) or string. In the latter case, the loop
variables are the split results of the string.


### let
---

Define a variable or function.

Usage:

    let [variable] = [expression]
    let [function] = do (command)
        (commands...)
    done

Args:
    - variable/function: string, with or without the dollar mark;
    - expression: An [expression](#expressions) string.
    - command: Any expression except function definition or another for loop (nested loop is not supported now). Indent is not required.

The function defined by `do` is similar to a function in shell, which is merely a set of code snippet.


### call
---

Call a function.

Usage:

    call [function]

The function must be defined by `let` command.


## Expressions

Line handles simple arithmetic expression, including indexing `[]` and functions `func()`. The grammar is similar to Python or other programming language:

- Arithmetic operators: `+ - * / ** ^ |`. All the operations are column-wise;
- Indexing a column: Using column title `['column_title']` or column index (starting from 1) `[1] [2]`;
- Variable: Start with dollar sign `$`. Line also tries to parse variable without dollar sign, but will not guarantee parsed;
- Function: Can have multiple arguments. List of available functions is given below;
- String: With either single quotation or double quotation;

It's suggested to quote expression by bracket `()` to avoid ambiguity with the other part of the command.

Examples:

    sin($x) # calculate sin() for each element in $x
    $a+$b   # calculate element-wise sum of $a and $b
    $file[2]    # get second column of $file

Function list:

 Name | Usage
 --- | ---
sin | sin(x)
cos | cos(x)
tan | tan(x)
cumsum | cumsum(x)
exp | exp(x)
log | log(x)
sinh | sinh(x)
cosh | cosh(x)
tanh | tanh(x)
sqrt | sqrt(x)
abs | abs(x)
tp | tp(x)
min | min(x, y) (minimum element between two lists)
max | max(x, y) (maximum element between two lists)
hist | hist(x) (requires a column, returns a Nx2 matrix)
load | load('filename')
save | save('filename')
col | col('column_name') (only available in plotting)
arg | arg(index) (get args passed in shell or by 'load' command. Start from 0)

### Assigning

Assigning starts with a dollar sign:

    line> $a = 2
    line> $b = load('filename.txt')

The variable must be a single token, and will be overrided if the name exists.

### Files and Autoloaded Variables

When `autoload-file-as-variable` is set, Line will try parsing a varaible that has not been defined as matrix file(s). The format of matrix file is same as spreadsheet, except that title and index can be omitted.

Example:

    $file   # <= load file.txt, stored in variable with same name
    $file1 + $file2 # load two files and add them up
    $file[2]   # Second column of file.txt

Currently line does not support special charaters in file (such as `. + - * /`). Please use `load()` instead.

### Automatic Column Mapping

In plotting commands, columns are automatically mapped to variables, if the variable name does not exist in global space.

Examples:

    plot file $a + $b => plot $file["a"] + $file["b"]
    plot file $1 => $file[1]



## Styles

In Line, any modifiable properties (colors, linewidths, ranges, ...) are get/set by style APIs, and eventually by set/show commands. Line uses a CSS-like style protocol: each element (see figure model below) has a type, name, a set of independent style and style classes.

### Set Styles via CSS

The default behavior of Line can be modified by modifying [styles/defaults.d.css](../styles/defaults.d.css) (modifying defaults.css is also possible, but may cause some weird behavior). The same goal can also be achieved by  `set default` or modifying `.linerc` file.

Note that currently Line only supports part of CSS. The style names must be predefined and the maximum hierachy of descendant is 2. The available selectors are:

- ClassNameSelector: `.class #name`: Select element which inside class;
- NameSelector `#name`: Select element which return true by has_name();
- TypeStyleSelector `type[style=val]`: Select type element with style;
- StyleSelector `[style=val]`: Select element with certain style value;
- ClassTypeSelector: `.class type`: Select type element within element with class;
- ClassSelector `.class`: Select element which has name in class_names;
- TypeSelector `type`: Select element with certain element_type attribute;

### Element Selector

Element selection is widely used in Line commands. Line uses a slightly different one from CSS selector to save typing:

Selector | Selection
--- | ---
type | [elements with type](#list-of-element-type-and-applicable-styles) 
.class | elements with class
.class.type | descedants with type of element with class
style=val | element with certain style value
type:style=val | element with certain type and style value. e.g. line[color=black]
name | element with name, e.g. line1
.class.name | descedants with name of element with class

Examples:

    line    # select all data lines
    line1   # select data line 1
    line:label=y1   # select data line whose label is y1
    lw=2    # select all elements with linewidth=2 (including axis, ticks, ...)

### Palette System

For figure elements like lines, drawlines and and polygons, Line has a palette system to batch assigning colors. When an element is created, it is assigned a `colorid` (usually just its index). Color is assigned according to this number. Colorid can be manually set by set command. For data line it also can be changed using [group](#group) command.

Each data line also has a `groupid` to distinguish it between others. This is automatically set when using group command to change its colorid. Line also has several style classes for group, such as `pairdash`, `pairdot` and `paircross`.

List of palettes can be found by `show palettes`, usually it's intrisic palettes and some matplotlib palettes. Palettes can be customized in [styles/palettes.json](../styles/palettes.json).

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

![](FigureModel.png)

### List of Intrinsic Style Classes

These can be found in [styles/defaults.d.css](../styles/defaults.d.css).

- pairdash
- pairdot
- paircross
- prettycircle

### List of Element Type and Applicable Styles

 Element Type | Style 
 --- | ---
 figure | size, margin, (h/v)spacing, dpi
 subfigure | rsize, rpos, padding, title, font, fontfamily, fontsize, color, linecolor, xlabel, ylabel, xrange, yrange, xtick, ytick
 axis | linewidth, linetype, font, fontfamily, fontsize, color, range, scale, visible, zindex
 label | font, fontfamily, fontsize, text, visible
 tick | orient, color, font, fontfamily, fontsize, format, linewidth, length, visible
 grid | linewidth, linetype, linecolor, visible, zindex
 line | linewidth, linecolor, linetype, pointsize, pointtype, edgewidth, edgecolor, fillcolor, fillstyle, color, skippoint, label, xlabel, colorid, groupid, visible, zindex
 bar | bin, norm, linewidth, linecolor, fillcolor, width, label, xlabel, alpha, colorid, visible, zindex
 drawline | linewidth, linecolor, linetype, pointsize, pointtype, edgewidth, edgecolor, fillcolor, fillstyle, color, coord, visible, zindex
 polygon | linetype, linecolor, fillcolor, color, alpha, colorid, visible, zindex
 text | font, fontfamily, fontsize, color, pos, coord, text, visible, zindex
 legend | linewidth, linecolor, linetype, alpha, fontfamily, fontsize, color, pos, visible, zindex

### List of Valid Style Values

Style Name | Value Description
--- | ---
alpha | float
bin | int
color or c|  'r'/'g'/'red'/'darkred' ... (CSS4 Colors) or 70707F...
colorid | int
coord | 'data'/'axis'/'figure'
dpi | int / 'high'/'mid'/'low'
edgewidth | int
fillstyle | 'full'/'none'
font | string,int (font name, size) or string (font name)
fontfamily | string (font name)
fontsize | float
format | string (indicator like '%f')
groupid | int
hold | 'on'/'off'/'true'/'false'
hspacing | float
label or t | string. (Experimental) '!\[regex]>\[repl]' if starts with '!'
length | float
linetype or lt| '-'/'--'/'-.'/':'/'solid'/'dash'/'dot'/'dashdot'
linewidth or lw| float
margin | float,float,float,float (bottom,left,right,top)
norm | 'pdf'/'density'/'distribution'/'probability'/'count'
orient | 'in/out'
padding | float,float,float,float (bottom,left,right,top)
pointsize or ps| float
pointtype or pt | '.'/'x'/'+'/'*'/'o'/'d'/'s'/'^'/'v'/'<'/'>'/'p'/'h'
pos | float,float (x,y) or (subfigure elements only) floating positions
rsize | float,float (x,y)
xrange/yange or xlim/ylim | float:float:float float:float
scale | 'linear'/'log'
size | int,int (x,y)
skippoint | int
spacing | float,float
title | string
tick or tics| string
text | string
visible | 'true'/'false'
vspacing | float
width | float
zindex | int
