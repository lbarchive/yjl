
# Introduction #
This is a Blogger.com widget, which enhances the official Label gadget. It converts original Label gadget into:
  * Dropdown box style
  * Tagcloud style

This widget's code is updated from [LabelCloud](http://makeyjl.blogspot.com/2008/09/labelcloud-tagcloud-for-blogger.html), and licensed under the LGPLv3.

# Screenshot #
![http://lh4.ggpht.com/_CLdf4ORfzWk/SSQ9T2T4ILI/AAAAAAAABcw/1B7UeOdzT90/s800/LabelX.png](http://lh4.ggpht.com/_CLdf4ORfzWk/SSQ9T2T4ILI/AAAAAAAABcw/1B7UeOdzT90/s800/LabelX.png)

# Features #
  * Tagcloud: Customizations of the minimum/maximum font size and font size unit.
  * Tagcloud: Customizations of the start and end colors.
  * Both: Limiting the number of Labels, e.g. top 100 or last 100 in counts (I wonder if really someone will try to list last 100 labels)
  * Both: Sorting by Labels' names or their counts.

# Installation #
  1. Backup your template.
  1. **Important** If you have messed up with other label cloud methods, please make sure you have clean up and completely remove them before you saying “LabelX is not working!”
  1. You need an official Label gadget for conversion, make sure you have one. **Important** You may have a messed Label gadget by using other label cloud methods, remove all current Label gadgets and add a new one is better way to ensure everything is right to go.
  1. Add a **HTML/JavaScript Gadget**. Assume you want a Tagcloud with fontsize from normal to twice big and coloring from gray to full black (Please check out Examples section for more usage):
```
<script src="http://www.google.com/jsapi"></script>
<script type='text/javascript'>
// LabelX for Blogger
// http://code.google.com/p/yjl/wiki/LabelX
google.load("jquery", "1.3.0");
google.setOnLoadCallback(function() {
    // As Label Cloud
    LX_Render('Label1', 'cloud', {
        MinFontSize: 1.0,
        MaxFontSize: 2.0,
        FontSizeUnit: 'em',
        StartColor: [128, 128, 128],
        EndColor: [0, 0, 0],
        Limit: -100,
        SortByName: true,
        Reverse: false
        });
    });
</script>
<script type='text/javascript' src='http://yjl.googlecode.com/svn/trunk/Blogger/LabelX.js'> </script>
```

If you only have one official Label gadget, now you should have a Tagcloud.

# Render Function #
`LX_Render` is important to set the things right. It should be called as
```
LX_Render(target, style, options);
```
  * **target** is the HTML Element ID of official Label gadget.
  * **style** is either `cloud` or `dropdown`.
  * **options** is a JavaScript object, which tells the render function how to render.

Options have:
  * (Cloud only) `MinFontSize`/`MaxFontSize`/`FontSizeUnit`: Settings for font sizes of labels. Default are 1.0/2.0/em, which means 1em to 2em.
  * (Cloud only) `StartColor`/`EndColor`: Setting for text color of labels. Should be a 3-element array `[red, green, blue]`. No default value. Two must be set together in order to take effect.
  * `Limit`: How many labels to be shown. If you want the top 100 in most frequent, then it's -100 (Note that the minus), which is also the default. If you want to top 15 in least frequent, then it's 15.
  * `SortByName`: After `Limit` the number of label by their frequency. If you want the labels get sorted by name (a->z...), then set it to true. Other values will sort by their counts (0->9...).
  * `Reverse`: Set to true if in descending order. Note that this take in action last.

# Examples #
Ask if you need more examples. You need to replace `LX_Render` above with one below.

## Tagcloud: Only coloring ##
```
    LX_Render('Label1', 'cloud', {
        MinFontSize: 1.0,
        MaxFontSize: 1.0,
        FontSizeUnit: 'em',
        StartColor: [128, 128, 128],
        EndColor: [0, 0, 0],
        Limit: -100,
        SortByName: true,
        Reverse: false
        });
```
The labels should be rendered as normal font size and coloring from gray to full black.

## Dropdown box: all labels, sorting alphabetically ##
```
    LX_Render('Label1', 'dropdown', {
        SortByName: true
        });
```

## Dropdown box: 20 label, most frequent first ##
```
    LX_Render('Label1', 'dropdown', {
        Limit: -20,
        SortByName: false,
        Reverse: true
        });
```

# Known Issues #
## All labels in StartColor ##
If you set `StartColor` and `EndColor` and all labels are colored in `StartColor`, all of the labels may have same post count. I don't treat this as a bug.

# Contact #
Please contact via this [Discussions Group](http://groups.google.com/group/yu-jie-lin).

## Asking to solve problems ##
When **LabelX** doesn't work, please supply information:
  * **Required** Browser and version
  * **Required** Link to your blog, and it must have LabelX code. Do NOT remove LabelX and ask for help!
  * What else non-official-blogger stuff you have added?

**_Any inquiry that miss any required information above will be ignored!_**